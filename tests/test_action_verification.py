"""Unit tests for ActionManager, closed-loop hardware verification, and audit logging."""

import os
import tempfile
import pytest
from bat_pod.action.action_manager import ActionManager
from bat_pod.audit.audit_logger import AuditLogger
from bat_pod.auth.rfid_auth import RFIDAuthenticator
from bat_pod.core.models import (
    ActionPriority,
    ActionType,
    ApprovalStatus,
    UserIdentity,
    UserRole,
    VerificationStatus,
)
from bat_pod.hal.mock_adapters import (
    MockAlarmActuator,
    MockPumpActuator,
    MockServoActuator,
)
from bat_pod.safety.policy_engine import SafetyPolicyEngine


@pytest.fixture
def test_setup():
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    audit = AuditLogger(db_path=temp_db.name)
    servo = MockServoActuator(initial_angle=90)
    pump = MockPumpActuator()
    alarm = MockAlarmActuator()
    auth = RFIDAuthenticator()
    safety = SafetyPolicyEngine()

    mgr = ActionManager(
        servo=servo,
        pump=pump,
        alarm=alarm,
        audit_log=audit,
        safety_engine=safety,
        auth=auth,
    )

    yield {
        "manager": mgr,
        "servo": servo,
        "pump": pump,
        "alarm": alarm,
        "audit": audit,
        "auth": auth,
    }

    try:
        os.remove(temp_db.name)
    except Exception:
        pass


def test_action_execution_with_successful_verification(test_setup):
    mgr = test_setup["manager"]
    servo = test_setup["servo"]
    admin = UserIdentity(rfid_uid="CARD_ADMIN_001", name="Bruce", role=UserRole.ADMIN)

    result = mgr.execute_action(
        action=ActionType.CLOSE_VALVE,
        priority=ActionPriority.NORMAL,
        requested_by=admin,
        approval_status=ApprovalStatus.APPROVED,
    )

    assert result.dispatched is True
    assert result.execution_result == "success"
    assert result.verification_status == VerificationStatus.VERIFIED_SUCCESS
    assert servo.get_state() == "0_DEG"

    # Verify audit log was recorded
    latest = test_setup["audit"].get_latest_record()
    assert latest is not None
    assert latest.requested_action == "close_valve"
    assert latest.verification_result == "verified_success"


def test_action_execution_with_hardware_verification_failure(test_setup):
    mgr = test_setup["manager"]
    servo = test_setup["servo"]
    servo.simulate_verification_failure = True
    admin = UserIdentity(rfid_uid="CARD_ADMIN_001", name="Bruce", role=UserRole.ADMIN)

    result = mgr.execute_action(
        action=ActionType.CLOSE_VALVE,
        priority=ActionPriority.NORMAL,
        requested_by=admin,
        approval_status=ApprovalStatus.APPROVED,
    )

    assert result.verification_status == VerificationStatus.VERIFIED_FAILURE
    assert result.execution_result == "failed"

    # Verify unconfirmed/failed state recorded in audit log
    latest = test_setup["audit"].get_latest_record()
    assert latest is not None
    assert latest.verification_result == "verified_failure"


def test_action_aborted_without_human_approval(test_setup):
    mgr = test_setup["manager"]
    worker = UserIdentity(rfid_uid="CARD_WORKER_002", name="Alfred", role=UserRole.WORKER)

    result = mgr.execute_action(
        action=ActionType.WATER_PLANT,
        priority=ActionPriority.NORMAL,
        requested_by=worker,
        approval_status=ApprovalStatus.PENDING,  # Not approved yet
    )

    assert result.dispatched is False
    assert result.execution_result == "aborted"
    assert result.verification_status == VerificationStatus.UNVERIFIED


def test_emergency_action_bypasses_approval(test_setup):
    mgr = test_setup["manager"]
    servo = test_setup["servo"]

    result = mgr.trigger_emergency(
        action=ActionType.CLOSE_VALVE,
        reason="Critical gas threshold exceeded",
        context={"ppm": 350.0},
    )

    assert result.dispatched is True
    assert result.priority == ActionPriority.EMERGENCY
    assert result.approval_status == ApprovalStatus.BYPASSED_EMERGENCY
    assert result.verification_status == VerificationStatus.VERIFIED_SUCCESS
    assert servo.get_state() == "0_DEG"
