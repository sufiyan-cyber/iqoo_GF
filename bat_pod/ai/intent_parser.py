"""Intent extraction converting natural-language utterances into structured intents."""

import json
import logging
import re
from typing import Optional
import requests
from bat_pod.config import settings
from bat_pod.core.models import ActionType, IntentType, ParsedIntent

logger = logging.getLogger(__name__)


class IntentParser:
    """Parses natural-language user commands into structured intents with fail-safe fallback."""

    def __init__(self) -> None:
        self.backend = settings.AI_BACKEND
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model = settings.OLLAMA_MODEL

    def parse(self, text: str) -> ParsedIntent:
        """Parse natural language query using chosen backend with guaranteed safe fallback."""
        cleaned = text.strip()
        if not cleaned:
            return ParsedIntent(intent=IntentType.UNKNOWN, raw_text="")

        # If LLM backend is configured, attempt LLM parsing
        if self.backend == "ollama":
            llm_result = self._parse_with_ollama(cleaned)
            if llm_result:
                return llm_result
            logger.info("Ollama parsing unavailable or failed; falling back to deterministic parser.")

        # Deterministic offline-first regex/rule parser
        return self._parse_deterministic(cleaned)

    def _parse_deterministic(self, text: str) -> ParsedIntent:
        """Deterministic keyword and pattern matching for 100% offline accuracy."""
        lower = text.lower()

        # What happened / Explain event
        if any(p in lower for p in ["what happened", "why did you close", "explain event", "what occurred", "ಏನಾಯಿತು"]):
            return ParsedIntent(
                intent=IntentType.EXPLAIN_EVENT,
                raw_text=text,
                confidence=1.0,
            )

        # Environmental Safety checks
        if any(p in lower for p in ["is the environment safe", "environment safe", "is it safe", "is everything safe", "check safety", "ಸುರಕ್ಷಿತವಾಗಿದೆಯೇ"]):
            return ParsedIntent(
                intent=IntentType.CHECK_SAFETY,
                raw_text=text,
                confidence=1.0,
            )

        # Gas queries
        if any(p in lower for p in ["gas leak", "is there gas", "gas level", "check gas", "ಅನಿಲ ಸೋರಿಕೆ"]):
            return ParsedIntent(
                intent=IntentType.CHECK_GAS,
                target="gas_sensor",
                raw_text=text,
                confidence=1.0,
            )

        # Temperature queries
        if any(p in lower for p in ["temperature normal", "is it hot", "check temp", "what is the temperature", "ತಾಪಮಾನ"]):
            return ParsedIntent(
                intent=IntentType.CHECK_TEMPERATURE,
                target="temperature_sensor",
                raw_text=text,
                confidence=1.0,
            )

        # Soil moisture queries
        if any(p in lower for p in ["plant need water", "soil dry", "soil moisture", "check plant", "ಗಿಡಕ್ಕೆ ನೀರು"]):
            return ParsedIntent(
                intent=IntentType.CHECK_SOIL,
                target="soil_moisture_sensor",
                raw_text=text,
                confidence=1.0,
            )

        # Water plant command (Action)
        if any(p in lower for p in ["water the plant", "water plant", "turn on water", "irrigate", "ಗಿಡಕ್ಕೆ ನೀರು ಹಾಕು"]):
            return ParsedIntent(
                intent=IntentType.WATER_PLANT,
                target="plant_01",
                action=ActionType.WATER_PLANT,
                raw_text=text,
                confidence=1.0,
            )

        # Close valve command (Action)
        if any(p in lower for p in ["close the valve", "close valve", "shut off valve", "ವಾಲ್ವ್ ಮುಚ್ಚು"]):
            return ParsedIntent(
                intent=IntentType.CLOSE_VALVE,
                target="gas_valve",
                action=ActionType.CLOSE_VALVE,
                raw_text=text,
                confidence=1.0,
            )

        # Help
        if any(p in lower for p in ["help", "what can you do", "commands"]):
            return ParsedIntent(
                intent=IntentType.HELP,
                raw_text=text,
                confidence=1.0,
            )

        return ParsedIntent(
            intent=IntentType.UNKNOWN,
            raw_text=text,
            confidence=0.0,
        )

    def _parse_with_ollama(self, text: str) -> Optional[ParsedIntent]:
        """Call local Ollama service for intent extraction."""
        system_prompt = (
            "You are an intent parser for the physical AI companion BAT POD. "
            "Output ONLY valid JSON without markdown formatting. Valid intents: "
            "check_safety, check_temperature, check_gas, check_soil, water_plant, close_valve, what_happened, help, unknown. "
            "JSON structure: {\"intent\": \"<intent>\", \"action\": \"none\"|\"water_plant\"|\"close_valve\"}"
        )
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\nUser utterance: \"{text}\"",
            "stream": False,
            "format": "json",
        }

        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                raw_response = data.get("response", "")
                parsed = json.loads(raw_response)
                intent_str = parsed.get("intent", "").lower()
                action_str = parsed.get("action", "none").lower()

                # Validate intent against enum
                intent_enum = IntentType.UNKNOWN
                for it in IntentType:
                    if it.value == intent_str:
                        intent_enum = it
                        break

                action_enum = ActionType.NONE
                for at in ActionType:
                    if at.value == action_str:
                        action_enum = at
                        break

                return ParsedIntent(
                    intent=intent_enum,
                    action=action_enum,
                    raw_text=text,
                    confidence=0.9,
                )
        except Exception as ex:
            logger.debug(f"Ollama call failed: {ex}")

        return None


intent_parser = IntentParser()
