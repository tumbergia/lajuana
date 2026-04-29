import os
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.business_errors import ENDPOINT_BUSINESS_CASES
from app.api.deps import get_current_user
from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.main import app

client = TestClient(app)
FAKE_ID = "660000000000000000000001"


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(id="admin-id", role=UserRole.ADMIN, is_active=True)


def _guide_user() -> SimpleNamespace:
    return SimpleNamespace(id="guide-id", role=UserRole.GUIDE, is_active=True)


PROTECTED_ENDPOINTS = [
    ("post", "/api/v1/auth/logout", None),
    ("post", "/api/v1/auth/change-password", {"current_password": "x", "new_password": "nueva123"}),
    ("get", "/api/v1/auth/me", None),
    ("post", "/api/v1/chat", {"conversation_id": "conv-test-1", "message": "hola"}),
    (
        "post",
        "/api/v1/users",
        {
            "email": "u@test.com",
            "full_name": "Usuario Test",
            "password": "Segura123",
            "role": "guide",
        },
    ),
    ("get", "/api/v1/users", None),
    ("get", f"/api/v1/users/{FAKE_ID}", None),
    ("patch", f"/api/v1/users/{FAKE_ID}", {"full_name": "Nuevo Nombre"}),
    ("delete", f"/api/v1/users/{FAKE_ID}", None),
    (
        "post",
        "/api/v1/experiences",
        {
            "name": "Cabalgata",
            "slug": "cabalgata",
            "description": "Ruta corta",
            "level": "basic",
            "duration_hours": 2,
        },
    ),
    ("get", "/api/v1/experiences", None),
    ("get", f"/api/v1/experiences/{FAKE_ID}", None),
    ("patch", f"/api/v1/experiences/{FAKE_ID}", {"name": "Cabalgata premium"}),
    ("delete", f"/api/v1/experiences/{FAKE_ID}", None),
    (
        "post",
        "/api/v1/schedules",
        {
            "experience_id": FAKE_ID,
            "date": "2026-05-20",
            "start_time": "08:00:00",
            "capacity_total": 8,
        },
    ),
    ("get", "/api/v1/schedules", None),
    ("get", f"/api/v1/schedules/{FAKE_ID}", None),
    ("patch", f"/api/v1/schedules/{FAKE_ID}", {"capacity_total": 10}),
    ("delete", f"/api/v1/schedules/{FAKE_ID}", None),
    (
        "post",
        "/api/v1/reservations",
        {"experience_id": FAKE_ID, "participant_count": 2, "channel": "whatsapp"},
    ),
    ("get", "/api/v1/reservations", None),
    ("get", f"/api/v1/reservations/{FAKE_ID}", None),
    ("patch", f"/api/v1/reservations/{FAKE_ID}", {"participant_count": 3}),
    ("post", f"/api/v1/reservations/{FAKE_ID}/confirm", {}),
    ("post", f"/api/v1/reservations/{FAKE_ID}/cancel", {}),
    (
        "post",
        f"/api/v1/reservations/{FAKE_ID}/payment-proofs",
        {
            "filename": "comprobante.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1000,
            "sha256": "abc",
            "content_base64": "SG9sYQ==",
        },
    ),
    (
        "post",
        f"/api/v1/reservations/{FAKE_ID}/participants",
        {
            "first_name": "Ana",
            "last_name": "Perez",
            "birth_date": "2000-01-01",
            "document_type": "cc",
            "document_number": "1",
            "phone": "3000000000",
            "country": "CO",
            "city": "Bogota",
            "height_cm": 165,
            "weight_kg": 60,
            "experience_level": "basic",
            "emergency_contact": {"name": "Luis", "phone": "3001111111"},
            "accepted_data_processing": True,
        },
    ),
    ("get", f"/api/v1/payment-proofs/{FAKE_ID}", None),
    ("patch", f"/api/v1/payment-proofs/{FAKE_ID}", {"status": "verified"}),
    ("get", f"/api/v1/participants/{FAKE_ID}", None),
    ("patch", f"/api/v1/participants/{FAKE_ID}", {"city": "Medellin"}),
    ("post", "/api/v1/equines", {"name": "Lucero", "weight_kg": 410}),
    ("get", "/api/v1/equines", None),
    ("get", f"/api/v1/equines/{FAKE_ID}", None),
    ("patch", f"/api/v1/equines/{FAKE_ID}", {"is_available": False}),
    ("delete", f"/api/v1/equines/{FAKE_ID}", None),
    ("post", "/api/v1/saddles", {"code": "S-001"}),
    ("get", "/api/v1/saddles", None),
    ("get", f"/api/v1/saddles/{FAKE_ID}", None),
    ("patch", f"/api/v1/saddles/{FAKE_ID}", {"name": "Silla principal"}),
    (
        "post",
        "/api/v1/assignments",
        {"reservation_id": FAKE_ID, "participant_id": FAKE_ID, "equine_id": FAKE_ID},
    ),
    ("get", f"/api/v1/assignments/{FAKE_ID}", None),
    ("patch", f"/api/v1/assignments/{FAKE_ID}", {"notes": "Ajuste de ultima hora"}),
    (
        "post",
        "/api/v1/logs",
        {"reservation_id": FAKE_ID, "event_type": "note", "happened_at": "2026-05-20T08:00:00Z"},
    ),
    ("get", f"/api/v1/logs/{FAKE_ID}", None),
    ("patch", f"/api/v1/logs/{FAKE_ID}", {"notes": "Actualizacion de bitacora"}),
    ("post", "/api/v1/providers", {"name": "Hospedaje Sierra", "provider_type": "lodging"}),
    ("get", f"/api/v1/providers/{FAKE_ID}", None),
    ("patch", f"/api/v1/providers/{FAKE_ID}", {"contact_name": "Carlos"}),
    ("delete", f"/api/v1/providers/{FAKE_ID}", None),
    ("post", "/api/v1/policies", {"reservation_id": FAKE_ID, "policy_number": "POL-001"}),
    ("get", f"/api/v1/policies/{FAKE_ID}", None),
    ("patch", f"/api/v1/policies/{FAKE_ID}", {"notes": "Revisada"}),
    ("get", "/api/v1/config/reservation-rules", None),
    ("patch", "/api/v1/config/reservation-rules", {"min_days_in_advance": 7}),
]

