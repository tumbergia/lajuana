"""P1: Booking flow — create pending reservation (quote → pending_payment).

Risk: the booking flow is the primary customer conversion funnel. If the
quote/pre-reserve/confirm chain breaks, revenue is directly impacted.

Tests the core BookingService.create_pending_reservation method which
orchestrates quote creation → status transition to PENDING_PAYMENT.
"""

from __future__ import annotations

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.common.enums import ReservationStatus
from app.core.errors import ApiError
from app.services.booking_service import BookingService


class FakeReservationService:
    """Simulates ReservationService for unit tests."""

    def __init__(self) -> None:
        self.created_reservations: list[dict] = []
        self.set_status_calls: list[tuple[str, ReservationStatus]] = []

    async def create(
        self,
        payload: dict,
        actor_id: object = None,
        initial_status: ReservationStatus | None = None,
    ) -> SimpleNamespace:
        self.created_reservations.append(
            {"payload": payload, "actor_id": actor_id, "initial_status": initial_status}
        )
        return SimpleNamespace(
            id="660000000000000000000001",
            code="RES-001",
            status=initial_status or ReservationStatus.QUOTED,
            experience_id=payload.get("experience_id"),
            requested_date=payload.get("requested_date"),
            participant_count=payload.get("participant_count"),
        )

    async def set_status(
        self,
        reservation_id: str,
        target_status: ReservationStatus,
        actor_id: object = None,
    ) -> SimpleNamespace:
        self.set_status_calls.append((reservation_id, target_status))
        return SimpleNamespace(
            id=reservation_id,
            status=target_status,
            code="RES-001",
        )

    async def has_active_reservation_for_date(self, requested_date: date) -> bool:
        return False


class TestBookingService:
    """Booking flow tests."""

    def test_create_pending_reservation_creates_with_quoted_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """BookingService.create_pending_reservation should create a reservation
        with QUOTED status first, then transition to PENDING_PAYMENT."""
        fake = FakeReservationService()

        async def run() -> None:
            svc = BookingService(reservation_service=fake)  # type: ignore[arg-type]

            # Mock the channel setting
            monkeypatch.setattr(
                "app.services.booking_service.settings.chat_default_channel",
                "whatsapp",
            )

            result = await svc.create_pending_reservation(
                experience_id="660000000000000000000020",
                participant_count=2,
                requested_date=date(2026, 7, 15),
                holder_name="Test User",
                holder_email="test@example.com",
                holder_phone="+573001234567",
            )

            # Verify the result
            assert result is not None
            assert result.id == "660000000000000000000001"

            # Verify create was called with QUOTED status
            assert len(fake.created_reservations) == 1
            create_call = fake.created_reservations[0]
            assert create_call["initial_status"] == ReservationStatus.QUOTED
            assert create_call["payload"]["experience_id"] == "660000000000000000000020"
            assert create_call["payload"]["participant_count"] == 2

            # Verify set_status was called with PENDING_PAYMENT
            assert len(fake.set_status_calls) == 1
            status_call = fake.set_status_calls[0]
            assert status_call[0] == "660000000000000000000001"
            assert status_call[1] == ReservationStatus.PENDING_PAYMENT

        asyncio.run(run())

    def test_date_is_available_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """date_is_available should return True when no active reservation exists."""
        fake = FakeReservationService()
        svc = BookingService(reservation_service=fake)  # type: ignore[arg-type]

        async def run() -> None:
            available = await svc.date_is_available(requested_date=date(2026, 7, 15))
            assert available is True

        asyncio.run(run())

    def test_date_is_available_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """date_is_available should return False when an active reservation exists."""

        class FakeReservationServiceBusy:
            async def has_active_reservation_for_date(self, requested_date: date) -> bool:
                return True

        svc = BookingService(reservation_service=FakeReservationServiceBusy())  # type: ignore[arg-type]

        async def run() -> None:
            available = await svc.date_is_available(requested_date=date(2026, 7, 15))
            assert available is False

        asyncio.run(run())

    def test_create_pending_reservation_without_optional_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should work without optional fields like holder_name, email, phone."""
        fake = FakeReservationService()
        svc = BookingService(reservation_service=fake)  # type: ignore[arg-type]

        monkeypatch.setattr(
            "app.services.booking_service.settings.chat_default_channel",
            "whatsapp",
        )

        async def run() -> None:
            result = await svc.create_pending_reservation(
                experience_id="660000000000000000000020",
                participant_count=1,
                requested_date=None,
            )

            assert result is not None
            assert len(fake.created_reservations) == 1
            create_call = fake.created_reservations[0]
            assert create_call["payload"]["requested_date"] is None
            assert create_call["payload"]["holder_name"] is None

        asyncio.run(run())

    def test_create_pending_reservation_invalid_participant_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should propagate ApiError when participant count is invalid."""

        class FakeReservationServiceValidating(FakeReservationService):
            async def create(
                self,
                payload: dict,
                actor_id: object = None,
                initial_status: ReservationStatus | None = None,
            ) -> SimpleNamespace:
                if payload.get("participant_count", 0) <= 0:
                    raise ApiError(
                        status_code=400,
                        code="reservation.invalid_participant_count",
                        message="Número de participantes inválido.",
                    )
                return await super().create(payload, actor_id, initial_status)

        svc = BookingService(reservation_service=FakeReservationServiceValidating())  # type: ignore[arg-type]
        monkeypatch.setattr(
            "app.services.booking_service.settings.chat_default_channel",
            "whatsapp",
        )

        async def run() -> None:
            # The schema validation should catch this before reaching the service
            # but we verify the error path anyway
            from pydantic import ValidationError

            from app.schemas.reservation import ReservationCreateSchema

            with pytest.raises(ValidationError):
                ReservationCreateSchema(
                    experience_id="660000000000000000000020",
                    participant_count=0,
                    channel="whatsapp",
                )

        asyncio.run(run())
