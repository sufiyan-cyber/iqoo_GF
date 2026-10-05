"""Master BAT POD Controller orchestrating the SENSE -> UNDERSTAND -> DECIDE -> ACT -> CONFIRM loop."""

import logging
import time
from typing import Any, Dict, Optional
from bat_pod.action.action_manager import ActionManager, action_manager
from bat_pod.ai.context_retriever import SensorContextRetriever, context_retriever
from bat_pod.ai.intent_parser import IntentParser, intent_parser
from bat_pod.ai.response_generator import ResponseGenerator, response_generator
from bat_pod.ai.voice_pipeline import VoicePipeline, voice_pipeline
from bat_pod.audit.audit_logger import AuditLogger, audit_logger
from bat_pod.auth.approval_manager import ApprovalManager, approval_manager
from bat_pod.auth.rfid_auth import RFIDAuthenticator, auth_manager
from bat_pod.core.interfaces import (
    IAlarmActuator,
    IAudioInput,
    IAudioOutput,
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
    ActionExecutionResult,
    ActionPriority,
    ActionType,
    ApprovalStatus,
    EnvironmentalSnapshot,
    IntentType,
    ParsedIntent,
    SensorReading,
    UserIdentity,
    UserRole,
    VerificationStatus,
)
from bat_pod.display.display_controller import DisplayController
from bat_pod.safety.policy_engine import SafetyPolicyEngine, safety_policy_engine

logger = logging.getLogger(__name__)


