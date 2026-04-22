import os
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.deps import get_current_user
from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.main import app


def _guide_user() -> SimpleNamespace:
    return SimpleNamespace(id="guide-id", role=UserRole.GUIDE, is_active=True)


def test_guide_cannot_list_users() -> None:
    app.dependency_overrides[get_current_user] = lambda: _guide_user()
    client = TestClient(app)
    response = client.get("/api/v1/users")
    assert response.status_code == 403
    assert response.json()["code"] == ErrorCode.AUTH_FORBIDDEN
    app.dependency_overrides.clear()


def test_guide_cannot_confirm_reservation() -> None:
    app.dependency_overrides[get_current_user] = lambda: _guide_user()
    client = TestClient(app)
    response = client.post("/api/v1/reservations/660000000000000000000001/confirm", json={})
    assert response.status_code == 403
    assert response.json()["code"] == ErrorCode.AUTH_FORBIDDEN
    app.dependency_overrides.clear()


def test_guide_cannot_update_config() -> None:
    app.dependency_overrides[get_current_user] = lambda: _guide_user()
    client = TestClient(app)
    response = client.patch("/api/v1/config/reservation-rules", json={"min_days_in_advance": 5})
    assert response.status_code == 403
    assert response.json()["code"] == ErrorCode.AUTH_FORBIDDEN
    app.dependency_overrides.clear()
