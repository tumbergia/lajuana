from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.common.enums import UserRole
from app.main import app


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(id="admin-id", role=UserRole.ADMIN, is_active=True)


def test_ask_is_blocked_when_ai_globally_disabled(monkeypatch) -> None:
    async def blocked(*_args, **_kwargs) -> SimpleNamespace:
        return SimpleNamespace(allowed=False, reason="global_disabled")

    monkeypatch.setattr(
        "app.api.endpoints.ask.AssistantGate.evaluate",
        blocked,
    )
    monkeypatch.setattr(
        "app.api.endpoints.ask.AssistantOrchestrator",
        lambda: (_ for _ in ()).throw(AssertionError("orchestrator should not run")),
    )

    client = TestClient(app)
    response = client.post("/api/v1/ask", json={"message": "hola"})

    assert response.status_code == 409
    assert response.json() == {
        "code": "assistant.disabled",
        "message": "El asistente está deshabilitado globalmente.",
        "details": None,
    }


def test_admin_ask_is_blocked_when_ai_globally_disabled(monkeypatch) -> None:
    app.dependency_overrides[get_current_user] = lambda: _admin_user()

    async def blocked(*_args, **_kwargs) -> SimpleNamespace:
        return SimpleNamespace(allowed=False, reason="global_disabled")

    monkeypatch.setattr(
        "app.api.endpoints.admin_ask.AssistantGate.evaluate",
        blocked,
    )
    monkeypatch.setattr(
        "app.api.endpoints.admin_ask.AssistantOrchestrator",
        lambda: (_ for _ in ()).throw(AssertionError("orchestrator should not run")),
    )

    client = TestClient(app)
    response = client.post("/api/v1/admin/ask", json={"message": "hola"})

    assert response.status_code == 409
    assert response.json() == {
        "code": "assistant.disabled",
        "message": "El asistente está deshabilitado globalmente.",
        "details": None,
    }
    app.dependency_overrides.clear()
