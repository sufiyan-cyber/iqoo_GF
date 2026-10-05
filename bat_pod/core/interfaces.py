"""Abstract interfaces for BAT POD Hardware Abstraction Layer (HAL)."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from bat_pod.core.models import (
    SensorReading,
    SensorType,
    VerificationStatus,
    DisplayState,
)


class ISensor(ABC):
    """Base interface for all physical and mock sensors."""

    @abstractmethod
    def read(self) -> SensorReading:
        """Poll the sensor and return a standardized reading."""
        pass

    @abstractmethod
    def get_type(self) -> SensorType:
        """Return the sensor type."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Return True if the sensor is functional and responding."""
        pass


class ITemperatureSensor(ISensor):
    """Temperature sensor interface."""
    pass


class IGasSensor(ISensor):
    """Gas / MQ sensor interface."""
    pass


class ISoilMoistureSensor(ISensor):
    """Soil moisture sensor interface."""
    pass


class IActuator(ABC):
    """Base interface for all physical and mock actuators."""

    @abstractmethod
    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Send command to actuator. Returns True if dispatch succeeded."""
        pass

    @abstractmethod
    def verify(self, expected_state: str, timeout_sec: float = 2.0) -> VerificationStatus:
        """Verify the physical hardware state matches the expected state."""
        pass

    @abstractmethod
    def get_state(self) -> str:
        """Return the current reported physical state."""
        pass

    @abstractmethod
    def emergency_safe_state(self) -> bool:
        """Immediately drive actuator into the deterministic safe fallback state."""
        pass


class IServoActuator(IActuator):
    """Servo motor interface for simulated valve or lock control."""
    pass


class IPumpActuator(IActuator):
    """Water pump actuator interface."""
    pass


class IAlarmActuator(IActuator):
    """Audible buzzer / LED warning actuator interface."""
    pass


class IRFIDProvider(ABC):
    """RFID Card reader interface."""

    @abstractmethod
    def poll_card(self) -> Optional[str]:
        """Poll reader and return card UID if present, else None."""
        pass


class ITouchButtonProvider(ABC):
    """Touch button interface for manual user approval."""

    @abstractmethod
    def is_pressed(self) -> bool:
        """Return True if the touch button is currently pressed."""
        pass

    @abstractmethod
    def wait_for_press(self, timeout_sec: float = 30.0) -> bool:
        """Block until button pressed or timeout expires."""
        pass


class IDisplay(ABC):
    """Visual display interface (OLED screen or simulated TUI)."""

    @abstractmethod
    def show_screen(self, state: DisplayState, context: Dict[str, Any]) -> None:
        """Update display layout according to state and environmental context."""
        pass


class IAudioInput(ABC):
    """Microphone / Voice input provider."""

    @abstractmethod
    def listen_and_transcribe(self, timeout_sec: float = 5.0) -> Optional[str]:
        """Capture audio and return transcribed speech text."""
        pass


class IAudioOutput(ABC):
    """Speaker / Text-to-Speech provider."""

    @abstractmethod
    def speak(self, text: str, language: str = "en-IN") -> None:
        """Speak out text via speaker or simulated audio output."""
        pass
