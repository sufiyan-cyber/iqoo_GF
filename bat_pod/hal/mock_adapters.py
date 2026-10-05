"""Mock hardware adapters providing high-fidelity simulation for offline testing."""

import time
from typing import Any, Dict, Optional
from bat_pod.core.interfaces import (
    IAlarmActuator,
    IAudioInput,
    IAudioOutput,
    IDisplay,
    IGasSensor,
    IPumpActuator,
    IRFIDProvider,
    IServoActuator,
    ISoilMoistureSensor,
    ITemperatureSensor,
    ITouchButtonProvider,
)
from bat_pod.core.models import (
    DisplayState,
    SensorReading,
    SensorStatus,
    SensorType,
    VerificationStatus,
)


class MockTemperatureSensor(ITemperatureSensor):
    """Simulated digital temperature sensor."""

    def __init__(self, initial_c: float = 26.0) -> None:
        self.current_value = initial_c
        self.status = SensorStatus.OK
        self.healthy = True

    def read(self) -> SensorReading:
        if not self.healthy:
            return SensorReading(
                sensor_type=SensorType.TEMPERATURE,
                value=None,
                unit="°C",
                status=SensorStatus.DISCONNECTED,
                error_message="Sensor hardware offline or disconnected",
            )
        return SensorReading(
            sensor_type=SensorType.TEMPERATURE,
            value=self.current_value,
            unit="°C",
            status=self.status,
            raw_value=self.current_value,
        )

    def get_type(self) -> SensorType:
        return SensorType.TEMPERATURE

    def is_healthy(self) -> bool:
        return self.healthy

    def set_value(self, temp_c: float, status: SensorStatus = SensorStatus.OK) -> None:
        self.current_value = temp_c
        self.status = status


class MockGasSensor(IGasSensor):
    """Simulated MQ gas sensor."""

    def __init__(self, initial_ppm: float = 45.0) -> None:
        self.current_value = initial_ppm
        self.status = SensorStatus.OK
        self.healthy = True

    def read(self) -> SensorReading:
        if not self.healthy:
            return SensorReading(
                sensor_type=SensorType.GAS,
                value=None,
                unit="PPM",
                status=SensorStatus.DISCONNECTED,
                error_message="Gas sensor bus fault",
            )
        return SensorReading(
            sensor_type=SensorType.GAS,
            value=self.current_value,
            unit="PPM",
            status=self.status,
            raw_value=self.current_value,
        )

    def get_type(self) -> SensorType:
        return SensorType.GAS

    def is_healthy(self) -> bool:
        return self.healthy

    def set_value(self, ppm: float, status: SensorStatus = SensorStatus.OK) -> None:
        self.current_value = ppm
        self.status = status


class MockSoilMoistureSensor(ISoilMoistureSensor):
    """Simulated capacitive soil moisture sensor."""

    def __init__(self, initial_pct: float = 21.0) -> None:
        self.current_value = initial_pct
        self.status = SensorStatus.OK
        self.healthy = True

    def read(self) -> SensorReading:
        if not self.healthy:
            return SensorReading(
                sensor_type=SensorType.SOIL_MOISTURE,
                value=None,
                unit="%",
                status=SensorStatus.DISCONNECTED,
                error_message="Soil sensor unreadable",
            )
        return SensorReading(
            sensor_type=SensorType.SOIL_MOISTURE,
            value=self.current_value,
            unit="%",
            status=self.status,
            raw_value=self.current_value,
        )

    def get_type(self) -> SensorType:
        return SensorType.SOIL_MOISTURE

    def is_healthy(self) -> bool:
        return self.healthy

    def set_value(self, pct: float, status: SensorStatus = SensorStatus.OK) -> None:
        self.current_value = pct
        self.status = status


class MockServoActuator(IServoActuator):
    """Simulated physical servo motor with angle feedback."""

    def __init__(self, initial_angle: int = 90) -> None:
        self.target_angle = initial_angle
        self.actual_angle = initial_angle
        self.simulate_verification_failure = False

    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        if command == "SET_ANGLE":
            params = parameters or {}
            self.target_angle = int(params.get("angle", 90))
            if not self.simulate_verification_failure:
                self.actual_angle = self.target_angle
            return True
        return False

    def verify(self, expected_state: str, timeout_sec: float = 2.0) -> VerificationStatus:
        if self.simulate_verification_failure:
            return VerificationStatus.VERIFIED_FAILURE
        current = f"{self.actual_angle}_DEG"
        if current == expected_state:
            return VerificationStatus.VERIFIED_SUCCESS
        return VerificationStatus.VERIFIED_FAILURE

    def get_state(self) -> str:
        return f"{self.actual_angle}_DEG"

    def emergency_safe_state(self) -> bool:
        self.target_angle = 0  # 0 degrees = Closed valve
        self.actual_angle = 0
        return True


