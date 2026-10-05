"""Unit tests for the AI intent extraction, context retrieval, and response pipeline."""

import pytest
from bat_pod.ai.context_retriever import SensorContextRetriever
from bat_pod.ai.intent_parser import IntentParser
from bat_pod.ai.response_generator import ResponseGenerator
from bat_pod.core.models import (
    ActionType,
    EnvironmentalSnapshot,
    IntentType,
    ParsedIntent,
    SensorReading,
    SensorType,
)


@pytest.fixture
def parser():
    return IntentParser()


@pytest.fixture
def context_retriever():
    return SensorContextRetriever()


@pytest.fixture
def response_gen():
    return ResponseGenerator()


def test_intent_parsing_safety(parser):
    res = parser.parse("BAT POD, is the environment safe?")
    assert res.intent == IntentType.CHECK_SAFETY


def test_intent_parsing_gas(parser):
    res = parser.parse("Is there any gas leak detected?")
    assert res.intent == IntentType.CHECK_GAS


def test_intent_parsing_temperature(parser):
    res = parser.parse("Is the temperature normal?")
    assert res.intent == IntentType.CHECK_TEMPERATURE


def test_intent_parsing_soil(parser):
    res = parser.parse("Does the plant need water?")
    assert res.intent == IntentType.CHECK_SOIL


def test_intent_parsing_water_plant(parser):
    res = parser.parse("Water the plant.")
    assert res.intent == IntentType.WATER_PLANT
    assert res.action == ActionType.WATER_PLANT


def test_intent_parsing_what_happened(parser):
    res = parser.parse("What happened?")
    assert res.intent == IntentType.EXPLAIN_EVENT


def test_intent_parsing_unknown(parser):
    res = parser.parse("Tell me a funny joke about quantum physics.")
    assert res.intent == IntentType.UNKNOWN


def test_sensor_context_retrieval(context_retriever):
    snapshot = EnvironmentalSnapshot(
        temperature=SensorReading(sensor_type=SensorType.TEMPERATURE, value=26.0, unit="°C"),
        gas=SensorReading(sensor_type=SensorType.GAS, value=42.0, unit="PPM"),
        soil_moisture=SensorReading(sensor_type=SensorType.SOIL_MOISTURE, value=19.0, unit="%"),
    )

    # For check_gas, only gas should be retrieved
    gas_intent = ParsedIntent(intent=IntentType.CHECK_GAS)
    ctx = context_retriever.retrieve_context(gas_intent, snapshot)
    readings = ctx["relevant_readings"]
    assert "gas" in readings
    assert "soil_moisture" not in readings

    # For water_plant, soil moisture should be retrieved
    water_intent = ParsedIntent(intent=IntentType.WATER_PLANT, action=ActionType.WATER_PLANT)
    ctx_w = context_retriever.retrieve_context(water_intent, snapshot)
    assert "soil_moisture" in ctx_w["relevant_readings"]


def test_response_generator_safety(response_gen):
    snapshot = EnvironmentalSnapshot(
        temperature=SensorReading(sensor_type=SensorType.TEMPERATURE, value=26.0, unit="°C"),
        gas=SensorReading(sensor_type=SensorType.GAS, value=42.0, unit="PPM"),
        soil_moisture=SensorReading(sensor_type=SensorType.SOIL_MOISTURE, value=21.0, unit="%"),
        is_safe=True,
    )
    intent = ParsedIntent(intent=IntentType.CHECK_SAFETY)
    resp = response_gen.generate_sensor_response(intent, snapshot, language="en")
    assert "26.0" in resp
    assert "Everything is safe" in resp

