"""FastAPI Web API serving the Organic/Natural BAT POD Web UI and telemetry endpoints."""

from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bat_pod.audit.audit_logger import audit_logger
from bat_pod.config import settings
from bat_pod.core.models import ActionType, ApprovalStatus, DisplayState, UserRole
from bat_pod.hal.mock_adapters import (
    MockAlarmActuator,
    MockAudioInput,
    MockAudioOutput,
    MockDisplay,
    MockGasSensor,
    MockPumpActuator,
    MockRFIDProvider,
    MockServoActuator,
    MockSoilMoistureSensor,
    MockTemperatureSensor,
    MockTouchButton,
)
from bat_pod.orchestrator.pod_controller import BatPodController


def create_app(controller: Optional[BatPodController] = None, mocks: Optional[Dict[str, Any]] = None) -> FastAPI:
    """Create FastAPI application bound to the BatPodController."""
    app = FastAPI(title="BAT POD — Physical AI Companion API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # If controller not passed in, initialize default mock controller
    if controller is None:
        temp_s = MockTemperatureSensor(initial_c=26.0)
        gas_s = MockGasSensor(initial_ppm=42.0)
        soil_s = MockSoilMoistureSensor(initial_pct=21.0)
        servo = MockServoActuator(initial_angle=90)
        pump = MockPumpActuator()
        alarm = MockAlarmActuator()
        rfid = MockRFIDProvider()
        touch = MockTouchButton()
        display = MockDisplay()
        audio_out = MockAudioOutput()

        controller = BatPodController(
            temp_sensor=temp_s,
            gas_sensor=gas_s,
            soil_sensor=soil_s,
            servo=servo,
            pump=pump,
            alarm=alarm,
            rfid=rfid,
            touch=touch,
            display=display,
            audio_out=audio_out,
            audit=audit_logger,
        )
        mocks = {
            "temp": temp_s,
            "gas": gas_s,
            "soil": soil_s,
            "servo": servo,
            "pump": pump,
            "alarm": alarm,
            "rfid": rfid,
            "touch": touch,
            "display": display,
            "audio_out": audio_out,
        }

    web_dir = Path(__file__).resolve().parent.parent / "web"

    # API Models
    class UtteranceRequest(BaseModel):
        text: str
        language: str = "en"

    class TapRequest(BaseModel):
        card_id: str

    class ApprovalRequest(BaseModel):
        approved: bool
        language: str = "en"

    class SensorUpdateRequest(BaseModel):
        sensor_type: str  # gas, temp, soil
        value: float

    @app.get("/api/status")
    def get_status():
        """Retrieve latest environmental telemetry, device state, and active user."""
        snap = controller.sense()
        user = controller.auth.get_active_user()
        pending = controller.approval.get_pending_request()

        servo_state = controller.servo.get_state() if controller.servo else "UNKNOWN"
        pump_state = controller.pump.get_state() if controller.pump else "STOPPED"
        alarm_state = controller.alarm.get_state() if controller.alarm else "OFF"
        display_text = mocks["display"].current_screen_text if mocks and "display" in mocks else ""
        display_state = mocks["display"].current_state.value if mocks and "display" in mocks else "normal"

        return {
            "snapshot": snap.model_dump(mode="json"),
            "user": user.model_dump(mode="json"),
            "actuators": {
                "servo": servo_state,
                "pump": pump_state,
                "alarm": alarm_state,
            },
            "display": {
                "state": display_state,
                "screen_text": display_text,
            },
            "pending_approval": pending.model_dump(mode="json") if pending else None,
        }

    @app.post("/api/say")
    def say_phrase(req: UtteranceRequest):
        """Send a natural-language voice utterance to BAT POD."""
        resp = controller.process_utterance(req.text, req.language)
        return {"response": resp, "display_state": mocks["display"].current_state.value if mocks else "normal"}

    @app.post("/api/tap")
    def tap_card(req: TapRequest):
        """Simulate tapping an RFID Card."""
        if mocks and "rfid" in mocks:
            mocks["rfid"].tap_card(req.card_id)
            controller.sense()
            user = controller.auth.get_active_user()
            return {"status": "ok", "user": user.model_dump(mode="json")}
        return {"status": "error", "message": "RFID simulation only available in mock mode"}

    @app.post("/api/approve")
    def approve_action(req: ApprovalRequest):
        """User confirms or rejects a pending human-in-the-loop action."""
        res = controller.handle_user_approval(approved=req.approved, language=req.language)
        if res:
            return {"status": "ok", "result": res.model_dump(mode="json")}
        return {"status": "no_pending_action", "result": None}

    @app.post("/api/sensor/set")
    def update_sensor(req: SensorUpdateRequest):
        """Manually inject simulated sensor value."""
        if not mocks:
            raise HTTPException(status_code=400, detail="Sensors cannot be overridden in hardware mode")

        if req.sensor_type == "gas" and "gas" in mocks:
            mocks["gas"].set_value(req.value)
        elif req.sensor_type == "temp" and "temp" in mocks:
            mocks["temp"].set_value(req.value)
        elif req.sensor_type == "soil" and "soil" in mocks:
            mocks["soil"].set_value(req.value)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown sensor type: {req.sensor_type}")

        snap = controller.sense()
        return {"status": "ok", "snapshot": snap.model_dump(mode="json")}

    @app.get("/api/audit")
    def get_audit_records(limit: int = 10):
        """Retrieve recent SQLite audit logs."""
        records = audit_logger.get_recent(limit=limit)
        return [r.model_dump(mode="json") for r in records]

    # Serve Web UI
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

        @app.get("/", response_class=HTMLResponse)
        def serve_index():
            index_path = web_dir / "index.html"
            if index_path.exists():
                return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
            return HTMLResponse(content="<h1>BAT POD Web UI not found</h1>")

    return app
