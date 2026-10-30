"""Cancel reservation tests — state transitions and day-lock release.

P1 risk: incorrect cancellation can lead to revenue loss or double refund.
"""

from __future__ import annotations

import asyncio
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
        experience_id="660000000000000000000020",
        requested_date=None,
        holder_name="Test",
        holder_phone="+573001234567",
        holder_email="test@test.com",
        participant_count=2,
        cancelled_at=None,
        updated_by=None,
        blocks_day=True,
        availability_lock_key="2026-07-15",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestCancelReservation:
    """cancel_reservation — state machine + day-lock sync."""

    def test_cancel_from_confirmed_releases_day_lock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        res = _reservation()
        sync_calls: list[object] = []

        async def run() -> None:
            async def _mock_save() -> None:
                pass

            res.save = _mock_save  # type: ignore[assignment]

            async def _mock_get(_rid: str, **_kwargs: object) -> object:
                return res

            async def _mock_sync(reservation: object) -> None:
                sync_calls.append(reservation)
                reservation.blocks_day = False
                reservation.availability_lock_key = None

            async def _noop(*_args: object, **_kwargs: object) -> None:
                pass

            async def _mock_get_exp(*_args: object, **_kwargs: object) -> object:
                return SimpleNamespace(name="Test Experience")

            svc = Container.get_instance().reservation_service
            monkeypatch.setattr(svc, "get", _mock_get)
            monkeypatch.setattr(svc, "_sync_day_lock_fields", _mock_sync)
            monkeypatch.setattr(
                "app.services.reservation_service.ExperienceDocument.get",
                _mock_get_exp,
            )
            monkeypatch.setattr(
                svc.notification_service,
                "enqueue_reservation_cancelled",
                _noop,
            )

            result = await svc.cancel_reservation(
                reservation_id="660000000000000000000001",
                actor_id="660000000000000000000050",
            )
            assert result.status == ReservationStatus.CANCELLED
            assert sync_calls == [res]
            assert res.blocks_day is False
            assert res.availability_lock_key is None

        asyncio.run(run())

    def test_cancel_from_pre_reserved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        res = _reservation(
            status=ReservationStatus.PRE_RESERVED,
            blocks_day=False,
            availability_lock_key=None,
        )

        async def run() -> None:
            async def _mock_save() -> None:
                pass

            res.save = _mock_save  # type: ignore[assignment]

            async def _mock_get(_rid: str, **_kwargs: object) -> object:
                return res

            async def _mock_sync(_reservation: object) -> None:
                pass

            svc = Container.get_instance().reservation_service
            monkeypatch.setattr(svc, "get", _mock_get)
            monkeypatch.setattr(svc, "_sync_day_lock_fields", _mock_sync)

            result = await svc.cancel_reservation(
                reservation_id="660000000000000000000001",
                actor_id="660000000000000000000050",
            )
            assert result.status == ReservationStatus.CANCELLED

        asyncio.run(run())

    def test_cancel_from_cancelled_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Terminal state: CANCELLED → CANCELLED is not allowed."""
        res = _reservation(status=ReservationStatus.CANCELLED)

        async def run() -> None:
            async def _mock_save() -> None:
                pass

            res.save = _mock_save  # type: ignore[assignment]

            async def _mock_get(_rid: str, **_kwargs: object) -> object:
                return res

            svc = Container.get_instance().reservation_service
            monkeypatch.setattr(svc, "get", _mock_get)

            with pytest.raises(ApiError) as exc:
                await svc.cancel_reservation(
                    reservation_id="660000000000000000000001",
                    actor_id="660000000000000000000050",
                )
            assert exc.value.status_code == 409

        asyncio.run(run())

    def test_cancel_from_completed_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Terminal state: COMPLETED → CANCELLED is not allowed."""
        res = _reservation(status=ReservationStatus.COMPLETED)

        async def run() -> None:
            async def _mock_save() -> None:
                pass

            res.save = _mock_save  # type: ignore[assignment]

            async def _mock_get(_rid: str, **_kwargs: object) -> object:
                return res

            svc = Container.get_instance().reservation_service
            monkeypatch.setattr(svc, "get", _mock_get)

            with pytest.raises(ApiError) as exc:
                await svc.cancel_reservation(
                    reservation_id="660000000000000000000001",
                    actor_id="660000000000000000000050",
                )
            assert exc.value.status_code == 409

        asyncio.run(run())
