"""Cancel reservation tests — state transitions, capacity rollback.

P1 risk: incorrect cancellation can lead to revenue loss or double refund.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.common.enums import ReservationStatus
from app.core.di import Container
from app.core.errors import ApiError


def _reservation(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000001",
        code="RES-001",
        status=ReservationStatus.CONFIRMED,
        schedule_id="660000000000000000000010",
        requested_date=None,
        holder_name="Test",
        holder_phone="+573001234567",
        holder_email="test@test.com",
        participant_count=2,
        experience_id="660000000000000000000020",
        cancelled_at=None,
        updated_by=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _schedule(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000010",
        status="open",
        is_active=True,
        available_slots=5,
        date=None,
        start_time="08:00",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestCancelReservation:
    """cancel_reservation — state machine + schedule rollback."""

    def test_cancel_from_confirmed_reopens_schedule(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        res = _reservation()
        sched = _schedule()

        async def run() -> None:
            async def _mock_get(_self: object, rid: str) -> object:
                return res
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            async def _mock_schedule_get(sid: str) -> object:
                return sched
            monkeypatch.setattr(
                "app.services.reservation_service.ScheduleDocument.get",
                _mock_schedule_get,
            )

            async def _mock_save() -> None:
                pass
            res.save = _mock_save  # type: ignore[assignment]
            sched.save = _mock_save  # type: ignore[assignment]

            # No other active reservations for this schedule
            async def _mock_has_active(_self: object, _sid: str) -> bool:
                return False
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.has_active_reservation_for_schedule",
                _mock_has_active,
            )

            async def _mock_sync(_self: object, _res: object) -> None:
                pass
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._sync_day_lock_fields",
                _mock_sync,
            )

            svc = Container.get_instance().reservation_service
            result = await svc.cancel_reservation(
                reservation_id="660000000000000000000001",
                actor_id="660000000000000000000050",
            )
            assert result.status == ReservationStatus.CANCELLED
            assert sched.status == "open"

        asyncio.run(run())

    def test_cancel_confirmed_keeps_schedule_status_when_other_reservations_exist(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Schedule stays CLOSED if other active reservations still use it."""
        res = _reservation()
        sched = _schedule(status="closed")

        async def run() -> None:
            async def _mock_get(_self: object, rid: str) -> object:
                return res
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            async def _mock_schedule_get(sid: str) -> object:
                return sched
            monkeypatch.setattr(
                "app.services.reservation_service.ScheduleDocument.get",
                _mock_schedule_get,
            )

            async def _mock_save() -> None:
                pass
            res.save = _mock_save  # type: ignore[assignment]
            sched.save = _mock_save  # type: ignore[assignment]

            # Another active reservation exists
            async def _mock_has_active2(_self: object, _sid: str) -> bool:
                return True
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.has_active_reservation_for_schedule",
                _mock_has_active2,
            )

            async def _mock_sync2(_self: object, _res: object) -> None:
                pass
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._sync_day_lock_fields",
                _mock_sync2,
            )

            svc = Container.get_instance().reservation_service
            result = await svc.cancel_reservation(
                reservation_id="660000000000000000000001",
                actor_id="660000000000000000000050",
            )
            assert result.status == ReservationStatus.CANCELLED
            # Schedule status should NOT have been changed
            assert sched.status == "closed"

        asyncio.run(run())

    def test_cancel_from_pre_reserved_no_schedule(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        res = _reservation(
            status=ReservationStatus.PRE_RESERVED,
            schedule_id=None,
        )

        async def run() -> None:
            async def _mock_get(_self: object, rid: str) -> object:
                return res
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            async def _mock_save() -> None:
                pass
            res.save = _mock_save  # type: ignore[assignment]

            async def _mock_sync3(_self: object, _res: object) -> None:
                pass
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._sync_day_lock_fields",
                _mock_sync3,
            )

            svc = Container.get_instance().reservation_service
            result = await svc.cancel_reservation(
                reservation_id="660000000000000000000001",
                actor_id="660000000000000000000050",
            )
            assert result.status == ReservationStatus.CANCELLED

        asyncio.run(run())

    def test_cancel_from_cancelled_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Terminal state: CANCELLED → CANCELLED is not allowed."""
        res = _reservation(status=ReservationStatus.CANCELLED)

        async def run() -> None:
            async def _mock_get(_self: object, rid: str) -> object:
                return res
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            async def _mock_save() -> None:
                pass
            res.save = _mock_save  # type: ignore[assignment]

            svc = Container.get_instance().reservation_service
            with pytest.raises(ApiError) as exc:
                await svc.cancel_reservation(
                    reservation_id="660000000000000000000001",
                    actor_id="660000000000000000000050",
                )
            assert exc.value.status_code == 409

        asyncio.run(run())

    def test_cancel_from_completed_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Terminal state: COMPLETED → CANCELLED is not allowed."""
        res = _reservation(status=ReservationStatus.COMPLETED)

        async def run() -> None:
            async def _mock_get(_self: object, rid: str) -> object:
                return res
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            async def _mock_save() -> None:
                pass
            res.save = _mock_save  # type: ignore[assignment]

            svc = Container.get_instance().reservation_service
            with pytest.raises(ApiError) as exc:
                await svc.cancel_reservation(
                    reservation_id="660000000000000000000001",
                    actor_id="660000000000000000000050",
                )
            assert exc.value.status_code == 409

        asyncio.run(run())
