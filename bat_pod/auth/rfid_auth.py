"""RFID authentication and Role-Based Access Control (RBAC)."""

from typing import Dict, Optional, Tuple
from bat_pod.core.models import ActionType, UserIdentity, UserRole


class RFIDAuthenticator:
    """Manages local authorized RFID cards and enforces RBAC."""

    def __init__(self) -> None:
        # Pre-configured authorized RFID tags for demo / local operation
        self._authorized_cards: Dict[str, UserIdentity] = {
            "CARD_ADMIN_001": UserIdentity(
                rfid_uid="CARD_ADMIN_001",
                name="Bruce Wayne",
                role=UserRole.ADMIN,
                is_authenticated=True,
            ),
            "CARD_WORKER_002": UserIdentity(
                rfid_uid="CARD_WORKER_002",
                name="Alfred Pennyworth",
                role=UserRole.WORKER,
                is_authenticated=True,
            ),
            "CARD_GUEST_003": UserIdentity(
                rfid_uid="CARD_GUEST_003",
                name="Visitor",
                role=UserRole.GUEST,
                is_authenticated=True,
            ),
        }
        # Currently active user session
        self._active_user: UserIdentity = UserIdentity(
            rfid_uid="ANONYMOUS",
            name="Guest User",
            role=UserRole.GUEST,
            is_authenticated=False,
        )

    def register_card(self, uid: str, name: str, role: UserRole) -> None:
        """Register a new card into local memory."""
        self._authorized_cards[uid] = UserIdentity(
            rfid_uid=uid,
            name=name,
            role=role,
            is_authenticated=True,
        )

    def authenticate_card(self, uid: str) -> Tuple[bool, UserIdentity]:
        """Authenticate card UID against local registry."""
        if uid in self._authorized_cards:
            user = self._authorized_cards[uid]
            self._active_user = user
            return True, user

        # Unknown card defaults to guest with no privileges
        guest_user = UserIdentity(
            rfid_uid=uid,
            name=f"Unknown User ({uid})",
            role=UserRole.GUEST,
            is_authenticated=False,
        )
        self._active_user = guest_user
        return False, guest_user

    def get_active_user(self) -> UserIdentity:
        """Return the current session user."""
        return self._active_user

    def check_permission(self, action: ActionType, user: Optional[UserIdentity] = None) -> Tuple[bool, str]:
        """
        Verify if the given user is authorized to perform the requested physical action.
        Matrix:
        - GUEST: View only (0 physical actions allowed)
        - WORKER: Normal actions (WATER_PLANT, DEACTIVATE_ALARM)
        - ADMIN: All actions including safety override (CLOSE_VALVE, OPEN_VALVE)
        """
        target_user = user or self._active_user

        if action == ActionType.NONE:
            return True, "No action requested."

        if target_user.role == UserRole.GUEST:
            return (
                False,
                f"Access Denied: Guest users are not permitted to trigger physical actuators ({action.value}). Please tap an authorized RFID card.",
            )

        if action in (ActionType.WATER_PLANT, ActionType.DEACTIVATE_ALARM):
            if target_user.role in (UserRole.WORKER, UserRole.ADMIN):
                return True, f"Authorized for {target_user.name} ({target_user.role.value})"
            return False, f"Unauthorized: Worker or Admin role required for {action.value}"

        if action in (ActionType.CLOSE_VALVE, ActionType.OPEN_VALVE):
            if target_user.role == UserRole.ADMIN:
                return True, f"Admin privileges verified for {target_user.name}"
            return False, f"Access Denied: Admin privileges required to manually control valve ({action.value})"

        return True, "Action permitted."


# Default global instance
auth_manager = RFIDAuthenticator()
