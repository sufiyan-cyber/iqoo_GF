"""Core domain models, enumerations, and data structures for BAT POD."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SensorType(str, Enum):
    TEMPERATURE = "temperature"
    GAS = "gas"
    SOIL_MOISTURE = "soil_moisture"
    MOTION = "motion"


class SensorStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    INVALID = "INVALID"
    DISCONNECTED = "DISCONNECTED"


class SensorReading(BaseModel):
    sensor_type: SensorType
    value: Optional[float] = None
    unit: str
    status: SensorStatus = SensorStatus.OK
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_value: Optional[float] = None
    error_message: Optional[str] = None

    def is_valid(self) -> bool:
        return self.status not in (SensorStatus.INVALID, SensorStatus.DISCONNECTED) and self.value is not None


class EnvironmentalSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    temperature: Optional[SensorReading] = None
    gas: Optional[SensorReading] = None
    soil_moisture: Optional[SensorReading] = None
    is_safe: bool = True
    safety_summary: str = "Everything OK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "is_safe": self.is_safe,
            "safety_summary": self.safety_summary,
            "readings": {
                k: (v.model_dump(mode="json") if v else None)
                for k, v in {
                    "temperature": self.temperature,
                    "gas": self.gas,
                    "soil_moisture": self.soil_moisture,
                }.items()
            },
        }


class UserRole(str, Enum):
    GUEST = "guest"
    WORKER = "worker"
    ADMIN = "admin"


class UserIdentity(BaseModel):
    rfid_uid: str
    name: str
    role: UserRole = UserRole.GUEST
    is_authenticated: bool = True
    authenticated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActionType(str, Enum):
    NONE = "none"
    WATER_PLANT = "water_plant"
    CLOSE_VALVE = "close_valve"
    OPEN_VALVE = "open_valve"
    ACTIVATE_ALARM = "activate_alarm"
    DEACTIVATE_ALARM = "deactivate_alarm"


class ActionPriority(str, Enum):
    NORMAL = "normal"
    EMERGENCY = "emergency"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    BYPASSED_EMERGENCY = "bypassed_emergency"


class VerificationStatus(str, Enum):
    VERIFIED_SUCCESS = "verified_success"
    VERIFIED_FAILURE = "verified_failure"
    UNVERIFIED = "unverified"
    TIMEOUT = "timeout"


class IntentType(str, Enum):
    CHECK_SAFETY = "check_safety"
    CHECK_TEMPERATURE = "check_temperature"
    CHECK_GAS = "check_gas"
    CHECK_SOIL = "check_soil"
    WATER_PLANT = "water_plant"
    CLOSE_VALVE = "close_valve"
    EXPLAIN_EVENT = "what_happened"
    HELP = "help"
    UNKNOWN = "unknown"


class ParsedIntent(BaseModel):
    intent: IntentType
    target: Optional[str] = None
    action: ActionType = ActionType.NONE
    location: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 1.0


class DecisionCategory(str, Enum):
    INFORMATION = "INFORMATION"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    SAFETY_ALERT = "SAFETY_ALERT"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    ERROR = "ERROR"


class DecisionResult(BaseModel):
    category: DecisionCategory
    action_type: ActionType = ActionType.NONE
    action_priority: ActionPriority = ActionPriority.NORMAL
    requires_approval: bool = False
    message: str
    explanation: Optional[str] = None
    target_actuator: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ActionExecutionResult(BaseModel):
    action_id: str
    action_type: ActionType
    priority: ActionPriority
    requested_by: str
    authorized_by: Optional[str] = None
    approval_status: ApprovalStatus
    dispatched: bool
    execution_result: str  # "success", "failed", "aborted"
    verification_status: VerificationStatus
    verified_state: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditRecord(BaseModel):
    id: Optional[int] = None
    timestamp: str
    user: str
    intent: str
    sensor_context: Dict[str, Any] = Field(default_factory=dict)
    requested_action: str
    authorization: str
    execution_result: str
    verification_result: str
    error: Optional[str] = None


class DisplayState(str, Enum):
    NORMAL = "normal"
    APPROVAL = "approval"
    EMERGENCY = "emergency"
    ERROR = "error"
