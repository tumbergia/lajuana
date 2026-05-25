import os
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.deps import get_current_user
from app.common.enums import PaymentStatus, UserRole
from app.common.labels import ErrorCode
from app.main import app

client = TestClient(app)


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(id="660000000000000000000001", role=UserRole.ADMIN, is_active=True)


def _guide_user() -> SimpleNamespace:
    return SimpleNamespace(id="660000000000000000000002", role=UserRole.GUIDE, is_active=True)


def _proof_doc(status: PaymentStatus) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id="660000000000000000000501",
        reservation_id="660000000000000000000001",
        storage_key="payment_proof/proof.pdf",
        filename="proof.pdf",
        content_type="application/pdf",
        size_bytes=100,
        sha256="abc",
        status=status,
        uploaded_at=now,
        created_at=now,
        updated_at=now,
        deleted_at=None,
        version=1,
    )


def test_verify_payment_proof_endpoint_returns_verified_status(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_verify(payment_proof_id, payload, *, actor_id, actor_role):
        captured["payment_proof_id"] = payment_proof_id
        captured["token"] = payload.confirmation_token
        captured["actor_id"] = str(actor_id)
        captured["actor_role"] = actor_role
        return _proof_doc(PaymentStatus.VERIFIED)

    monkeypatch.setattr("app.api.endpoints.payment_proofs.service.verify_payment", fake_verify)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/verify",
        json={"confirmation_token": "VERIFY_PAYMENT"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "verified"
    assert captured == {
        "payment_proof_id": "660000000000000000000501",
        "token": "VERIFY_PAYMENT",
        "actor_id": "660000000000000000000001",
        "actor_role": UserRole.ADMIN,
    }


def test_reject_payment_proof_endpoint_returns_rejected_status(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_reject(payment_proof_id, payload, *, actor_id, actor_role):
        captured["payment_proof_id"] = payment_proof_id
        captured["token"] = payload.confirmation_token
        captured["actor_id"] = str(actor_id)
        captured["actor_role"] = actor_role
        return _proof_doc(PaymentStatus.REJECTED)

    monkeypatch.setattr("app.api.endpoints.payment_proofs.service.reject_payment", fake_reject)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/reject",
        json={"confirmation_token": "REJECT_PAYMENT", "note": "Datos invalidos"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert captured == {
        "payment_proof_id": "660000000000000000000501",
        "token": "REJECT_PAYMENT",
        "actor_id": "660000000000000000000001",
        "actor_role": UserRole.ADMIN,
    }


def test_approve_payment_proof_endpoint_returns_verified_status(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_approve(payment_proof_id, payload, *, actor_id, actor_role):
        captured["payment_proof_id"] = payment_proof_id
        captured["token"] = payload.confirmation_token
        captured["actor_id"] = str(actor_id)
        captured["actor_role"] = actor_role
        return _proof_doc(PaymentStatus.VERIFIED)

    monkeypatch.setattr("app.api.endpoints.payment_proofs.service.approve_payment", fake_approve)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/approve",
        json={"confirmation_token": "APPROVE_PAYMENT"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "verified"
    assert captured == {
        "payment_proof_id": "660000000000000000000501",
        "token": "APPROVE_PAYMENT",
        "actor_id": "660000000000000000000001",
        "actor_role": UserRole.ADMIN,
    }


def test_guide_cannot_verify_or_reject_payment_proof() -> None:
    app.dependency_overrides[get_current_user] = lambda: _guide_user()
    verify_response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/verify",
        json={"confirmation_token": "VERIFY_PAYMENT"},
    )
    reject_response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/reject",
        json={"confirmation_token": "REJECT_PAYMENT", "note": "x"},
    )
    app.dependency_overrides.clear()

    assert verify_response.status_code == 403
    assert verify_response.json()["code"] == ErrorCode.AUTH_FORBIDDEN
    assert reject_response.status_code == 403
    assert reject_response.json()["code"] == ErrorCode.AUTH_FORBIDDEN
