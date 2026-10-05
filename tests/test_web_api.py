"""Unit and integration tests for FastAPI Web Companion API."""

import pytest
from fastapi.testclient import TestClient
from bat_pod.web_api import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_get_status_endpoint(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "snapshot" in data
    assert "user" in data
    assert "actuators" in data
    assert data["snapshot"]["temperature"]["value"] == 26.0


def test_post_say_endpoint(client):
    res = client.post("/api/say", json={"text": "Is the environment safe?"})
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert "26.0" in data["response"]


def test_post_tap_rfid(client):
    res = client.post("/api/tap", json={"card_id": "CARD_ADMIN_001"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["user"]["name"] == "Bruce Wayne"


def test_sensor_set_endpoint(client):
    res = client.post("/api/sensor/set", json={"sensor_type": "gas", "value": 350.0})
    assert res.status_code == 200
    data = res.json()
    assert data["snapshot"]["gas"]["value"] == 350.0
    assert data["snapshot"]["is_safe"] is False


def test_audit_logs_endpoint(client):
    res = client.get("/api/audit?limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_serve_index_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "BAT POD" in res.text
    assert "Fraunces" in res.text
    assert "bg-grain" in res.text
