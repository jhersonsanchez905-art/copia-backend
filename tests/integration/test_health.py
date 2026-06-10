"""
Integration tests for the health check endpoint.
No auth, no DB — verifies the app starts and /health responds correctly.
"""
from fastapi.testclient import TestClient

from app.main import app


def test_health_status_200():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_body_has_status_ok():
    client = TestClient(app)
    data = client.get("/health").json()
    assert data["status"] == "ok"


def test_health_body_has_project():
    client = TestClient(app)
    data = client.get("/health").json()
    assert "project" in data
    assert data["project"] != ""


def test_health_requires_no_auth():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code not in (401, 403)
