"""P0: Race condition — two concurrent confirms on same reservation.

Risk: double confirmation or inconsistent day-lock state.

Two concurrent confirm_reservation calls must not both succeed.
The second call must detect the race and fail with ApiError (409),
or the state machine must prevent the double transition (invalid status).

IMPORTANT: mock functions assigned to SimpleNamespace attributes receive NO self
           (no method binding). Mock functions on class via monkeypatch.setattr
           receive self as first arg.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.common.enums import PaymentStatus, ReservationStatus
from app.core.errors import ApiError


def _reservation(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000001",
        code="RES-001",
        status=ReservationStatus.PAYMENT_RECEIVED,
        requested_date=date.today() + timedelta(days=30),
        experience_id="660000000000000000000020",
        holder_name="Test",
        holder_phone="+573001234567",
        participant_count=2,
        payment_status=PaymentStatus.VERIFIED,
        payment_proof_ids=["proof-1"],
        confirmed_at=None,
        updated_by=None,
        blocks_day=False,
        availability_lock_key=None,
        form_url=None,
        expected_participants_count=2,
        participants_completed_count=0,
        participant_form_status="not_sent",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestConcurrentConfirm:
    """Race condition: two concurrent confirm_reservation calls."""

    def test_concurrent_confirm_second_fails_on_day_lock(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two concurrent confirms on the same reservation: only one succeeds.

        Losers fail because the status transition is no longer valid once the
        first call moves the reservation to CONFIRMED.
        """
        status_tracker: list[ReservationStatus] = [ReservationStatus.PAYMENT_RECEIVED]

        async def run() -> None:
            async def _mock_get_reservation(_self: object, rid: str, **kwargs: object) -> object:
                obj = _reservation(status=status_tracker[0])
                obj.save = _mock_save  # type: ignore[assignment]
                return obj

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get_reservation,
            )

            async def _mock_transition(
                _self: object, reservation: object, target: ReservationStatus
            ) -> None:
                if status_tracker[0] != ReservationStatus.PAYMENT_RECEIVED:
                    raise ApiError(
                        status_code=409,
                        code="reservation.invalid_status_transition",
                        message="Invalid transition",
                    )
                status_tracker[0] = ReservationStatus.CONFIRMED
                reservation.status = ReservationStatus.CONFIRMED

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.transition_status",
                _mock_transition,
            )

            async def _noop(*args: object, **kwargs: object) -> None:
                pass

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.ensure_date_available",
                _noop,
            )
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._sync_day_lock_fields",
                _noop,
            )

            async def _mock_notify(*args: object, **kwargs: object) -> None:
                pass

            async def _mock_generate(*args: object, **kwargs: object) -> tuple[str, str]:
                return "token", "raw_token"

            async def _mock_get_rules() -> object:
                return SimpleNamespace(
                    min_days_in_advance=0,
                    require_payment_proof_for_confirmation=True,
                )

            from app.services.reservation_service import ReservationService

            svc = ReservationService(
                notification_service=SimpleNamespace(
                    enqueue_reservation_confirmed=_mock_notify,
                    enqueue_reservation_confirmed_logistics=_mock_notify,
                ),
                form_link_service=SimpleNamespace(generate=_mock_generate),
                config_service=SimpleNamespace(get_reservation_rules=_mock_get_rules),
            )

            async def _mock_save() -> None:
                pass

            async def _mock_get_exp(eid: str) -> object:
                return SimpleNamespace(id=eid, name="Test Experience")

            monkeypatch.setattr(
                "app.services.reservation_service.ExperienceDocument.get",
                _mock_get_exp,
            )

            results = await asyncio.gather(
                *[
                    svc.confirm_reservation(
                        reservation_id="660000000000000000000001",
                        actor_id="660000000000000000000050",
                    )
                    for _ in range(5)
                ],
                return_exceptions=True,
            )

            successes = [r for r in results if not isinstance(r, Exception)]
            failures = [r for r in results if isinstance(r, Exception)]
            assert len(successes) == 1, (
                f"Expected 1 success, got {len(successes)}. "
                f"Failures: {[(type(f).__name__, str(f)) for f in failures]}"
            )
            assert len(failures) == 4, f"Expected 4 failures, got {len(failures)}"
            failure = failures[0]
            assert isinstance(failure, ApiError), (
                f"Expected ApiError, got {type(failure).__name__}: {failure}"
            )

        asyncio.run(run())

    def test_concurrent_confirm_same_date_blocks_second_reservation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two reservations on the same date: second confirm fails on day-lock."""
        confirmed_dates: dict[str, str] = {}
        reservation_ids = [
            "660000000000000000000001",
            "660000000000000000000002",
        ]

        async def run() -> None:
            async def _mock_get_reservation(_self: object, rid: str, **kwargs: object) -> object:
                obj = _reservation(id=rid)
                obj.save = _mock_save  # type: ignore[assignment]
                return obj

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get_reservation,
            )

            async def _mock_ensure_date_available(
                _self: object,
                requested_date: date,
                exclude_reservation_id: str | None = None,
            ) -> None:
                key = requested_date.isoformat()
                blocker = confirmed_dates.get(key)
                if blocker is not None and blocker != exclude_reservation_id:
                    raise ApiError(
                        status_code=409,
                        code="reservation.no_availability",
                        message="La fecha ya tiene una reserva activa.",
                    )

            async def _mock_transition(
                _self: object, reservation: object, target: ReservationStatus
            ) -> None:
                reservation.status = target
                if target == ReservationStatus.CONFIRMED and reservation.requested_date:
                    confirmed_dates[reservation.requested_date.isoformat()] = str(reservation.id)

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.ensure_date_available",
                _mock_ensure_date_available,
            )
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.transition_status",
                _mock_transition,
            )

            async def _noop(*args: object, **kwargs: object) -> None:
                pass

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._sync_day_lock_fields",
                _noop,
            )

            async def _mock_notify(*args: object, **kwargs: object) -> None:
                pass

            async def _mock_generate(*args: object, **kwargs: object) -> tuple[str, str]:
                return "token", "raw_token"

            async def _mock_get_rules() -> object:
                return SimpleNamespace(
                    min_days_in_advance=0,
                    require_payment_proof_for_confirmation=True,
                )

            from app.services.reservation_service import ReservationService

            svc = ReservationService(
                notification_service=SimpleNamespace(
                    enqueue_reservation_confirmed=_mock_notify,
                    enqueue_reservation_confirmed_logistics=_mock_notify,
                ),
                form_link_service=SimpleNamespace(generate=_mock_generate),
                config_service=SimpleNamespace(get_reservation_rules=_mock_get_rules),
            )

            async def _mock_save() -> None:
                pass

            async def _mock_get_exp(eid: str) -> object:
                return SimpleNamespace(id=eid, name="Test Experience")

            monkeypatch.setattr(
                "app.services.reservation_service.ExperienceDocument.get",
                _mock_get_exp,
            )

            first = await svc.confirm_reservation(
                reservation_id=reservation_ids[0],
                actor_id="660000000000000000000050",
            )
            assert first.status == ReservationStatus.CONFIRMED

            with pytest.raises(ApiError):
                await svc.confirm_reservation(
                    reservation_id=reservation_ids[1],
                    actor_id="660000000000000000000050",
                )

        asyncio.run(run())
