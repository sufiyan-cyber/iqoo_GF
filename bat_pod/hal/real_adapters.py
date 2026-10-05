"""Physical Serial/UART hardware adapters communicating with Arduino and ESP32."""

import logging
import threading
import time
from typing import Any, Dict, Optional
import serial
from bat_pod.config import settings
from bat_pod.core.interfaces import (
    IAlarmActuator,
    IDisplay,
    IGasSensor,
    IPumpActuator,
    IRFIDProvider,
    IServoActuator,
    ISoilMoistureSensor,
    ITemperatureSensor,
    ITouchButtonProvider,
)
from bat_pod.core.models import (
    DisplayState,
    SensorReading,
    SensorStatus,
    SensorType,
    VerificationStatus,
)
from bat_pod.hal.serial_protocol import SerialProtocol

logger = logging.getLogger(__name__)


class SerialDeviceManager:
    """Manages raw serial ports and background thread reading."""

    def __init__(self, port: str, baud: int = 115200, timeout: float = 1.0) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Latest received state from hardware
        self.latest_telemetry: Dict[str, Any] = {}
        self.latest_card_uid: Optional[str] = None
        self.latest_touch_pressed = False
        self.latest_servo_angle = 90
        self.latest_ack: Dict[str, Any] = {}

    def connect(self) -> bool:
        """Attempt to open serial connection to microcontroller."""
        try:
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=self.timeout)
            self.is_connected = True
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            logger.info(f"Connected to physical serial device on {self.port} at {self.baud} baud.")
            return True
        except Exception as ex:
            logger.error(f"Failed to connect to serial port {self.port}: {ex}")
            self.is_connected = False
            return False

    def disconnect(self) -> None:
        self._running = False
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        self.is_connected = False

    def send_packet(self, payload: Dict[str, Any]) -> bool:
        """Send JSON packet over UART."""
        if not self.is_connected or not self.serial_conn or not self.serial_conn.is_open:
            return False
        with self._lock:
            try:
                encoded = SerialProtocol.encode(payload)
                self.serial_conn.write(encoded)
                self.serial_conn.flush()
                return True
            except Exception as ex:
                logger.error(f"Serial write error to {self.port}: {ex}")
                self.is_connected = False
                return False

    def _read_loop(self) -> None:
        """Background thread continuously reading lines from serial."""
        while self._running and self.serial_conn and self.serial_conn.is_open:
            try:
                raw_line = self.serial_conn.readline().decode("utf-8", errors="ignore")
                if not raw_line:
                    continue
                packet = SerialProtocol.decode(raw_line)
                if not packet:
                    continue

                pkt_type = packet.get("type")
                if pkt_type == "telemetry":
                    self.latest_telemetry = packet
                    if packet.get("rfid"):
                        self.latest_card_uid = packet["rfid"]
                    if packet.get("touch") == 1:
                        self.latest_touch_pressed = True
                    if "servo_angle" in packet:
                        self.latest_servo_angle = packet["servo_angle"]
                elif pkt_type == "ack":
                    self.latest_ack = packet

            except Exception as ex:
                logger.error(f"Error reading from serial port {self.port}: {ex}")
                time.sleep(0.5)


class RealTemperatureSensor(ITemperatureSensor):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager

    def read(self) -> SensorReading:
        if not self.mgr.is_connected:
            return SensorReading(
                sensor_type=SensorType.TEMPERATURE,
                value=None,
                unit="°C",
                status=SensorStatus.DISCONNECTED,
                error_message="Microcontroller serial disconnected",
            )
        val = self.mgr.latest_telemetry.get("temp")
        if val is None:
            return SensorReading(
                sensor_type=SensorType.TEMPERATURE,
                value=None,
                unit="°C",
                status=SensorStatus.INVALID,
                error_message="No reading reported by sensor hub",
            )
        return SensorReading(
            sensor_type=SensorType.TEMPERATURE,
            value=float(val),
            unit="°C",
            status=SensorStatus.OK,
        )

    def get_type(self) -> SensorType:
        return SensorType.TEMPERATURE

    def is_healthy(self) -> bool:
        return self.mgr.is_connected and "temp" in self.mgr.latest_telemetry


class RealGasSensor(IGasSensor):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager

    def read(self) -> SensorReading:
        if not self.mgr.is_connected:
            return SensorReading(
                sensor_type=SensorType.GAS,
                value=None,
                unit="PPM",
                status=SensorStatus.DISCONNECTED,
                error_message="Gas sensor microcontroller disconnected",
            )
        val = self.mgr.latest_telemetry.get("gas")
        if val is None:
            return SensorReading(
                sensor_type=SensorType.GAS,
                value=None,
                unit="PPM",
                status=SensorStatus.INVALID,
                error_message="Gas sensor returned null",
            )
        return SensorReading(
            sensor_type=SensorType.GAS,
            value=float(val),
            unit="PPM",
            status=SensorStatus.OK,
        )

    def get_type(self) -> SensorType:
        return SensorType.GAS

    def is_healthy(self) -> bool:
        return self.mgr.is_connected and "gas" in self.mgr.latest_telemetry