GUIDE_FORBIDDEN_ENDPOINTS = [
    (
        "post",
        "/api/v1/users",
        {"email": "x@y.com", "full_name": "X Y", "password": "Segura123", "role": "guide"},
    ),
    ("get", "/api/v1/users", None),
    ("post", f"/api/v1/reservations/{FAKE_ID}/confirm", {}),
    ("patch", "/api/v1/config/reservation-rules", {"min_days_in_advance": 3}),
    (
        "post",
        "/api/v1/experiences",
        {
            "name": "Ruta",
            "slug": "ruta-1",
            "description": "Desc",
            "level": "basic",
            "duration_hours": 2,
        },
    ),
    ("delete", f"/api/v1/providers/{FAKE_ID}", None),
]

VALIDATION_ENDPOINTS = [
    ("post", "/api/v1/auth/login", {}),
    ("post", "/api/v1/auth/register", {}),
    ("post", "/api/v1/chat", {}),
    ("post", "/api/v1/experiences", {}),
    ("post", "/api/v1/schedules", {}),
    ("post", "/api/v1/reservations", {}),
    ("post", f"/api/v1/reservations/{FAKE_ID}/payment-proofs", {}),
    ("post", f"/api/v1/reservations/{FAKE_ID}/participants", {}),
    ("post", "/api/v1/equines", {}),
    ("post", "/api/v1/saddles", {}),
    ("post", "/api/v1/assignments", {}),
    ("post", "/api/v1/logs", {}),
    ("post", "/api/v1/providers", {}),
    ("post", "/api/v1/policies", {}),
]


