"""Tests for PaymentProofService — verifies payment proof lifecycle.

P0 risk: incorrect verify/reject can release horses without payment.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.common.enums import PaymentStatus, ReservationStatus, UserRole
from app.core.errors import ApiError


def _proof(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000501",
        reservation_id="660000000000000000000001",
        storage_key="proofs/x.pdf",
        status=PaymentStatus.RECEIVED,
        uploaded_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        deleted_at=None,
        version=1,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _reservation(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000001",
        code="RES-001",
        status=ReservationStatus.PAYMENT_RECEIVED,
        payment_status=PaymentStatus.RECEIVED,
        holder_phone="+573001234567",
        holder_email="test@test.com",
        holder_name="Test User",
        participant_count=2,
        experience_id="660000000000000000000010",
        form_url="",
        participant_form_sent_at=None,
        participant_form_send_count=0,
        confirmation_message_sent_at=None,
        updated_by=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestPaymentProofVerify:
    """verify_payment — core flow, reservation status sync, rollback."""

    def test_verify_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        proof = _proof()
        reservation = _reservation()

        async def run() -> None:
            async def _mock_payment_proof_get(_: str) -> object:
                return proof
            async def _mock_reservation_get(_: str) -> object:
                return reservation
            monkeypatch.setattr(
                "app.services.payment_proof_service.PaymentProofDocument.get",
                _mock_payment_proof_get,
            )
            monkeypatch.setattr(
                "app.services.payment_proof_service.ReservationDocument.get",
                _mock_reservation_get,
            )

            calls: list[str] = []

            async def _save() -> None:
                calls.append("save")

            proof.save = _save  # type: ignore[assignment]
            reservation.save = _save  # type: ignore[assignment]

            from app.schemas.payment_proof import PaymentProofVerifySchema

            payload = PaymentProofVerifySchema(confirmation_token="VERIFY_PAYMENT")
            from app.common.enums import UserRole
            from app.services.payment_proof_service import PaymentProofService

            svc = PaymentProofService()
            result = await svc.verify_payment(
                payment_proof_id="660000000000000000000501",
                payload=payload,
                actor_id="660000000000000000000001",
                actor_role=UserRole.ADMIN,
            )
            assert result.id == proof.id
            assert result.status == PaymentStatus.VERIFIED

        asyncio.run(run())

    def test_verify_invalid_transition_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """VERIFIED->VERIFIED is not allowed."""
        proof = _proof(status=PaymentStatus.VERIFIED)
        reservation = _reservation()

        async def run() -> None:
            async def _mock_payment_proof_get(_: str) -> object:
                return proof
            async def _mock_reservation_get(_: str) -> object:
                return reservation
            monkeypatch.setattr(
                "app.services.payment_proof_service.PaymentProofDocument.get",
                _mock_payment_proof_get,
            )
            monkeypatch.setattr(
                "app.services.payment_proof_service.ReservationDocument.get",
                _mock_reservation_get,
            )

            from app.schemas.payment_proof import PaymentProofVerifySchema

            payload = PaymentProofVerifySchema(confirmation_token="VERIFY_PAYMENT")
            from app.services.payment_proof_service import PaymentProofService

            svc = PaymentProofService()
            with pytest.raises(ApiError) as exc:
                await svc.verify_payment(
                    payment_proof_id="660000000000000000000501",
                    payload=payload,
                    actor_id="660000000000000000000001",
                    actor_role=UserRole.ADMIN,
                )
            assert exc.value.status_code == 409

        asyncio.run(run())

    def test_verify_proof_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def run() -> None:
            async def _mock_proof_get_none(_: str) -> None:
                return None
            monkeypatch.setattr(
                "app.services.payment_proof_service.PaymentProofDocument.get",
                _mock_proof_get_none,
            )

            from app.schemas.payment_proof import PaymentProofVerifySchema

            payload = PaymentProofVerifySchema(confirmation_token="VERIFY_PAYMENT")
            from app.services.payment_proof_service import PaymentProofService

            svc = PaymentProofService()
            with pytest.raises(ApiError) as exc:
                await svc.verify_payment(
                    payment_proof_id="660000000000000000000999",
                    payload=payload,
                    actor_id="660000000000000000000001",
                    actor_role=UserRole.ADMIN,
                )
            assert exc.value.status_code == 404

        asyncio.run(run())


class TestPaymentProofReject:
    def test_reject_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        proof = _proof()
        reservation = _reservation()

        async def run() -> None:
            async def _mock_payment_proof_get(_: str) -> object:
                return proof
            async def _mock_reservation_get(_: str) -> object:
                return reservation
            monkeypatch.setattr(
                "app.services.payment_proof_service.PaymentProofDocument.get",
                _mock_payment_proof_get,
            )
            monkeypatch.setattr(
                "app.services.payment_proof_service.ReservationDocument.get",
                _mock_reservation_get,
            )

            calls: list[str] = []

            async def _save() -> None:
                calls.append("save")

            proof.save = _save  # type: ignore[assignment]
            reservation.save = _save  # type: ignore[assignment]

            from app.schemas.payment_proof import PaymentProofRejectSchema

            payload = PaymentProofRejectSchema(confirmation_token="REJECT_PAYMENT", reason="Documento ilegible")
            from app.common.enums import UserRole
            from app.services.payment_proof_service import PaymentProofService

            svc = PaymentProofService()
            result = await svc.reject_payment(
                payment_proof_id="660000000000000000000501",
                payload=payload,
                actor_id="660000000000000000000001",
                actor_role=UserRole.ADMIN,
            )
            assert result.status == PaymentStatus.REJECTED

        asyncio.run(run())

    def test_reject_empty_reason_rejected_by_schema(self) -> None:
        """Empty reason rejected by Pydantic schema validation (min_length=1)."""
        from pydantic import ValidationError
        from app.schemas.payment_proof import PaymentProofRejectSchema

        with pytest.raises(ValidationError):
            PaymentProofRejectSchema(confirmation_token="REJECT_PAYMENT", reason="")

    def test_reject_terminal_state_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """REJECTED->REJECTED is not allowed."""
        proof = _proof(status=PaymentStatus.REJECTED)
        reservation = _reservation()

        async def run() -> None:
            async def _mock_payment_proof_get(_: str) -> object:
                return proof
            async def _mock_reservation_get(_: str) -> object:
                return reservation
            monkeypatch.setattr(
                "app.services.payment_proof_service.PaymentProofDocument.get",
                _mock_payment_proof_get,
            )
            monkeypatch.setattr(
                "app.services.payment_proof_service.ReservationDocument.get",
                _mock_reservation_get,
            )

            from app.schemas.payment_proof import PaymentProofRejectSchema

            payload = PaymentProofRejectSchema(confirmation_token="REJECT_PAYMENT", reason="Duplicado")
            from app.common.enums import UserRole
            from app.services.payment_proof_service import PaymentProofService

            svc = PaymentProofService()
            with pytest.raises(ApiError) as exc:
                await svc.reject_payment(
                    payment_proof_id="660000000000000000000501",
                    payload=payload,
                    actor_id="660000000000000000000001",
                    actor_role=UserRole.ADMIN,
                )
            assert exc.value.status_code == 409

        asyncio.run(run())
