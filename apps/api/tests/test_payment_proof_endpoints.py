import os
from datetime import UTC, datetime, date
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.api.deps import get_current_user
from app.common.enums import Channel, ParticipantFormStatus, PaymentStatus, ReservationStatus, UserRole
from app.common.labels import ErrorCode
from app.core.di import Container
from app.main import app

client = TestClient(app)


def _admin_user() -> SimpleNamespace:
    return SimpleNamespace(id="660000000000000000000001", role=UserRole.ADMIN, is_active=True)


def _guide_user() -> SimpleNamespace:
    return SimpleNamespace(id="660000000000000000000002", role=UserRole.GUIDE, is_active=True)


class _FakeProofDoc:
    """Fake PaymentProofDocument compatible with payment_proof_to_response."""

    def __init__(self, status: PaymentStatus) -> None:
        now = datetime.now(UTC)
        self.id = "660000000000000000000501"
        self.reservation_id = "660000000000000000000001"
        self.storage_key = "payment_proof/proof.pdf"
        self.filename = "proof.pdf"
        self.content_type = "application/pdf"
        self.size_bytes = 100
        self.sha256 = "abc"
        self.status = status
        self.uploaded_at = now
        self.created_at = now
        self.updated_at = now
        self.deleted_at = None
        self.version = 1

    def model_dump(self, exclude: set[str] | None = None) -> dict:
        data = {
            "id": self.id,
            "reservation_id": self.reservation_id,
            "storage_key": self.storage_key,
            "filename": self.filename,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "status": self.status,
            "uploaded_at": self.uploaded_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
            "version": self.version,
        }
        if exclude:
            for field in exclude:
                data.pop(field, None)
        return data


def _proof_doc(status: PaymentStatus) -> _FakeProofDoc:
    return _FakeProofDoc(status)


def _reservation_doc() -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id="660000000000000000000001",
        code="RES-001",
        experience_id="660000000000000000000010",
        channel=Channel.WHATSAPP,
        status=ReservationStatus.PENDING_PAYMENT,
        participant_count=2,
        payment_status=PaymentStatus.RECEIVED,
        holder_name="Carlos",
        holder_email="carlos@mail.com",
        holder_phone="3000000001",
        requested_date=date(2026, 6, 1),
        quoted_total_amount=Decimal("180000"),
        currency="COP",
        expected_participants_count=2,
        participants_completed_count=0,
        participant_form_status=ParticipantFormStatus.NOT_SENT,
        form_url=None,
        confirmed_at=None,
        cancelled_at=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
        deleted_at=None,
        version=1,
        participant_ids=[],
        payment_proof_ids=["660000000000000000000501"],
    )


def _reservation_response_data() -> dict:
    return {
        "id": "660000000000000000000001",
        "code": "RES-001",
        "experience_id": "660000000000000000000010",
        "channel": "whatsapp",
        "status": "payment_received",
        "participant_count": 2,
        "payment_status": "verified",
        "holder_name": "Carlos",
        "holder_email": "carlos@mail.com",
        "holder_phone": "3000000001",
        "requested_date": "2026-06-01",
        "quoted_total_amount": 180000,
        "currency": "COP",
        "expected_participants_count": 2,
        "participants_completed_count": 0,
        "participant_form_status": "not_sent",
        "form_url": None,
        "confirmed_at": None,
        "cancelled_at": None,
        "completed_at": None,
        "participants": [],
        "payment_proofs": [
            {
                "id": "660000000000000000000501",
                "reservation_id": "660000000000000000000001",
                "storage_key": "payment_proof/proof.pdf",
                "filename": "proof.pdf",
                "content_type": "application/pdf",
                "size_bytes": 100,
                "sha256": "abc",
                "status": "verified",
                "uploaded_at": datetime.now(UTC).isoformat(),
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
                "deleted_at": None,
                "version": 1,
            }
        ],
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "deleted_at": None,
        "version": 1,
    }


