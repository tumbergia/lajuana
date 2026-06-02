import os

from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "checks" in data
    assert "mongodb" in data["checks"]


def test_health_has_checks() -> None:
    """Verify health response includes dependency checks."""
    response = client.get("/api/v1/health")
    data = response.json()
    checks = data["checks"]
    # With APP_SKIP_DB_INIT, mongodb should be not_initialized
    assert checks["mongodb"] in ("ok", "not_initialized", "error")
