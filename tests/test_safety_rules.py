"""Unit tests for deterministic safety rules and emergency threshold logic."""

import pytest
from bat_pod.core.models import (
    ActionType,
    EnvironmentalSnapshot,
    SensorReading,
    SensorStatus,
    SensorType,
)
from bat_pod.safety.policy_engine import SafetyPolicyEngine


@pytest.fixture
def policy_engine():
    return SafetyPolicyEngine()


def test_safe_environment(policy_engine):
    snapshot = EnvironmentalSnapshot(
        temperature=SensorReading(sensor_type=SensorType.TEMPERATURE, value=25.0, unit="°C"),
        gas=SensorReading(sensor_type=SensorType.GAS, value=40.0, unit="PPM"),
        soil_moisture=SensorReading(sensor_type=SensorType.SOIL_MOISTURE, value=35.0, unit="%"),
    )
    evaluation = policy_engine.evaluate_environment(snapshot)
    assert evaluation.is_safe is True
    assert evaluation.is_emergency is False
    assert evaluation.emergency_action == ActionType.NONE


def test_gas_critical_emergency(policy_engine):
    # Above 300 PPM threshold
    snapshot = EnvironmentalSnapshot(
        temperature=SensorReading(sensor_type=SensorType.TEMPERATURE, value=25.0, unit="°C"),
        gas=SensorReading(sensor_type=SensorType.GAS, value=350.0, unit="PPM"),
        soil_moisture=SensorReading(sensor_type=SensorType.SOIL_MOISTURE, value=35.0, unit="%"),
    )
    evaluation = policy_engine.evaluate_environment(snapshot)
    assert evaluation.is_safe is False
    assert evaluation.is_emergency is True
    assert evaluation.hazard_detected == "GAS_LEAK"
    assert evaluation.emergency_action == ActionType.CLOSE_VALVE


def test_gas_warning_threshold(policy_engine):
    # Between 150 and 300 PPM
    snapshot = EnvironmentalSnapshot(
        temperature=SensorReading(sensor_type=SensorType.TEMPERATURE, value=25.0, unit="°C"),
        gas=SensorReading(sensor_type=SensorType.GAS, value=180.0, unit="PPM"),
        soil_moisture=SensorReading(sensor_type=SensorType.SOIL_MOISTURE, value=35.0, unit="%"),
    )
    evaluation = policy_engine.evaluate_environment(snapshot)
    assert evaluation.is_safe is False
    assert evaluation.is_emergency is False  # Warning, not immediate auto-shutdown


def test_extreme_temperature_critical(policy_engine):
    snapshot = EnvironmentalSnapshot(
        temperature=SensorReading(sensor_type=SensorType.TEMPERATURE, value=55.0, unit="°C"),
        gas=SensorReading(sensor_type=SensorType.GAS, value=50.0, unit="PPM"),
        soil_moisture=SensorReading(sensor_type=SensorType.SOIL_MOISTURE, value=35.0, unit="%"),
    )
    evaluation = policy_engine.evaluate_environment(snapshot)
    assert evaluation.is_safe is False
    assert evaluation.is_emergency is True
    assert evaluation.hazard_detected == "EXTREME_HEAT"


def test_action_safety_rejection(policy_engine):
    # Test that opening valve is refused when gas hazard is present
    snapshot = EnvironmentalSnapshot(
        gas=SensorReading(sensor_type=SensorType.GAS, value=250.0, unit="PPM"),
    )
    is_safe, reason = policy_engine.authorize_action_safety(ActionType.OPEN_VALVE, snapshot)
    assert is_safe is False
    assert "Refused" in reason


def test_overwatering_safety_rejection(policy_engine):
    # Test that overwatering saturated soil is refused
    snapshot = EnvironmentalSnapshot(
        soil_moisture=SensorReading(sensor_type=SensorType.SOIL_MOISTURE, value=92.0, unit="%"),
    )
    is_safe, reason = policy_engine.authorize_action_safety(ActionType.WATER_PLANT, snapshot)
    assert is_safe is False
    assert "Overwatering prevented" in reason