def test_verify_payment_proof_endpoint_returns_verified_status(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_verify(payment_proof_id, payload, *, actor_id, actor_role):
        captured["payment_proof_id"] = payment_proof_id
        captured["token"] = payload.confirmation_token
        captured["actor_id"] = str(actor_id)
        captured["actor_role"] = actor_role
        return _proof_doc(PaymentStatus.VERIFIED)

    monkeypatch.setattr(Container.get_instance().payment_proof_service, "verify_payment", fake_verify)
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


def test_reject_payment_proof_endpoint_returns_reservation_response(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_reject(payment_proof_id, payload, *, actor_id, actor_role):
        captured["payment_proof_id"] = payment_proof_id
        captured["token"] = payload.confirmation_token
        captured["reason"] = payload.reason
        captured["actor_id"] = str(actor_id)
        captured["actor_role"] = actor_role
        return _proof_doc(PaymentStatus.REJECTED)

    async def fake_get(_: str) -> SimpleNamespace:
        return _reservation_doc()

    async def fake_to_response(_: object) -> dict:
        return _reservation_response_data()

    monkeypatch.setattr(Container.get_instance().payment_proof_service, "reject_payment", fake_reject)
    monkeypatch.setattr("app.api.endpoints.payment_proofs.ReservationDocument.get", fake_get)
    monkeypatch.setattr("app.api.endpoints.payment_proofs.reservation_to_response", fake_to_response)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/reject",
        json={"confirmation_token": "REJECT_PAYMENT", "reason": "Monto incorrecto"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["code"] == "RES-001"
    assert response.json()["payment_status"] == "verified"
    assert captured == {
        "payment_proof_id": "660000000000000000000501",
        "token": "REJECT_PAYMENT",
        "reason": "Monto incorrecto",
        "actor_id": "660000000000000000000001",
        "actor_role": UserRole.ADMIN,
    }


def test_approve_payment_proof_endpoint_returns_reservation_response(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_approve(payment_proof_id, payload, *, actor_id, actor_role):
        captured["payment_proof_id"] = payment_proof_id
        captured["token"] = payload.confirmation_token
        captured["note"] = payload.note
        captured["actor_id"] = str(actor_id)
        captured["actor_role"] = actor_role
        return _proof_doc(PaymentStatus.VERIFIED)

    async def fake_get(_: str) -> SimpleNamespace:
        return _reservation_doc()

    async def fake_to_response(_: object) -> dict:
        return _reservation_response_data()

    monkeypatch.setattr(Container.get_instance().payment_proof_service, "approve_payment", fake_approve)
    monkeypatch.setattr("app.api.endpoints.payment_proofs.ReservationDocument.get", fake_get)
    monkeypatch.setattr("app.api.endpoints.payment_proofs.reservation_to_response", fake_to_response)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/approve",
        json={"confirmation_token": "APPROVE_PAYMENT", "note": "Pago verificado"},
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["code"] == "RES-001"
    assert response.json()["payment_status"] == "verified"
    assert len(response.json()["payment_proofs"]) == 1
    assert captured == {
        "payment_proof_id": "660000000000000000000501",
        "token": "APPROVE_PAYMENT",
        "note": "Pago verificado",
        "actor_id": "660000000000000000000001",
        "actor_role": UserRole.ADMIN,
    }


def test_reject_requires_reason() -> None:
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/reject",
        json={"confirmation_token": "REJECT_PAYMENT"},
    )
    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_reject_empty_reason_is_rejected() -> None:
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/reject",
        json={"confirmation_token": "REJECT_PAYMENT", "reason": ""},
    )
    app.dependency_overrides.clear()
    assert response.status_code == 422


def test_guide_cannot_verify_or_reject_payment_proof() -> None:
    app.dependency_overrides[get_current_user] = lambda: _guide_user()
    verify_response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/verify",
        json={"confirmation_token": "VERIFY_PAYMENT"},
    )
    reject_response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/reject",
        json={"confirmation_token": "REJECT_PAYMENT", "reason": "x"},
    )
    approve_response = client.post(
        "/api/v1/payment-proofs/660000000000000000000501/approve",
        json={"confirmation_token": "APPROVE_PAYMENT"},
    )
    app.dependency_overrides.clear()

    assert verify_response.status_code == 403
    assert verify_response.json()["code"] == ErrorCode.AUTH_FORBIDDEN
    assert reject_response.status_code == 403
    assert reject_response.json()["code"] == ErrorCode.AUTH_FORBIDDEN
    assert approve_response.status_code == 403
    assert approve_response.json()["code"] == ErrorCode.AUTH_FORBIDDEN


def test_download_with_file_data_returns_bytes(monkeypatch) -> None:
    """When service returns bytes (from file_data or storage), endpoint streams them."""

    async def fake_download(_: str) -> tuple[str, bytes | None]:
        return "image/png", b"fake-png-bytes"

    monkeypatch.setattr(Container.get_instance().payment_proof_service, "get_download", fake_download)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.get(
        "/api/v1/payment-proofs/660000000000000000000501/download",
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers.get("content-type") == "image/png"
    assert response.content == b"fake-png-bytes"


def test_download_pending_whatsapp_proof_returns_202(monkeypatch) -> None:
    """WhatsApp proof not yet downloaded returns 202 with pending status."""

    async def fake_download(_: str) -> tuple[str, bytes | None]:
        return "pending", None

    monkeypatch.setattr(Container.get_instance().payment_proof_service, "get_download", fake_download)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.get(
        "/api/v1/payment-proofs/660000000000000000000501/download",
    )
    app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json()["status"] == "pending"


def test_download_file_not_found_returns_404(monkeypatch) -> None:
    """When storage_key has no file and no file_data, endpoint returns 404."""

    async def fake_download(_: str) -> tuple[str, bytes | None]:
        from app.common.labels import ErrorCode
        from app.core.errors import ApiError

        raise ApiError(
            status_code=404,
            code=ErrorCode.PAYMENT_PROOF_FILE_NOT_FOUND,
            message="Archivo no encontrado en el almacenamiento.",
            details={"storage_key": "missing/file.pdf"},
        )

    monkeypatch.setattr(Container.get_instance().payment_proof_service, "get_download", fake_download)
    app.dependency_overrides[get_current_user] = lambda: _admin_user()
    response = client.get(
        "/api/v1/payment-proofs/660000000000000000000501/download",
    )
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["code"] == ErrorCode.PAYMENT_PROOF_FILE_NOT_FOUND