class MockPumpActuator(IPumpActuator):
    """Simulated 5V DC relay water pump."""

    def __init__(self) -> None:
        self.is_running = False
        self.simulate_verification_failure = False

    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        if command == "START":
            self.is_running = True
            return True
        elif command == "STOP":
            self.is_running = False
            return True
        return False

    def verify(self, expected_state: str, timeout_sec: float = 2.0) -> VerificationStatus:
        if self.simulate_verification_failure:
            return VerificationStatus.VERIFIED_FAILURE
        curr = "RUNNING" if self.is_running else "STOPPED"
        return VerificationStatus.VERIFIED_SUCCESS if curr == expected_state else VerificationStatus.VERIFIED_FAILURE

    def get_state(self) -> str:
        return "RUNNING" if self.is_running else "STOPPED"

    def emergency_safe_state(self) -> bool:
        self.is_running = False
        return True


class MockAlarmActuator(IAlarmActuator):
    """Simulated buzzer and strobe alarm."""

    def __init__(self) -> None:
        self.alarm_active = False

    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        if command == "ALARM_ON":
            self.alarm_active = True
            return True
        elif command == "ALARM_OFF":
            self.alarm_active = False
            return True
        return False

    def verify(self, expected_state: str, timeout_sec: float = 2.0) -> VerificationStatus:
        curr = "ON" if self.alarm_active else "OFF"
        return VerificationStatus.VERIFIED_SUCCESS if curr == expected_state else VerificationStatus.VERIFIED_FAILURE

    def get_state(self) -> str:
        return "ON" if self.alarm_active else "OFF"

    def emergency_safe_state(self) -> bool:
        self.alarm_active = False
        return True


class MockRFIDProvider(IRFIDProvider):
    """Simulated RC522 RFID reader."""

    def __init__(self) -> None:
        self._queued_card: Optional[str] = None

    def tap_card(self, uid: str) -> None:
        """Simulate tapping an RFID card."""
        self._queued_card = uid

    def poll_card(self) -> Optional[str]:
        card = self._queued_card
        self._queued_card = None
        return card


class MockTouchButton(ITouchButtonProvider):
    """Simulated capacitive touch sensor."""

    def __init__(self) -> None:
        self._pressed = False

    def press(self) -> None:
        """Trigger button press simulation."""
        self._pressed = True

    def is_pressed(self) -> bool:
        pressed = self._pressed
        self._pressed = False
        return pressed

    def wait_for_press(self, timeout_sec: float = 5.0) -> bool:
        start = time.time()
        while time.time() - start < timeout_sec:
            if self._pressed:
                self._pressed = False
                return True
            time.sleep(0.05)
        return False


class MockDisplay(IDisplay):
    """Simulates device OLED / TFT display according to PRD screen designs."""

    def __init__(self) -> None:
        self.current_screen_text = ""
        self.current_state = DisplayState.NORMAL

    def show_screen(self, state: DisplayState, context: Dict[str, Any]) -> None:
        self.current_state = state
        lines = []

        if state == DisplayState.NORMAL:
            temp = context.get("temp", "--")
            gas = context.get("gas", "--")
            soil = context.get("soil", "--")
            summary = context.get("summary", "Everything OK")
            lines = [
                "┌────────────────────────────────┐",
                "│            BAT POD             │",
                "├────────────────────────────────┤",
                f"│ TEMP       {temp:<20}│",
                f"│ GAS        {gas:<20}│",
                f"│ SOIL       {soil:<20}│",
                "│                                │",
                "│ STATUS                         │",
                f"│ {summary:<31}│",
                "└────────────────────────────────┘",
            ]

        elif state == DisplayState.APPROVAL:
            action_name = context.get("action_name", "Action Request")
            detail = context.get("detail", "")
            lines = [
                "┌────────────────────────────────┐",
                "│         ACTION REQUEST         │",
                "├────────────────────────────────┤",
                f"│ {action_name:<31}│",
                "│                                │",
                f"│ {detail:<31}│",
                "│                                │",
                "│ [ APPROVE ]       [ CANCEL ]   │",
                "└────────────────────────────────┘",
            ]

        elif state == DisplayState.EMERGENCY:
            hazard = context.get("hazard", "HAZARD DETECTED")
            action_desc = context.get("action", "Intervention Active")
            lines = [
                "┌────────────────────────────────┐",
                "│         ⚠ WARNING ⚠            │",
                "├────────────────────────────────┤",
                f"│ {hazard:<31}│",
                "│                                │",
                f"│ {action_desc:<31}│",
                "│                                │",
                "│ >>> ALARM ACTIVE <<<           │",
                "└────────────────────────────────┘",
            ]

        self.current_screen_text = "\n".join(lines)


class MockAudioInput(IAudioInput):
    """Simulated voice input queue."""

    def __init__(self) -> None:
        self._spoken_text: Optional[str] = None

    def inject_speech(self, text: str) -> None:
        self._spoken_text = text

    def listen_and_transcribe(self, timeout_sec: float = 5.0) -> Optional[str]:
        text = self._spoken_text
        self._spoken_text = None
        return text


class MockAudioOutput(IAudioOutput):
    """Simulated speaker and speech synthesizer."""

    def __init__(self) -> None:
        self.last_spoken: Optional[str] = None
        self.history: list[str] = []

    def speak(self, text: str, language: str = "en-IN") -> None:
        self.last_spoken = text
        self.history.append(text)