@pytest.mark.parametrize(("method", "path", "payload"), PROTECTED_ENDPOINTS)
def test_protected_endpoints_require_auth(method: str, path: str, payload: dict | None) -> None:
    response = client.request(method=method.upper(), url=path, json=payload)
    assert response.status_code == 401, path
    assert response.json()["code"] == ErrorCode.AUTH_UNAUTHORIZED


@pytest.mark.parametrize(("method", "path", "payload"), GUIDE_FORBIDDEN_ENDPOINTS)
def test_guide_forbidden_on_admin_actions(method: str, path: str, payload: dict | None) -> None:
    app.dependency_overrides[get_current_user] = lambda: _guide_user()
    response = client.request(method=method.upper(), url=path, json=payload)
    app.dependency_overrides.clear()
    assert response.status_code == 403, path
    assert response.json()["code"] == ErrorCode.AUTH_FORBIDDEN


@pytest.mark.parametrize(("method", "path", "payload"), VALIDATION_ENDPOINTS)
def test_validation_error_contract(method: str, path: str, payload: dict) -> None:
    if path.startswith("/api/v1/auth/"):
        response = client.request(method=method.upper(), url=path, json=payload)
    else:
        app.dependency_overrides[get_current_user] = lambda: _admin_user()
        response = client.request(method=method.upper(), url=path, json=payload)
        app.dependency_overrides.clear()
    assert response.status_code == 422, path
    assert response.json()["code"] == ErrorCode.VALIDATION_ERROR


def _path_template(path: str) -> str:
    path = re.sub(r"/[0-9a-f]{24}(?=/|$)", "/{id}", path)
    path = re.sub(r"/users/\{id\}", "/users/{user_id}", path)
    path = re.sub(r"/experiences/\{id\}", "/experiences/{experience_id}", path)
    path = re.sub(r"/schedules/\{id\}", "/schedules/{schedule_id}", path)
    path = re.sub(r"/reservations/\{id\}", "/reservations/{reservation_id}", path)
    path = re.sub(r"/payment-proofs/\{id\}", "/payment-proofs/{payment_proof_id}", path)
    path = re.sub(r"/participants/\{id\}", "/participants/{participant_id}", path)
    path = re.sub(r"/equines/\{id\}", "/equines/{equine_id}", path)
    path = re.sub(r"/saddles/\{id\}", "/saddles/{saddle_id}", path)
    path = re.sub(r"/assignments/\{id\}", "/assignments/{assignment_id}", path)
    path = re.sub(r"/logs/\{id\}", "/logs/{log_id}", path)
    path = re.sub(r"/providers/\{id\}", "/providers/{provider_id}", path)
    path = re.sub(r"/policies/\{id\}", "/policies/{policy_id}", path)
    return path


def test_all_protected_endpoints_have_business_matrix_entry() -> None:
    for method, path, _payload in PROTECTED_ENDPOINTS:
        key = (method.upper(), _path_template(path))
        assert key in ENDPOINT_BUSINESS_CASES, key


def test_emergency_contacts_is_public_and_returns_catalog() -> None:
    response = client.get("/api/v1/config/emergency-contacts")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    assert len(body["items"]) >= 5
    first = body["items"][0]
    assert "code" in first
    assert "name" in first
    assert "description" in first
    assert "phone_number" in first
    assert "category" in first
    assert "is_primary" in first
    assert "is_national" in first


def test_create_experience_duplicate_slug_returns_409(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_create(_: object) -> object:
        raise ApiError(
            status_code=409,
            code=ErrorCode.EXPERIENCE_SLUG_ALREADY_EXISTS,
            message="Ya existe una experiencia con ese slug.",
            details={"field": "slug"},
        )

    monkeypatch.setattr("app.api.endpoints.experiences.service.create", fake_create)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/experiences",
        json={
            "name": "Cabalgata",
            "slug": "string",
            "description": "Ruta corta",
            "level": "basic",
            "duration_hours": 2,
        },
    )
    app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["code"] == ErrorCode.EXPERIENCE_SLUG_ALREADY_EXISTS
