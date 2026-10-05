"""Sensor Context Retrieval module for filtering relevant telemetry based on parsed intent."""

from typing import Any, Dict
from bat_pod.core.models import (
    EnvironmentalSnapshot,
    IntentType,
    ParsedIntent,
    SensorType,
)


class SensorContextRetriever:
    """Retrieves only sensor context strictly necessary for a given intent."""

    INTENT_SENSOR_MAP = {
        IntentType.CHECK_SAFETY: [SensorType.TEMPERATURE, SensorType.GAS, SensorType.SOIL_MOISTURE],
        IntentType.CHECK_GAS: [SensorType.GAS],
        IntentType.CHECK_TEMPERATURE: [SensorType.TEMPERATURE],
        IntentType.CHECK_SOIL: [SensorType.SOIL_MOISTURE],
        IntentType.WATER_PLANT: [SensorType.SOIL_MOISTURE, SensorType.GAS],
        IntentType.CLOSE_VALVE: [SensorType.GAS, SensorType.TEMPERATURE],
        IntentType.EXPLAIN_EVENT: [SensorType.GAS, SensorType.TEMPERATURE, SensorType.SOIL_MOISTURE],
    }

    def retrieve_context(self, intent: ParsedIntent, snapshot: EnvironmentalSnapshot) -> Dict[str, Any]:
        """Filter snapshot to only the sensors relevant to the specific user intent."""
        relevant_types = self.INTENT_SENSOR_MAP.get(
            intent.intent,
            [SensorType.TEMPERATURE, SensorType.GAS, SensorType.SOIL_MOISTURE],
        )

        context: Dict[str, Any] = {
            "timestamp": snapshot.timestamp.isoformat(),
            "overall_safe": snapshot.is_safe,
            "overall_summary": snapshot.safety_summary,
            "relevant_readings": {},
        }

        if SensorType.TEMPERATURE in relevant_types and snapshot.temperature:
            context["relevant_readings"]["temperature"] = {
                "value": snapshot.temperature.value,
                "unit": snapshot.temperature.unit,
                "status": snapshot.temperature.status.value,
                "is_valid": snapshot.temperature.is_valid(),
            }

        if SensorType.GAS in relevant_types and snapshot.gas:
            context["relevant_readings"]["gas"] = {
                "value": snapshot.gas.value,
                "unit": snapshot.gas.unit,
                "status": snapshot.gas.status.value,
                "is_valid": snapshot.gas.is_valid(),
            }

        if SensorType.SOIL_MOISTURE in relevant_types and snapshot.soil_moisture:
            context["relevant_readings"]["soil_moisture"] = {
                "value": snapshot.soil_moisture.value,
                "unit": snapshot.soil_moisture.unit,
                "status": snapshot.soil_moisture.status.value,
                "is_valid": snapshot.soil_moisture.is_valid(),
            }

        return context


context_retriever = SensorContextRetriever()
