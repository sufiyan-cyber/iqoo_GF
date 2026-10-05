"""Serial communication protocol framing and parsing between microcontrollers and host."""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SerialProtocol:
    """Encodes and decodes JSON-based delimited packets for UART transmission."""

    DELIMITER = "\n"

    @classmethod
    def encode(cls, payload: Dict[str, Any]) -> bytes:
        """Encode dictionary payload into newline-delimited bytes."""
        serialized = json.dumps(payload, separators=(",", ":")) + cls.DELIMITER
        return serialized.encode("utf-8")

    @classmethod
    def decode(cls, raw_line: str) -> Optional[Dict[str, Any]]:
        """Decode and validate incoming JSON line."""
        cleaned = raw_line.strip()
        if not cleaned:
            return None
        try:
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                logger.warning(f"Received malformed non-dict packet: {cleaned}")
                return None
            return data
        except json.JSONDecodeError as ex:
            logger.warning(f"JSON decode failed for line '{cleaned}': {ex}")
            return None

    @classmethod
    def create_command(cls, target: str, command: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate structured actuator command."""
        return {
            "type": "command",
            "target": target,
            "cmd": command,
            **kwargs,
        }

    @classmethod
    def create_telemetry_packet(
        cls,
        temp: Optional[float],
        gas: Optional[float],
        soil: Optional[float],
        servo_angle: int,
        rfid_uid: Optional[str] = None,
        touch_pressed: bool = False,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Construct sensor hub telemetry packet."""
        return {
            "type": "telemetry",
            "temp": temp,
            "gas": gas,
            "soil": soil,
            "servo_angle": servo_angle,
            "rfid": rfid_uid,
            "touch": 1 if touch_pressed else 0,
            "error": error,
        }
