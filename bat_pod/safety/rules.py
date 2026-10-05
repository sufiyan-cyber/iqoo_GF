"""Deterministic safety rules for environmental conditions and sensor validation."""

from typing import List, Optional
from pydantic import BaseModel, Field
from bat_pod.config import settings
from bat_pod.core.models import (
    ActionType,
    EnvironmentalSnapshot,
    SensorReading,
    SensorStatus,
    SensorType,
)


class SafetyEvaluation(BaseModel):
    """Result of deterministic rule checks over environmental data."""

    is_safe: bool = True
    is_emergency: bool = False
    hazard_detected: Optional[str] = None
    emergency_action: ActionType = ActionType.NONE
    summary: str = "Everything OK"
    violations: List[str] = Field(default_factory=list)
    invalid_sensors: List[SensorType] = Field(default_factory=list)


def evaluate_sensor_health(reading: Optional[SensorReading], sensor_type: SensorType) -> Optional[str]:
    """Validate that a sensor reading is present and within physically plausible bounds."""
    if reading is None:
        return f"{sensor_type.value} sensor reading is missing"
    if reading.status in (SensorStatus.INVALID, SensorStatus.DISCONNECTED):
        return f"{sensor_type.value} sensor reported status {reading.status.value}"
    if reading.value is None:
        return f"{sensor_type.value} sensor returned a null value"

    # Plausibility boundary checks
    if sensor_type == SensorType.TEMPERATURE:
        if reading.value < -20.0 or reading.value > 100.0:
            return f"Temperature {reading.value}°C out of realistic operating range (-20 to 100°C)"
    elif sensor_type == SensorType.GAS:
        if reading.value < 0.0 or reading.value > 10000.0:
            return f"Gas {reading.value} PPM out of plausible sensor range (0 to 10000 PPM)"
    elif sensor_type == SensorType.SOIL_MOISTURE:
        if reading.value < 0.0 or reading.value > 100.0:
            return f"Soil moisture {reading.value}% out of valid percentage range (0 to 100%)"

    return None


def evaluate_gas_hazard(reading: Optional[SensorReading]) -> tuple[bool, bool, Optional[str]]:
    """
    Evaluate gas sensor reading.
    Returns: (is_emergency, is_warning, message)
    """
    if reading is None or not reading.is_valid():
        return False, False, None

    ppm = reading.value or 0.0
    if ppm >= settings.GAS_CRITICAL_THRESHOLD_PPM:
        return True, True, f"CRITICAL: Gas concentration dangerous ({ppm:.1f} PPM >= {settings.GAS_CRITICAL_THRESHOLD_PPM} PPM threshold)"
    if ppm >= settings.GAS_WARNING_THRESHOLD_PPM:
        return False, True, f"WARNING: Elevated gas levels detected ({ppm:.1f} PPM)"

    return False, False, None


def evaluate_temperature_hazard(reading: Optional[SensorReading]) -> tuple[bool, bool, Optional[str]]:
    """
    Evaluate temperature reading.
    Returns: (is_emergency, is_warning, message)
    """
    if reading is None or not reading.is_valid():
        return False, False, None

    temp_c = reading.value or 0.0
    if temp_c >= settings.TEMP_CRITICAL_HIGH_C:
        return True, True, f"CRITICAL: Extreme high temperature ({temp_c:.1f}°C >= {settings.TEMP_CRITICAL_HIGH_C}°C)"
    if temp_c >= settings.TEMP_WARNING_HIGH_C:
        return False, True, f"WARNING: High temperature warning ({temp_c:.1f}°C)"

    return False, False, None
