"""Response Generator formulating contextual natural-language speech responses."""

from typing import Any, Dict, Optional
from bat_pod.audit.audit_logger import AuditLogger, audit_logger
from bat_pod.core.models import (
    ActionExecutionResult,
    ActionType,
    EnvironmentalSnapshot,
    IntentType,
    ParsedIntent,
    VerificationStatus,
)


class ResponseGenerator:
    """Generates natural language responses for voice output in English and Kannada."""

    def __init__(self, audit_log: Optional[AuditLogger] = None) -> None:
        self.audit_log = audit_log or audit_logger

    def generate_sensor_response(
        self,
        intent: ParsedIntent,
        snapshot: EnvironmentalSnapshot,
        language: str = "en",
    ) -> str:
        """Formulate response for sensor and environmental queries."""
        is_kannada = language.lower().startswith("kn")

        temp_val = f"{snapshot.temperature.value:.1f}°C" if snapshot.temperature and snapshot.temperature.is_valid() else "unavailable"
        gas_val = f"{snapshot.gas.value:.1f} PPM" if snapshot.gas and snapshot.gas.is_valid() else "unavailable"
        gas_safe = (snapshot.gas.value or 0) < 150 if snapshot.gas and snapshot.gas.is_valid() else False
        soil_val = f"{snapshot.soil_moisture.value:.1f}%" if snapshot.soil_moisture and snapshot.soil_moisture.is_valid() else "unavailable"

        if intent.intent == IntentType.CHECK_SAFETY:
            if is_kannada:
                if snapshot.is_safe:
                    return f"ವಾತಾವರಣ ಸುರಕ್ಷಿತವಾಗಿದೆ. ತಾಪಮಾನ {temp_val}. ಅನಿಲ ಸೋರಿಕೆ ಇಲ್ಲ. ಮಣ್ಣಿನ ತೇವಾಂಶ {soil_val}."
                return f"ಎಚ್ಚರಿಕೆ! ವಾತಾವರಣ ಸುರಕ್ಷಿತವಾಗಿಲ್ಲ: {snapshot.safety_summary}"
            else:
                if snapshot.is_safe:
                    gas_str = "No gas detected." if gas_safe else f"Gas is {gas_val}."
                    soil_desc = "Soil moisture is low." if (snapshot.soil_moisture and (snapshot.soil_moisture.value or 0) < 25) else f"Soil moisture is {soil_val}."
                    return f"Temperature is normal at {temp_val}. {soil_desc} {gas_str} Everything is safe."
                return f"Warning: {snapshot.safety_summary}"

        if intent.intent == IntentType.CHECK_GAS:
            if is_kannada:
                return f"ಅನಿಲ ಮಟ್ಟ {gas_val} ಆಗಿದೆ. " + ("ಸುರಕ್ಷಿತವಾಗಿದೆ." if gas_safe else "ಎಚ್ಚರಿಕೆ!")
            return f"Current gas concentration is {gas_val}. " + ("The environment is clear of hazardous gas." if gas_safe else "Elevated gas detected!")

        if intent.intent == IntentType.CHECK_TEMPERATURE:
            if is_kannada:
                return f"ಪ್ರಸ್ತುತ ತಾಪಮಾನ {temp_val} ಆಗಿದೆ."
            return f"The current temperature is {temp_val}."

        if intent.intent == IntentType.CHECK_SOIL:
            if is_kannada:
                return f"ಮಣ್ಣಿನ ತೇವಾಂಶ {soil_val} ಇದೆ."
            return f"Soil moisture is at {soil_val}."

        return "I am monitoring the environment."

    def generate_approval_prompt(
        self,
        action: ActionType,
        snapshot: EnvironmentalSnapshot,
        language: str = "en",
    ) -> str:
        """Prompt user for confirmation before executing physical action."""
        is_kannada = language.lower().startswith("kn")

        if action == ActionType.WATER_PLANT:
            soil_pct = f"{snapshot.soil_moisture.value:.1f}%" if snapshot.soil_moisture and snapshot.soil_moisture.is_valid() else "unknown"
            if is_kannada:
                return f"ಗಿಡಕ್ಕೆ ನೀರು ಹಾಕಲೇ? ಮಣ್ಣಿನ ತೇವಾಂಶ {soil_pct} ಇದೆ. ದಯವಿಟ್ಟು ಬಟನ್ ಒತ್ತಿ ಅಥವಾ ಅನುಮೋದಿಸಿ."
            return f"Water the plant? Current soil moisture is {soil_pct}. Please approve using the touch button or voice."

        if action == ActionType.CLOSE_VALVE:
            if is_kannada:
                return "ವಾಲ್ವ್ ಮುಚ್ಚಲು ಅನುಮೋದಿಸುವಿರಾ?"
            return "Do you want me to close the valve? Please approve."

        return "Please confirm if you want to proceed with this action."

    def generate_action_feedback(
        self,
        result: ActionExecutionResult,
        language: str = "en",
    ) -> str:
        """Report physical action result including hardware confirmation."""
        is_kannada = language.lower().startswith("kn")

        if result.action_type == ActionType.WATER_PLANT:
            if result.verification_status == VerificationStatus.VERIFIED_SUCCESS:
                if is_kannada:
                    return "ಗಿಡಕ್ಕೆ ನೀರು ಹಾಕಲಾಗಿದೆ ಮತ್ತು ದೃಢೀಕರಿಸಲಾಗಿದೆ."
                return "Plant watered successfully. Physical action verified."
            elif result.execution_result == "aborted":
                if is_kannada:
                    return f"ಕಾರ್ಯ ರದ್ದುಗೊಂಡಿದೆ: {result.error}"
                return f"Action cancelled: {result.error}"
            else:
                if is_kannada:
                    return "ನೀರು ಹಾಕುವ ಆದೇಶ ಕಳುಹಿಸಲಾಗಿದೆ ಆದರೆ ಯಂತ್ರಾಂಶ ದೃಢೀಕರಣ ಲಭ್ಯವಿಲ್ಲ."
                return "Watering command sent, but hardware state could not be verified."

        if result.action_type == ActionType.CLOSE_VALVE:
            if result.verification_status == VerificationStatus.VERIFIED_SUCCESS:
                if is_kannada:
                    return "ವಾಲ್ವ್ ಯಶಸ್ವಿಯಾಗಿ ಮುಚ್ಚಲ್ಪಟ್ಟಿದೆ."
                return "Valve closed successfully and verified."
            return "Valve command dispatched, physical state unconfirmed."

        return f"Action {result.action_type.value} executed."

    def generate_event_explanation(self, language: str = "en") -> str:
        """Explain the most recent significant event from audit log."""
        is_kannada = language.lower().startswith("kn")
        latest = self.audit_log.get_latest_emergency_or_action()

        if not latest:
            if is_kannada:
                return "ಯಾವುದೇ ಇತ್ತೀಚಿನ ತುರ್ತು ಘಟನೆಗಳು ದಾಖಲಾಗಿಲ್ಲ."
            return "No recent critical safety events or physical actions have occurred."

        # Extract details
        ctx = latest.sensor_context or {}
        readings = ctx.get("readings", {})
        gas_info = readings.get("gas", {})
        gas_val = gas_info.get("value")

        if latest.requested_action == "close_valve" or "emergency" in latest.authorization:
            gas_str = f" of {gas_val:.1f} PPM" if gas_val else ""
            if is_kannada:
                return f"ಸುಮಾರು {latest.timestamp.split('T')[-1][:5]} ಕ್ಕೆ ಅನಿಲ ಸೋರಿಕೆ ಪತ್ತೆಯಾಗಿದೆ. ಸುರಕ್ಷತಾ ನಿಯಮದಂತೆ ವಾಲ್ವ್ ಮುಚ್ಚಲಾಗಿದೆ."
            return f"At {latest.timestamp.split('T')[-1][:5]}, elevated gas concentration{gas_str} triggered an emergency response. The valve was automatically closed, the alarm was activated, and the event was logged."

        if latest.requested_action == "water_plant":
            if is_kannada:
                return f"ಬಳಕೆದಾರರ ಕೋರಿಕೆಯಂತೆ ಗಿಡಕ್ಕೆ ನೀರು ಹಾಕಲಾಯಿತು. ಫಲಿತಾಂಶ: {latest.execution_result}."
            return f"The plant was watered following user approval. Execution result: {latest.execution_result}."

        return f"Event logged: {latest.requested_action} by {latest.user} at {latest.timestamp}."


response_generator = ResponseGenerator()
