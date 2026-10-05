"""Unit tests for RFID authentication and RBAC authorization."""

import pytest
from bat_pod.auth.rfid_auth import RFIDAuthenticator
from bat_pod.core.models import ActionType, UserRole


@pytest.fixture
def auth_mgr():
    return RFIDAuthenticator()


def test_authenticate_admin_card(auth_mgr):
    is_auth, user = auth_mgr.authenticate_card("CARD_ADMIN_001")
    assert is_auth is True
    assert user.name == "Bruce Wayne"
    assert user.role == UserRole.ADMIN


def test_authenticate_worker_card(auth_mgr):
    is_auth, user = auth_mgr.authenticate_card("CARD_WORKER_002")
    assert is_auth is True
    assert user.name == "Alfred Pennyworth"
    assert user.role == UserRole.WORKER


def test_authenticate_unknown_card(auth_mgr):
    is_auth, user = auth_mgr.authenticate_card("UNKNOWN_HEX_999")
    assert is_auth is False
    assert user.role == UserRole.GUEST
    assert "Unknown User" in user.name


def test_guest_cannot_execute_physical_actions(auth_mgr):
    auth_mgr.authenticate_card("UNKNOWN_GUEST")
    allowed, reason = auth_mgr.check_permission(ActionType.WATER_PLANT)
    assert allowed is False
    assert "Access Denied: Guest users are not permitted" in reason


def test_worker_can_water_plant(auth_mgr):
    auth_mgr.authenticate_card("CARD_WORKER_002")
    allowed, reason = auth_mgr.check_permission(ActionType.WATER_PLANT)
    assert allowed is True
    assert "Authorized" in reason


def test_worker_cannot_control_critical_valve(auth_mgr):
    auth_mgr.authenticate_card("CARD_WORKER_002")
    allowed, reason = auth_mgr.check_permission(ActionType.CLOSE_VALVE)
    assert allowed is False
    assert "Admin privileges required" in reason


def test_admin_can_control_critical_valve(auth_mgr):
    auth_mgr.authenticate_card("CARD_ADMIN_001")
    allowed, reason = auth_mgr.check_permission(ActionType.CLOSE_VALVE)
    assert allowed is True
    assert "Admin privileges verified" in reason
