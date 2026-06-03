"""P0: Race condition — two concurrent confirms on same reservation.
Risk: double schedule capacity reduction, double payment processing.

Two concurrent confirm_reservation calls must not reduce schedule capacity twice.
The second call must detect the race and fail with ApiError (409),
or the state machine must prevent the double transition (invalid status).

IMPORTANT: mock functions assigned to SimpleNamespace attributes receive NO self
           (no method binding). Mock functions on class via monkeypatch.setattr
           receive self as first arg.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from app.common.enums import PaymentStatus, ReservationStatus
from app.core.errors import ApiError


def _reservation(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000001",
        code="RES-001",
        status=ReservationStatus.PAYMENT_RECEIVED,
        schedule_id="660000000000000000000010",
        requested_date=date(2026, 7, 15),
        holder_name="Test",
        holder_phone="+573001234567",
        participant_count=2,
        experience_id="660000000000000000000020",
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


def _schedule(**overrides: object) -> SimpleNamespace:
    base = dict(
        id="660000000000000000000010",
        status="open",
        is_active=True,
        available_slots=5,
        held_slots=2,
        reserved_slots=0,
        date=date(2026, 7, 15),
        start_time="08:00",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestConcurrentConfirm:
    """Race condition: two concurrent confirm_reservation calls."""

    def test_concurrent_confirm_second_fails_on_capacity(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two concurrent confirms: first commits capacity, second fails because
        the capacity is already taken by the first call.

        This simulates the real race where both calls pass the initial status
        check before either commits the schedule capacity.
        """
        res = _reservation()
        sched = _schedule()

        async def run() -> None:
            # ── Mock class methods (receive self as first arg) ──

            async def _mock_get_reservation(_self: object, rid: str, **kwargs: object) -> object:
                return res

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get_reservation,
            )

            async def _mock_get_schedule(sid: str) -> object:
                return sched

            monkeypatch.setattr(
                "app.services.reservation_service.ScheduleDocument.get",
                _mock_get_schedule,
            )

            call_count = 0
            capacity_committed = False

            async def _mock_commit_capacity(
                _self: object, *, schedule_id: str, participant_count: int
            ) -> str | None:
                nonlocal call_count, capacity_committed
                call_count += 1
                if call_count == 1:
                    capacity_committed = True
                    return "available"
                return None  # second call: capacity already taken

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._commit_schedule_capacity",
                _mock_commit_capacity,
            )

            async def _mock_rollback(
                _self: object, *, schedule_id: str, participant_count: int, capacity_source: str
            ) -> None:
                pass

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._rollback_schedule_capacity",
                _mock_rollback,
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
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.transition_status",
                _noop,
            )
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._save_schedule_status",
                _noop,
            )

            # ── Mock SimpleNamespace functions (NO self arg) ──
            async def _mock_notify(*args: object, **kwargs: object) -> None:
                pass

            async def _mock_generate(*args: object, **kwargs: object) -> tuple[None, None]:
                return None, None

            # config_service.get_reservation_rules is called without binding
            async def _mock_get_rules() -> object:
                return SimpleNamespace(
                    min_days_in_advance=0,
                    require_payment_proof_for_confirmation=True,
                )

            # ── Build service with mock deps ──
            from app.services.reservation_service import ReservationService

            svc = ReservationService(
                notification_service=SimpleNamespace(
                    enqueue_reservation_confirmed=_mock_notify,
                    enqueue_reservation_confirmed_logistics=_mock_notify,
                ),
                form_link_service=SimpleNamespace(generate=_mock_generate),
                config_service=SimpleNamespace(get_reservation_rules=_mock_get_rules),
            )

            # ── Save stubs ──
            async def _mock_save() -> None:
                pass

            res.save = _mock_save  # type: ignore[assignment]
            sched.save = _mock_save  # type: ignore[assignment]

            # ── Mock ExperienceDocument.get (classmethod → cls passed) ──
            async def _mock_get_exp(eid: str) -> object:
                return SimpleNamespace(id=eid, name="Test Experience")

            monkeypatch.setattr(
                "app.services.reservation_service.ExperienceDocument.get",
                _mock_get_exp,
            )

            # ── Act — fire 5 confirms simultaneously ──
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

            # ── Assert — only one should succeed ──
            successes = [r for r in results if not isinstance(r, Exception)]
            failures = [r for r in results if isinstance(r, Exception)]
            assert len(successes) == 1, (
                f"Expected 1 success, got {len(successes)}. "
                f"Failures: {[(type(f).__name__, str(f)) for f in failures]}"
            )
            assert len(failures) == 4, (
                f"Expected 4 failures, got {len(failures)}"
            )
            failure = failures[0]
            assert isinstance(failure, ApiError), (
                f"Expected ApiError, got {type(failure).__name__}: {failure}"
            )

        asyncio.run(run())

    def test_concurrent_confirm_second_fails_on_status_transition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two concurrent confirms: first completes, second sees PAYMENT_RECEIVED
        is no longer allowed because the status was already changed.

        This tests the case where the first call completes fully (capacity +
        status transition), and the second call fails because the reservation
        status transition is no longer valid.
        """
        status_tracker: list[ReservationStatus] = [ReservationStatus.PAYMENT_RECEIVED]

        async def run() -> None:
            # Each confirm_reservation reads the reservation once at start.
            # The mock returns the CURRENT status from the tracker.
            # Both calls initially see PAYMENT_RECEIVED (passed validation).
            # First call commits capacity + transitions to CONFIRMED.
            # Second call commits capacity (different capacity source) + tries
            #   to transition, but status is now CONFIRMED → fails.

            async def _mock_get_reservation(_self: object, rid: str, **kwargs: object) -> object:
                obj = _reservation(status=status_tracker[0])
                obj.save = _mock_save  # type: ignore[assignment]
                return obj

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get_reservation,
            )

            # Both calls can commit capacity (different slots)
            async def _mock_commit_capacity(
                _self: object, *, schedule_id: str, participant_count: int
            ) -> str:
                return "available"

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._commit_schedule_capacity",
                _mock_commit_capacity,
            )

            # First call transitions OK, second call sees invalid status
            async def _mock_transition(
                _self: object, reservation: object, target: ReservationStatus
            ) -> None:
                if status_tracker[0] != ReservationStatus.PAYMENT_RECEIVED:
                    raise ApiError(
                        status_code=409,
                        code="reservation.invalid_status_transition",
                        message="Invalid transition",
                    )
                # First call: update tracker to CONFIRMED
                status_tracker[0] = ReservationStatus.CONFIRMED

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.transition_status",
                _mock_transition,
            )

            async def _mock_rollback(
                _self: object, *, schedule_id: str, participant_count: int, capacity_source: str
            ) -> None:
                pass

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._rollback_schedule_capacity",
                _mock_rollback,
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
            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService._save_schedule_status",
                _noop,
            )

            async def _mock_notify(*args: object, **kwargs: object) -> None:
                pass

            async def _mock_generate(*args: object, **kwargs: object) -> tuple[None, None]:
                return None, None

            # NO self arg — assigned to SimpleNamespace
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

            # Mock ScheduleDocument.get (needed in try/except rollback path)
            async def _mock_sched_get(sid: str) -> SimpleNamespace:
                return SimpleNamespace(
                    id=sid, status="open", is_active=True,
                    available_slots=5, held_slots=2, reserved_slots=0,
                )

            monkeypatch.setattr(
                "app.services.reservation_service.ScheduleDocument.get",
                _mock_sched_get,
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
                f"Failures: {[(type(f).__name__, str(f)[:100]) for f in failures]}"
            )
            assert len(failures) == 4, (
                f"Expected 4 failures, got {len(failures)}"
            )

        asyncio.run(run())