class RealSoilMoistureSensor(ISoilMoistureSensor):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager

    def read(self) -> SensorReading:
        if not self.mgr.is_connected:
            return SensorReading(
                sensor_type=SensorType.SOIL_MOISTURE,
                value=None,
                unit="%",
                status=SensorStatus.DISCONNECTED,
                error_message="Sensor hub disconnected",
            )
        val = self.mgr.latest_telemetry.get("soil")
        if val is None:
            return SensorReading(
                sensor_type=SensorType.SOIL_MOISTURE,
                value=None,
                unit="%",
                status=SensorStatus.INVALID,
                error_message="Soil sensor reading unavailable",
            )
        return SensorReading(
            sensor_type=SensorType.SOIL_MOISTURE,
            value=float(val),
            unit="%",
            status=SensorStatus.OK,
        )

    def get_type(self) -> SensorType:
        return SensorType.SOIL_MOISTURE

    def is_healthy(self) -> bool:
        return self.mgr.is_connected and "soil" in self.mgr.latest_telemetry


class RealServoActuator(IServoActuator):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager

    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        params = parameters or {}
        angle = params.get("angle", 0)
        pkt = SerialProtocol.create_command("servo", "SET_SERVO", angle=angle)
        return self.mgr.send_packet(pkt)

    def verify(self, expected_state: str, timeout_sec: float = 2.0) -> VerificationStatus:
        start = time.time()
        while time.time() - start < timeout_sec:
            current = f"{self.mgr.latest_servo_angle}_DEG"
            if current == expected_state:
                return VerificationStatus.VERIFIED_SUCCESS
            time.sleep(0.1)
        return VerificationStatus.TIMEOUT

    def get_state(self) -> str:
        return f"{self.mgr.latest_servo_angle}_DEG"

    def emergency_safe_state(self) -> bool:
        pkt = SerialProtocol.create_command("servo", "SET_SERVO", angle=0)
        return self.mgr.send_packet(pkt)


class RealPumpActuator(IPumpActuator):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager
        self._state = "STOPPED"

    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        state = 1 if command == "START" else 0
        self._state = "RUNNING" if state == 1 else "STOPPED"
        pkt = SerialProtocol.create_command("pump", "SET_PUMP", state=state)
        return self.mgr.send_packet(pkt)

    def verify(self, expected_state: str, timeout_sec: float = 2.0) -> VerificationStatus:
        return VerificationStatus.VERIFIED_SUCCESS if self._state == expected_state else VerificationStatus.VERIFIED_FAILURE

    def get_state(self) -> str:
        return self._state

    def emergency_safe_state(self) -> bool:
        return self.execute("STOP")


class RealAlarmActuator(IAlarmActuator):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager
        self._state = "OFF"

    def execute(self, command: str, parameters: Optional[Dict[str, Any]] = None) -> bool:
        state = 1 if command == "ALARM_ON" else 0
        self._state = "ON" if state == 1 else "OFF"
        pkt = SerialProtocol.create_command("alarm", "SET_ALARM", state=state)
        return self.mgr.send_packet(pkt)

    def verify(self, expected_state: str, timeout_sec: float = 2.0) -> VerificationStatus:
        return VerificationStatus.VERIFIED_SUCCESS if self._state == expected_state else VerificationStatus.VERIFIED_FAILURE

    def get_state(self) -> str:
        return self._state

    def emergency_safe_state(self) -> bool:
        return self.execute("ALARM_OFF")


class RealRFIDProvider(IRFIDProvider):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager

    def poll_card(self) -> Optional[str]:
        uid = self.mgr.latest_card_uid
        self.mgr.latest_card_uid = None
        return uid


class RealTouchButton(ITouchButtonProvider):
    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager

    def is_pressed(self) -> bool:
        pressed = self.mgr.latest_touch_pressed
        self.mgr.latest_touch_pressed = False
        return pressed

    def wait_for_press(self, timeout_sec: float = 30.0) -> bool:
        start = time.time()
        while time.time() - start < timeout_sec:
            if self.mgr.latest_touch_pressed:
                self.mgr.latest_touch_pressed = False
                return True
            time.sleep(0.05)
        return False


class RealDisplay(IDisplay):
    """Sends display frame packets to the ESP32 OLED display."""

    def __init__(self, manager: SerialDeviceManager) -> None:
        self.mgr = manager

    def show_screen(self, state: DisplayState, context: Dict[str, Any]) -> None:
        pkt = {
            "type": "display",
            "state": state.value,
            "context": context,
        }
        self.mgr.send_packet(pkt)
