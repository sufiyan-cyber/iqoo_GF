"""Action Manager enforcing authorization, closed-loop execution, and hardware verification."""

import logging
import uuid
from typing import Any, Dict, Optional
from bat_pod.audit.audit_logger import audit_logger, AuditLogger
from bat_pod.auth.rfid_auth import auth_manager, RFIDAuthenticator
from bat_pod.core.interfaces import IAlarmActuator, IPumpActuator, IServoActuator
from bat_pod.core.models import (
    ActionExecutionResult,
    ActionPriority,
    ActionType,
    ApprovalStatus,
    UserIdentity,
    UserRole,
    VerificationStatus,
)
from bat_pod.safety.policy_engine import safety_policy_engine, SafetyPolicyEngine

logger = logging.getLogger(__name__)


class ActionManager:
    """Coordinates actuator dispatch, safety enforcement, closed-loop verification, and audit logging."""

    def __init__(
        self,
        servo: Optional[IServoActuator] = None,
        pump: Optional[IPumpActuator] = None,
        alarm: Optional[IAlarmActuator] = None,
        audit_log: Optional[AuditLogger] = None,
        safety_engine: Optional[SafetyPolicyEngine] = None,
        auth: Optional[RFIDAuthenticator] = None,
    ) -> None:
        self.servo = servo
        self.pump = pump
        self.alarm = alarm
        self.audit_log = audit_log or audit_logger
        self.safety_engine = safety_engine or safety_policy_engine
        self.auth = auth or auth_manager

    def set_actuators(
        self,
        servo: Optional[IServoActuator] = None,
        pump: Optional[IPumpActuator] = None,
        alarm: Optional[IAlarmActuator] = None,
    ) -> None:
        """Bind physical or mock actuators."""
        if servo:
            self.servo = servo
        if pump:
            self.pump = pump
        if alarm:
            self.alarm = alarm

    def execute_action(
        self,
        action: ActionType,
        priority: ActionPriority,
        requested_by: UserIdentity,
        approval_status: ApprovalStatus,
        context: Optional[Dict[str, Any]] = None,
    ) -> ActionExecutionResult:
        """
        Execute an authorized physical action with mandatory closed-loop hardware verification.
        AI never touches this directly.
        """
        action_id = str(uuid.uuid4())[:8]
        ctx = context or {}

        # 1. Authorization check for non-emergency actions
        if priority != ActionPriority.EMERGENCY:
            is_authed, auth_reason = self.auth.check_permission(action, requested_by)
            if not is_authed:
                self.audit_log.log(
                    user=requested_by.name,
                    intent=f"action:{action.value}",
                    requested_action=action.value,
                    authorization=f"DENIED: {auth_reason}",
                    execution_result="aborted",
                    verification_result=VerificationStatus.UNVERIFIED.value,
                    sensor_context=ctx,
                    error=auth_reason,
                )
                return ActionExecutionResult(
                    action_id=action_id,
                    action_type=action,
                    priority=priority,
                    requested_by=requested_by.name,
                    authorized_by=None,
                    approval_status=ApprovalStatus.REJECTED,
                    dispatched=False,
                    execution_result="aborted",
                    verification_status=VerificationStatus.UNVERIFIED,
                    error=auth_reason,
                )

            # Check human approval requirement
            if approval_status != ApprovalStatus.APPROVED:
                err_msg = f"Action cancelled: Human approval not granted (status={approval_status.value})"
                return ActionExecutionResult(
                    action_id=action_id,
                    action_type=action,
                    priority=priority,
                    requested_by=requested_by.name,
                    authorized_by=requested_by.name,
                    approval_status=approval_status,
                    dispatched=False,
                    execution_result="aborted",
                    verification_status=VerificationStatus.UNVERIFIED,
                    error=err_msg,
                )

        # 2. Dispatch to physical/mock actuator
        dispatched = False
        target_state = "UNKNOWN"
        error_msg = None

        if action == ActionType.WATER_PLANT:
            # Water plant can be driven by a pump or a servo-assisted valve
            if self.pump:
                dispatched = self.pump.execute("START", {"duration_sec": 3.0})
                target_state = "RUNNING"
            elif self.servo:
                dispatched = self.servo.execute("SET_ANGLE", {"angle": 90})
                target_state = "90_DEG"
            else:
                error_msg = "No pump or servo actuator configured for watering."

        elif action in (ActionType.CLOSE_VALVE, ActionType.OPEN_VALVE):
            target_angle = 0 if action == ActionType.CLOSE_VALVE else 90
            target_state = f"{target_angle}_DEG"
            if self.servo:
                dispatched = self.servo.execute("SET_ANGLE", {"angle": target_angle})
            else:
                error_msg = "Servo actuator not available."

        elif action == ActionType.ACTIVATE_ALARM:
            if self.alarm:
                dispatched = self.alarm.execute("ALARM_ON")
                target_state = "ON"
            else:
                error_msg = "Alarm actuator not available."

        elif action == ActionType.DEACTIVATE_ALARM:
            if self.alarm:
                dispatched = self.alarm.execute("ALARM_OFF")
                target_state = "OFF"
            else:
                error_msg = "Alarm actuator not available."

        if not dispatched:
            fail_reason = error_msg or "Actuator driver rejected command dispatch."
            self.audit_log.log(
                user=requested_by.name,
                intent=f"action:{action.value}",
                requested_action=action.value,
                authorization=f"approved:{requested_by.role.value}",
                execution_result="failed",
                verification_result=VerificationStatus.UNVERIFIED.value,
                sensor_context=ctx,
                error=fail_reason,
            )
            return ActionExecutionResult(
                action_id=action_id,
                action_type=action,
                priority=priority,
                requested_by=requested_by.name,
                authorized_by=requested_by.name,
                approval_status=approval_status,
                dispatched=False,
                execution_result="failed",
                verification_status=VerificationStatus.UNVERIFIED,
                error=fail_reason,
            )

        # 3. Hardware Verification: Verify physical state actually changed!
        verification_status = VerificationStatus.UNVERIFIED
        verified_state = None

        if action in (ActionType.CLOSE_VALVE, ActionType.OPEN_VALVE) and self.servo:
            verification_status = self.servo.verify(target_state)
            verified_state = self.servo.get_state()
        elif action == ActionType.WATER_PLANT:
            if self.pump:
                verification_status = self.pump.verify(target_state)
                verified_state = self.pump.get_state()
            elif self.servo:
                verification_status = self.servo.verify(target_state)
                verified_state = self.servo.get_state()
        elif action in (ActionType.ACTIVATE_ALARM, ActionType.DEACTIVATE_ALARM) and self.alarm:
            verification_status = self.alarm.verify(target_state)
            verified_state = self.alarm.get_state()

        exec_res = "success" if verification_status == VerificationStatus.VERIFIED_SUCCESS else "unconfirmed"
        if verification_status == VerificationStatus.VERIFIED_FAILURE:
            exec_res = "failed"

        # 4. Record complete transaction in SQLite Audit Log
        self.audit_log.log(
            user=requested_by.name,
            intent=f"action:{action.value}",
            requested_action=action.value,
            authorization="emergency_override" if priority == ActionPriority.EMERGENCY else f"approved:{requested_by.role.value}",
            execution_result=exec_res,
            verification_result=verification_status.value,
            sensor_context=ctx,
            error=None if exec_res == "success" else f"Hardware verification reported: {verification_status.value}",
        )

        return ActionExecutionResult(
            action_id=action_id,
            action_type=action,
            priority=priority,
            requested_by=requested_by.name,
            authorized_by=requested_by.name if priority != ActionPriority.EMERGENCY else "SYSTEM_SAFETY_RULE",
            approval_status=approval_status,
            dispatched=True,
            execution_result=exec_res,
            verification_status=verification_status,
            verified_state=verified_state,
        )

    def trigger_emergency(self, action: ActionType, reason: str, context: Optional[Dict[str, Any]] = None) -> ActionExecutionResult:
        """Immediate deterministic emergency intervention bypassing human approval."""
        system_admin = UserIdentity(
            rfid_uid="SYSTEM_SAFETY",
            name="SAFETY_DAEMON",
            role=UserRole.ADMIN,
            is_authenticated=True,
        )
        logger.warning(f"EMERGENCY SAFETY ACTION TRIGGERED: {action.value} due to: {reason}")
        return self.execute_action(
            action=action,
            priority=ActionPriority.EMERGENCY,
            requested_by=system_admin,
            approval_status=ApprovalStatus.BYPASSED_EMERGENCY,
            context={"emergency_reason": reason, **(context or {})},
        )

    def enter_safe_state(self) -> None:
        """Drive all actuators into safe fallback state."""
        logger.critical("Entering HARDWARE SAFE STATE across all actuators.")
        if self.servo:
            self.servo.emergency_safe_state()
        if self.pump:
            self.pump.emergency_safe_state()
        if self.alarm:
            self.alarm.execute("ALARM_OFF")


# Default global instance
action_manager = ActionManager()
