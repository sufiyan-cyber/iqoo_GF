"""Human-in-the-Loop Approval Manager."""

import time
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from bat_pod.config import settings
from bat_pod.core.models import ActionType, ApprovalStatus, UserIdentity


class PendingApproval(BaseModel):
    """Encapsulates a human confirmation request."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    action: ActionType
    user: UserIdentity
    context_summary: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    timeout_sec: float = settings.APPROVAL_TIMEOUT_SEC

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout_sec


class ApprovalManager:
    """Tracks and handles approval state machine for physical actions."""

    def __init__(self) -> None:
        self._current_request: Optional[PendingApproval] = None

    def request_approval(
        self,
        action: ActionType,
        user: UserIdentity,
        context_summary: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> PendingApproval:
        """Create a new pending human approval request."""
        req = PendingApproval(
            action=action,
            user=user,
            context_summary=context_summary,
            parameters=parameters or {},
        )
        self._current_request = req
        return req

    def get_pending_request(self) -> Optional[PendingApproval]:
        """Return currently pending approval request if still valid."""
        if not self._current_request:
            return None
        if self._current_request.is_expired():
            self._current_request.status = ApprovalStatus.TIMED_OUT
            req = self._current_request
            self._current_request = None
            return None
        return self._current_request

    def approve(self) -> Optional[PendingApproval]:
        """User confirms approval via touch button or voice."""
        req = self.get_pending_request()
        if req:
            req.status = ApprovalStatus.APPROVED
            self._current_request = None
            return req
        return None

    def reject(self) -> Optional[PendingApproval]:
        """User explicitly declines approval."""
        req = self.get_pending_request()
        if req:
            req.status = ApprovalStatus.REJECTED
            self._current_request = None
            return req
        return None

    def clear(self) -> None:
        self._current_request = None


# Default global approval manager
approval_manager = ApprovalManager()