class BatPodController:
    """Central Controller implementing the end-to-end BAT POD MVP product loop."""

    def __init__(
        self,
        temp_sensor: ITemperatureSensor,
        gas_sensor: IGasSensor,
        soil_sensor: ISoilMoistureSensor,
        servo: IServoActuator,
        pump: Optional[IPumpActuator] = None,
        alarm: Optional[IAlarmActuator] = None,
        rfid: Optional[IRFIDProvider] = None,
        touch: Optional[ITouchButtonProvider] = None,
        display: Optional[IDisplay] = None,
        audio_in: Optional[IAudioInput] = None,
        audio_out: Optional[IAudioOutput] = None,
        audit: Optional[AuditLogger] = None,
        safety: Optional[SafetyPolicyEngine] = None,
        auth: Optional[RFIDAuthenticator] = None,
        approval: Optional[ApprovalManager] = None,
    ) -> None:
        self.temp_sensor = temp_sensor
        self.gas_sensor = gas_sensor
        self.soil_sensor = soil_sensor

        self.servo = servo
        self.pump = pump
        self.alarm = alarm

        self.rfid = rfid
        self.touch = touch
        self.display_ctrl = DisplayController(display)
        self.audio_in = audio_in
        self.audio_out = audio_out

        self.audit = audit or audit_logger
        self.safety = safety or safety_policy_engine
        self.auth = auth or auth_manager
        self.approval = approval or approval_manager

        self.action_mgr = ActionManager(
            servo=self.servo,
            pump=self.pump,
            alarm=self.alarm,
            audit_log=self.audit,
            safety_engine=self.safety,
            auth=self.auth,
        )

        self.context_retriever = context_retriever
        self.intent_parser = intent_parser
        self.response_generator = ResponseGenerator(self.audit)
        self.voice_pipe = voice_pipeline

        # Current runtime snapshot
        self.current_snapshot = EnvironmentalSnapshot()
        self._emergency_active = False

    def sense(self) -> EnvironmentalSnapshot:
        """SENSE: Poll all connected sensors and RFID reader."""
        # 1. Read environmental sensors
        temp_r = self.temp_sensor.read()
        gas_r = self.gas_sensor.read()
        soil_r = self.soil_sensor.read()

        snapshot = EnvironmentalSnapshot(
            temperature=temp_r,
            gas=gas_r,
            soil_moisture=soil_r,
        )

        # 2. Check for RFID card presentation
        if self.rfid:
            card_uid = self.rfid.poll_card()
            if card_uid:
                is_auth, user = self.auth.authenticate_card(card_uid)
                msg = f"User recognized: {user.name} ({user.role.value})" if is_auth else f"Unknown RFID card: {card_uid}"
                logger.info(f"[AUTH] {msg}")
                self._speak(f"Hello {user.name}." if is_auth else "Card not recognized.")

        # 3. Deterministic Safety Evaluation
        evaluation = self.safety.evaluate_environment(snapshot)
        snapshot.is_safe = evaluation.is_safe
        snapshot.safety_summary = evaluation.summary
        self.current_snapshot = snapshot

        # 4. Emergency auto-intervention check
        if evaluation.is_emergency and not self._emergency_active:
            self._emergency_active = True
            logger.critical(f"EMERGENCY TRIGGERED: {evaluation.hazard_detected}")
            # Act: trigger emergency valve close & activate alarm
            res = self.action_mgr.trigger_emergency(
                action=evaluation.emergency_action,
                reason=evaluation.summary,
                context=snapshot.to_dict(),
            )
            if self.alarm:
                self.alarm.execute("ALARM_ON")

            # Display emergency screen
            self.display_ctrl.show_emergency(
                hazard=evaluation.hazard_detected or "HAZARD",
                action_taken="Closing valve & Alarm ON",
            )
            # Voice notification
            self._speak(f"Warning! {evaluation.hazard_detected} detected. Closing valve.")
        elif not evaluation.is_emergency:
            if self._emergency_active:
                if self.alarm:
                    self.alarm.execute("ALARM_OFF")
            self._emergency_active = False
            self.display_ctrl.show_normal(snapshot)

        return snapshot

    def process_utterance(self, text: str, language: str = "en") -> str:
        """
        UNDERSTAND -> DECIDE -> ACT -> CONFIRM for a user voice command.
        """
        # Ensure latest sensor data is available
        snapshot = self.sense()
        active_user = self.auth.get_active_user()

        # UNDERSTAND: Parse intent
        intent = self.intent_parser.parse(text)
        logger.info(f"Parsed intent: {intent.intent.value} from \"{text}\"")

        # DECIDE: Route based on intent
        if intent.intent in (
            IntentType.CHECK_SAFETY,
            IntentType.CHECK_GAS,
            IntentType.CHECK_TEMPERATURE,
            IntentType.CHECK_SOIL,
        ):
            # Pure informational sensor query
            response_text = self.response_generator.generate_sensor_response(intent, snapshot, language)
            self._speak(response_text, language)
            return response_text

        if intent.intent == IntentType.EXPLAIN_EVENT:
            # Query audit history to explain what happened
            explanation = self.response_generator.generate_event_explanation(language)
            self._speak(explanation, language)
            return explanation

        if intent.intent in (IntentType.WATER_PLANT, IntentType.CLOSE_VALVE):
            # Physical action requested: Check RBAC first!
            target_action = intent.action
            is_permitted, perm_msg = self.auth.check_permission(target_action, active_user)
            if not is_permitted:
                self._speak(perm_msg, language)
                return perm_msg

            # Check safety rules for this action
            is_safe, safety_msg = self.safety.authorize_action_safety(target_action, snapshot)
            if not is_safe:
                self._speak(safety_msg, language)
                return safety_msg

            # Human-in-the-loop: Request approval
            soil_pct = f"{snapshot.soil_moisture.value:.1f}%" if snapshot.soil_moisture and snapshot.soil_moisture.is_valid() else "N/A"
            req = self.approval.request_approval(
                action=target_action,
                user=active_user,
                context_summary=f"Soil: {soil_pct}",
            )

            # Update display to Approval screen
            self.display_ctrl.show_approval(
                action_name=f"{target_action.value.replace('_', ' ').title()}?",
                detail=f"Soil: {soil_pct}",
            )

            prompt = self.response_generator.generate_approval_prompt(target_action, snapshot, language)
            self._speak(prompt, language)
            return prompt

        if intent.intent == IntentType.HELP:
            help_msg = "You can ask: 'Is the environment safe?', 'Water the plant', or 'What happened?'."
            self._speak(help_msg, language)
            return help_msg

        fallback = "I didn't understand that request. You can ask if the environment is safe or tell me to water the plant."
        self._speak(fallback, language)
        return fallback

    def handle_user_approval(self, approved: bool, language: str = "en") -> Optional[ActionExecutionResult]:
        """User confirms or rejects a pending physical action via touch button or voice."""
        req = self.approval.get_pending_request()
        if not req:
            logger.info("No action pending approval.")
            return None

        if not approved:
            self.approval.reject()
            res = ActionExecutionResult(
                action_id=req.request_id,
                action_type=req.action,
                priority=ActionPriority.NORMAL,
                requested_by=req.user.name,
                approval_status=ApprovalStatus.REJECTED,
                dispatched=False,
                execution_result="aborted",
                verification_status=VerificationStatus.UNVERIFIED,
                error="User declined approval",
            )
            feedback = self.response_generator.generate_action_feedback(res, language)
            self._speak(feedback, language)
            self.display_ctrl.show_normal(self.current_snapshot)
            return res

        # User approved!
        self.approval.approve()

        # ACT: Execute through ActionManager
        result = self.action_mgr.execute_action(
            action=req.action,
            priority=ActionPriority.NORMAL,
            requested_by=req.user,
            approval_status=ApprovalStatus.APPROVED,
            context=self.current_snapshot.to_dict(),
        )

        # CONFIRM: Report verification status back to user
        feedback = self.response_generator.generate_action_feedback(result, language)
        self._speak(feedback, language)

        # Return display to normal
        self.display_ctrl.show_normal(self.current_snapshot)
        return result

    def _speak(self, text: str, language: str = "en") -> None:
        """Speak out text via attached audio output and voice pipeline."""
        if self.audio_out:
            self.audio_out.speak(text, language)
        self.voice_pipe.text_to_speech(text, language)
