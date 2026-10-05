"""Deterministic safety policy engine enforcing safety constraints."""

import logging
from typing import Tuple
from bat_pod.core.models import (
    ActionType,
    EnvironmentalSnapshot,
    SensorType,
)
from bat_pod.safety.rules import (
    SafetyEvaluation,
    evaluate_gas_hazard,
    evaluate_sensor_health,
    evaluate_temperature_hazard,
)

logger = logging.getLogger(__name__)


class SafetyPolicyEngine:
    """Evaluates environmental data against hardcoded deterministic safety rules."""

    def evaluate_environment(self, snapshot: EnvironmentalSnapshot) -> SafetyEvaluation:
        """Examine snapshot and determine overall safety state."""
        evaluation = SafetyEvaluation()

        # 1. Health checks on each sensor
        for s_type, reading in [
            (SensorType.TEMPERATURE, snapshot.temperature),
            (SensorType.GAS, snapshot.gas),
            (SensorType.SOIL_MOISTURE, snapshot.soil_moisture),
        ]:
            err = evaluate_sensor_health(reading, s_type)
            if err:
                evaluation.violations.append(err)
                evaluation.invalid_sensors.append(s_type)

        # 2. Check Gas Hazard
        is_gas_crit, is_gas_warn, gas_msg = evaluate_gas_hazard(snapshot.gas)
        if is_gas_crit:
            evaluation.is_safe = False
            evaluation.is_emergency = True
            evaluation.hazard_detected = "GAS_LEAK"
            evaluation.emergency_action = ActionType.CLOSE_VALVE
            evaluation.violations.append(gas_msg or "Gas critical threshold exceeded")
        elif is_gas_warn:
            evaluation.is_safe = False
            evaluation.violations.append(gas_msg or "Elevated gas detected")

        # 3. Check Temperature Hazard
        is_temp_crit, is_temp_warn, temp_msg = evaluate_temperature_hazard(snapshot.temperature)
        if is_temp_crit:
            evaluation.is_safe = False
            evaluation.is_emergency = True
            evaluation.hazard_detected = evaluation.hazard_detected or "EXTREME_HEAT"
            if evaluation.emergency_action == ActionType.NONE:
                evaluation.emergency_action = ActionType.ACTIVATE_ALARM
            evaluation.violations.append(temp_msg or "Extreme heat detected")
        elif is_temp_warn:
            evaluation.violations.append(temp_msg or "High temperature warning")

        # 4. Formulate summary
        if evaluation.is_emergency:
            evaluation.summary = f"EMERGENCY: {evaluation.hazard_detected} detected!"
        elif not evaluation.is_safe:
            evaluation.summary = "Warning: Environmental hazards present."
        elif evaluation.invalid_sensors:
            evaluation.summary = f"Notice: {len(evaluation.invalid_sensors)} sensor(s) reporting invalid status."
        else:
            evaluation.summary = "Everything OK. Environment is safe."

        return evaluation

    def authorize_action_safety(
        self, action: ActionType, snapshot: EnvironmentalSnapshot
    ) -> Tuple[bool, str]:
        """
        Verify if an action is safe to execute given the current environmental state.
        Deterministic rules prevent dangerous conflicts.
        """
        # Rule 1: Never open valve if gas hazard is present
        if action == ActionType.OPEN_VALVE:
            if snapshot.gas and snapshot.gas.is_valid() and (snapshot.gas.value or 0) > 100:
                return False, "Refused: Cannot open valve while elevated gas is present."

        # Rule 2: Water plant checks
        if action == ActionType.WATER_PLANT:
            if snapshot.soil_moisture and snapshot.soil_moisture.is_valid():
                if (snapshot.soil_moisture.value or 0) > 85.0:
                    return False, f"Refused: Soil moisture is already high ({snapshot.soil_moisture.value}%). Overwatering prevented."
            if snapshot.gas and snapshot.gas.is_valid() and (snapshot.gas.value or 0) >= 300:
                return False, "Refused: Critical gas hazard in progress. Physical actions halted."

        return True, "Safety check passed."


# Default global instance
safety_policy_engine = SafetyPolicyEngine()
