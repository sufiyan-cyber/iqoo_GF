"""Hardware Abstraction Layer package exports."""

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
from bat_pod.hal.real_adapters import (
    RealAlarmActuator,
    RealDisplay,
    RealGasSensor,
    RealPumpActuator,
    RealRFIDProvider,
    RealServoActuator,
    RealSoilMoistureSensor,
    RealTemperatureSensor,
    RealTouchButton,
    SerialDeviceManager,
)
from bat_pod.hal.serial_protocol import SerialProtocol

__all__ = [
    "MockAlarmActuator",
    "MockAudioInput",
    "MockAudioOutput",
    "MockDisplay",
    "MockGasSensor",
    "MockPumpActuator",
    "MockRFIDProvider",
    "MockServoActuator",
    "MockSoilMoistureSensor",
    "MockTemperatureSensor",
    "MockTouchButton",
    "RealAlarmActuator",
    "RealDisplay",
    "RealGasSensor",
    "RealPumpActuator",
    "RealRFIDProvider",
    "RealServoActuator",
    "RealSoilMoistureSensor",
    "RealTemperatureSensor",
    "RealTouchButton",
    "SerialDeviceManager",
    "SerialProtocol",
]
