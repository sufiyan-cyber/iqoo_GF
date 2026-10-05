"""Unit tests for sensor readings, health validation, and failure handling."""

import pytest
from bat_pod.core.models import SensorReading, SensorStatus, SensorType
from bat_pod.hal.mock_adapters import (
    MockGasSensor,
    MockSoilMoistureSensor,
    MockTemperatureSensor,
)
from bat_pod.safety.rules import evaluate_sensor_health


def test_temperature_sensor_valid():
    sensor = MockTemperatureSensor(initial_c=25.5)
    reading = sensor.read()
    assert reading.is_valid() is True
    assert reading.sensor_type == SensorType.TEMPERATURE
    assert reading.value == 25.5
    assert reading.status == SensorStatus.OK
    assert evaluate_sensor_health(reading, SensorType.TEMPERATURE) is None


def test_gas_sensor_valid():
    sensor = MockGasSensor(initial_ppm=45.0)
    reading = sensor.read()
    assert reading.is_valid() is True
    assert reading.sensor_type == SensorType.GAS
    assert reading.value == 45.0
    assert evaluate_sensor_health(reading, SensorType.GAS) is None


def test_soil_moisture_valid():
    sensor = MockSoilMoistureSensor(initial_pct=30.0)
    reading = sensor.read()
    assert reading.is_valid() is True
    assert reading.sensor_type == SensorType.SOIL_MOISTURE
    assert reading.value == 30.0
    assert evaluate_sensor_health(reading, SensorType.SOIL_MOISTURE) is None


def test_sensor_unhealthy_or_disconnected():
    sensor = MockTemperatureSensor()
    sensor.healthy = False
    reading = sensor.read()
    assert reading.is_valid() is False
    assert reading.status == SensorStatus.DISCONNECTED
    err = evaluate_sensor_health(reading, SensorType.TEMPERATURE)
    assert err is not None
    assert "DISCONNECTED" in err


def test_sensor_out_of_bounds_reading():
    reading = SensorReading(
        sensor_type=SensorType.TEMPERATURE,
        value=150.0,  # Unrealistic 150°C
        unit="°C",
        status=SensorStatus.OK,
    )
    err = evaluate_sensor_health(reading, SensorType.TEMPERATURE)
    assert err is not None
    assert "operating range" in err


def test_sensor_null_reading():
    reading = SensorReading(
        sensor_type=SensorType.GAS,
        value=None,
        unit="PPM",
        status=SensorStatus.INVALID,
    )
    assert reading.is_valid() is False
    err = evaluate_sensor_health(reading, SensorType.GAS)
    assert err is not None
