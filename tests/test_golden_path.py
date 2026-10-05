"""End-to-End integration test executing the complete 11-step MVP Golden Path."""

import os
import tempfile
import pytest
from bat_pod.audit.audit_logger import AuditLogger
from bat_pod.core.models import (
    ActionPriority,
    ActionType,
    ApprovalStatus,
    DisplayState,
    UserRole,
    VerificationStatus,
)
from bat_pod.hal.mock_adapters import (
    MockAlarmActuator,
    MockAudioInput,
    MockAudioOutput,
    MockDisplay,
    MockGasSensor,
    MockPumpActuator,
    MockRFIDProvider,
    MockServoActuator,
    MockSoilMoistureSensor,
    MockTemperatureSensor,
    MockTouchButton,
)
from bat_pod.orchestrator.pod_controller import BatPodController


@pytest.fixture
def golden_path_system():
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db.close()

    temp_s = MockTemperatureSensor(initial_c=26.0)
    gas_s = MockGasSensor(initial_ppm=42.0)
    soil_s = MockSoilMoistureSensor(initial_pct=21.0)
    servo = MockServoActuator(initial_angle=90)
    pump = MockPumpActuator()
    alarm = MockAlarmActuator()
    rfid = MockRFIDProvider()
    touch = MockTouchButton()
    display = MockDisplay()
    audio_out = MockAudioOutput()
    audit = AuditLogger(db_path=temp_db.name)

    controller = BatPodController(
        temp_sensor=temp_s,
        gas_sensor=gas_s,
        soil_sensor=soil_s,
        servo=servo,
        pump=pump,
        alarm=alarm,
        rfid=rfid,
        touch=touch,
        display=display,
        audio_out=audio_out,
        audit=audit,
    )

    yield {
        "controller": controller,
        "temp_s": temp_s,
        "gas_s": gas_s,
        "soil_s": soil_s,
        "servo": servo,
        "pump": pump,
        "alarm": alarm,
        "rfid": rfid,
        "display": display,
        "audio_out": audio_out,
        "audit": audit,
    }

    try:
        os.remove(temp_db.name)
    except Exception:
        pass


def test_complete_golden_path_scenario(golden_path_system):
    ctrl = golden_path_system["controller"]
    rfid = golden_path_system["rfid"]
    gas_s = golden_path_system["gas_s"]
    servo = golden_path_system["servo"]
    alarm = golden_path_system["alarm"]
    display = golden_path_system["display"]
    audit = golden_path_system["audit"]

    # Step 1: User taps RFID
    rfid.tap_card("CARD_ADMIN_001")
    ctrl.sense()
    user = ctrl.auth.get_active_user()
    assert user.name == "Bruce Wayne"
    assert user.role == UserRole.ADMIN

    # Step 2: User asks: "BAT POD, is the environment safe?"
    resp_safe = ctrl.process_utterance("BAT POD, is the environment safe?")
    assert "26.0" in resp_safe
    assert "safe" in resp_safe.lower()
    assert display.current_state == DisplayState.NORMAL

    # Step 3: User says: "Water the plant."
    resp_water = ctrl.process_utterance("Water the plant.")
    assert "Water the plant?" in resp_water
    assert "21.0%" in resp_water
    assert display.current_state == DisplayState.APPROVAL

    # Step 4: User approves
    action_result = ctrl.handle_user_approval(approved=True)
    assert action_result is not None
    assert action_result.execution_result == "success"
    assert action_result.verification_status == VerificationStatus.VERIFIED_SUCCESS
    assert display.current_state == DisplayState.NORMAL

    # Step 5: Gas sensor test spikes above 300 PPM threshold
    gas_s.set_value(350.0)
    ctrl.sense()

    # Step 6: Emergency response triggered automatically
    assert servo.get_state() == "0_DEG"  # Valve closed!
    assert alarm.get_state() == "ON"     # Alarm active!
    assert display.current_state == DisplayState.EMERGENCY

    # Step 7: Check audit record was created for the emergency event
    latest = audit.get_latest_emergency_or_action()
    assert latest is not None
    assert latest.requested_action == "close_valve"
    assert "emergency" in latest.authorization

    # Step 8: User asks: "What happened?"
    resp_explain = ctrl.process_utterance("What happened?")
    assert "gas" in resp_explain.lower()
    assert "valve was automatically closed" in resp_explain
    assert "alarm" in resp_explain.lower()
