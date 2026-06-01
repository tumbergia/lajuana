import asyncio
from datetime import date
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.common.enums import PaymentStatus, ReservationStatus, ScheduleStatus, UserRole
from app.core.di import Container
from app.core.errors import ApiError
from app.documents import ReservationDocument
from app.schemas.payment_proof import PaymentProofUpdateSchema
from app.services.config_service import ConfigService
from app.services.participant_form_link_service import ParticipantFormLinkService
from app.services.payment_proof_service import PaymentProofService
from app.services.reservation_service import ALLOWED_RESERVATION_TRANSITIONS, ReservationService


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (ReservationStatus.CONTACT, ReservationStatus.QUOTED),
        (ReservationStatus.QUOTED, ReservationStatus.PRE_RESERVED),
        (ReservationStatus.QUOTED, ReservationStatus.PENDING_PAYMENT),
        (ReservationStatus.PRE_RESERVED, ReservationStatus.PENDING_PAYMENT),
        (ReservationStatus.PRE_RESERVED, ReservationStatus.EXPIRED),
        (ReservationStatus.PRE_RESERVED, ReservationStatus.CANCELLED),
        (ReservationStatus.PENDING_PAYMENT, ReservationStatus.PAYMENT_RECEIVED),
        (ReservationStatus.PAYMENT_RECEIVED, ReservationStatus.CONFIRMED),
        (ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED),
    ],
)
def test_allowed_transitions(from_status: ReservationStatus, to_status: ReservationStatus) -> None:
    assert to_status in ALLOWED_RESERVATION_TRANSITIONS[from_status]


def test_invalid_transition_raises() -> None:
    reservation = type("ReservationStub", (), {"status": ReservationStatus.CONTACT})()
    service = Container.get_instance().reservation_service
    with pytest.raises(ApiError):
        asyncio.run(service.transition_status(reservation, ReservationStatus.CONFIRMED))


class _FakePaymentProof:
    def __init__(self, reservation_id: str, status: PaymentStatus = PaymentStatus.RECEIVED) -> None:
        self.reservation_id = reservation_id
        self.status = status

    async def save(self) -> None:
        return None


class _FakePaymentProofWithRollback(_FakePaymentProof):
    def __init__(self, reservation_id: str, status: PaymentStatus = PaymentStatus.RECEIVED) -> None:
        super().__init__(reservation_id=reservation_id, status=status)
        self.saved_statuses: list[PaymentStatus] = []

    async def save(self) -> None:
        self.saved_statuses.append(self.status)
        return None


class _FakeReservation:
    def __init__(self) -> None:
        self.status = ReservationStatus.PAYMENT_RECEIVED
        self.payment_status = PaymentStatus.RECEIVED
        self.updated_by = None

    async def save(self) -> None:
        return None


class _FakeReservationSaveFailure(_FakeReservation):
    async def save(self) -> None:
        raise RuntimeError("forced reservation save error")


def test_admin_verify_success_leaves_reservation_unconfirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = PaymentProofService()
    proof = _FakePaymentProof("660000000000000000000001")
    reservation = _FakeReservation()

    async def _fake_get(_: str) -> _FakePaymentProof:
        return proof

    async def _fake_reservation_get(_: str) -> _FakeReservation:
        return reservation

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ReservationDocument, "get", _fake_reservation_get)

    payload = SimpleNamespace(
        confirmation_token="VERIFY_PAYMENT", amount=None, reference=None, note=None
    )
    asyncio.run(
        service.verify_payment(
            "proof-id",
            payload,
            actor_id=None,
            actor_role=UserRole.ADMIN,
        )
    )

    assert proof.status == PaymentStatus.VERIFIED
    assert reservation.payment_status == PaymentStatus.VERIFIED
    assert reservation.status != ReservationStatus.CONFIRMED


def test_update_rejects_status_changes_from_generic_patch(monkeypatch: pytest.MonkeyPatch) -> None:
    service = PaymentProofService()
    payload = SimpleNamespace(model_dump=lambda **_: {"status": PaymentStatus.VERIFIED})

    async def _fake_get(_: str) -> _FakePaymentProof:
        return _FakePaymentProof("660000000000000000000001")

    monkeypatch.setattr(service, "get", _fake_get)

    with pytest.raises(ApiError):
        asyncio.run(service.update("proof-id", payload))


def test_payment_proof_patch_schema_forbids_status_field() -> None:
    with pytest.raises(ValidationError):
        PaymentProofUpdateSchema(status=PaymentStatus.VERIFIED)


def test_verify_rejects_terminal_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    service = PaymentProofService()
    proof = _FakePaymentProof("660000000000000000000001", status=PaymentStatus.REJECTED)
    reservation = _FakeReservation()

    async def _fake_get(_: str) -> _FakePaymentProof:
        return proof

    async def _fake_reservation_get(_: str) -> _FakeReservation:
        return reservation

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ReservationDocument, "get", _fake_reservation_get)

    payload = SimpleNamespace(
        confirmation_token="VERIFY_PAYMENT", amount=None, reference=None, note=None
    )
    with pytest.raises(ApiError):
        asyncio.run(
            service.verify_payment(
                "proof-id",
                payload,
                actor_id=None,
                actor_role=UserRole.ADMIN,
            )
        )


def test_reject_rejects_terminal_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    service = PaymentProofService()
    proof = _FakePaymentProof("660000000000000000000001", status=PaymentStatus.VERIFIED)
    reservation = _FakeReservation()

    async def _fake_get(_: str) -> _FakePaymentProof:
        return proof

    async def _fake_reservation_get(_: str) -> _FakeReservation:
        return reservation

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ReservationDocument, "get", _fake_reservation_get)

    payload = SimpleNamespace(confirmation_token="REJECT_PAYMENT", note="invalid")
    with pytest.raises(ApiError):
        asyncio.run(
            service.reject_payment(
                "proof-id",
                payload,
                actor_id=None,
                actor_role=UserRole.ADMIN,
            )
        )


def test_verify_rolls_back_proof_when_reservation_save_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = PaymentProofService()
    proof = _FakePaymentProofWithRollback("660000000000000000000001", status=PaymentStatus.RECEIVED)
    reservation = _FakeReservationSaveFailure()

    async def _fake_get(_: str) -> _FakePaymentProofWithRollback:
        return proof

    async def _fake_reservation_get(_: str) -> _FakeReservationSaveFailure:
        return reservation

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ReservationDocument, "get", _fake_reservation_get)

    payload = SimpleNamespace(
        confirmation_token="VERIFY_PAYMENT", amount=None, reference=None, note=None
    )
    with pytest.raises(ApiError) as exc:
        asyncio.run(
            service.verify_payment(
                "proof-id",
                payload,
                actor_id=None,
                actor_role=UserRole.ADMIN,
            )
        )

    assert exc.value.status_code == 500
    assert proof.status == PaymentStatus.RECEIVED
    assert proof.saved_statuses == [PaymentStatus.VERIFIED, PaymentStatus.RECEIVED]


def test_reject_rolls_back_proof_when_reservation_save_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = PaymentProofService()
    proof = _FakePaymentProofWithRollback("660000000000000000000001", status=PaymentStatus.RECEIVED)
    reservation = _FakeReservationSaveFailure()

    async def _fake_get(_: str) -> _FakePaymentProofWithRollback:
        return proof

    async def _fake_reservation_get(_: str) -> _FakeReservationSaveFailure:
        return reservation

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ReservationDocument, "get", _fake_reservation_get)

    payload = SimpleNamespace(confirmation_token="REJECT_PAYMENT", note="invalid")
    with pytest.raises(ApiError) as exc:
        asyncio.run(
            service.reject_payment(
                "proof-id",
                payload,
                actor_id=None,
                actor_role=UserRole.ADMIN,
            )
        )

    assert exc.value.status_code == 500
    assert proof.status == PaymentStatus.RECEIVED
    assert proof.saved_statuses == [PaymentStatus.REJECTED, PaymentStatus.RECEIVED]


class _FakeSchedule:
    def __init__(self) -> None:
        self.id = "660000000000000000000100"
        self.date = date.today()
        self.is_active = True
        self.available_slots = 0
        self.status = ScheduleStatus.OPEN

    async def save(self) -> None:
        return None


class _FakeReservationConfirm:
    def __init__(self, payment_status: PaymentStatus = PaymentStatus.VERIFIED) -> None:
        self.id = "660000000000000000000001"
        self.status = ReservationStatus.PAYMENT_RECEIVED
        self.schedule_id = "660000000000000000000100"
        self.requested_date = date.today()
        self.payment_status = payment_status
        self.payment_proof_ids = ["proof-1"]
        self.participant_count = 2
        self.confirmed_at = None
        self.updated_by = None
        self.holder_phone = None

    async def save(self) -> None:
        return None


class _FakeReservationConfirmSaveFailure(_FakeReservationConfirm):
    async def save(self) -> None:
        raise RuntimeError("forced reservation save error")


def test_confirm_success_with_capacity_updates_schedule(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Container.get_instance().reservation_service
    reservation = _FakeReservationConfirm()
    schedule = _FakeSchedule()

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules(self):
        return SimpleNamespace(min_days_in_advance=0, require_payment_proof_for_confirmation=True)

    async def _fake_schedule_get(_: str):
        return schedule

    async def _fake_commit(*, schedule_id: str, participant_count: int) -> str | None:
        assert schedule_id == schedule.id
        assert participant_count == reservation.participant_count
        return "available"

    async def _noop(*args, **kwargs):
        return None

    async def _fake_generate(*args, **kwargs):
        return "token", "raw_token"

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ConfigService, "get_reservation_rules", _fake_rules)
    monkeypatch.setattr("app.services.reservation_service.ScheduleDocument.get", _fake_schedule_get)
    monkeypatch.setattr(service, "_commit_schedule_capacity", _fake_commit)
    monkeypatch.setattr(service, "ensure_date_available", _noop)
    monkeypatch.setattr(service, "_sync_day_lock_fields", _noop)
    monkeypatch.setattr(ParticipantFormLinkService, "generate", _fake_generate)

    result = asyncio.run(service.confirm_reservation(str(reservation.id)))

    assert result.status == ReservationStatus.CONFIRMED
    assert schedule.status == ScheduleStatus.FULL


def test_confirm_failure_without_capacity_keeps_status(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Container.get_instance().reservation_service
    reservation = _FakeReservationConfirm()
    original_status = reservation.status
    schedule = _FakeSchedule()

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules(self):
        return SimpleNamespace(min_days_in_advance=0, require_payment_proof_for_confirmation=True)

    async def _fake_schedule_get(_: str):
        return schedule

    async def _fake_commit(*, schedule_id: str, participant_count: int) -> str | None:
        assert schedule_id == schedule.id
        assert participant_count == reservation.participant_count
        return None

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ConfigService, "get_reservation_rules", _fake_rules)
    monkeypatch.setattr("app.services.reservation_service.ScheduleDocument.get", _fake_schedule_get)
    monkeypatch.setattr(service, "_commit_schedule_capacity", _fake_commit)
    monkeypatch.setattr(service, "ensure_date_available", _noop)

    with pytest.raises(ApiError):
        asyncio.run(service.confirm_reservation(str(reservation.id)))

    assert reservation.status == original_status


def test_confirm_failure_after_capacity_commit_rolls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    service = Container.get_instance().reservation_service
    reservation = _FakeReservationConfirm()
    schedule = _FakeSchedule()
    rollback_calls: list[tuple[str, int, str]] = []

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules(self):
        return SimpleNamespace(min_days_in_advance=0, require_payment_proof_for_confirmation=True)

    async def _fake_schedule_get(_: str):
        return schedule

    async def _fake_commit(*, schedule_id: str, participant_count: int) -> str | None:
        assert schedule_id == schedule.id
        assert participant_count == reservation.participant_count
        return "available"

    async def _fake_transition(*args, **kwargs):
        raise RuntimeError("forced transition error")

    async def _fake_rollback(
        *,
        schedule_id: str,
        participant_count: int,
        capacity_source: str,
    ) -> None:
        rollback_calls.append((schedule_id, participant_count, capacity_source))

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ConfigService, "get_reservation_rules", _fake_rules)
    monkeypatch.setattr("app.services.reservation_service.ScheduleDocument.get", _fake_schedule_get)
    monkeypatch.setattr(service, "_commit_schedule_capacity", _fake_commit)
    monkeypatch.setattr(service, "transition_status", _fake_transition)
    monkeypatch.setattr(service, "_rollback_schedule_capacity", _fake_rollback)
    monkeypatch.setattr(service, "ensure_date_available", _noop)

    with pytest.raises(RuntimeError):
        asyncio.run(service.confirm_reservation(str(reservation.id)))

    assert reservation.status == ReservationStatus.PAYMENT_RECEIVED
    assert rollback_calls == [(schedule.id, reservation.participant_count, "available")]


def test_confirm_failure_after_schedule_save_recomputes_status_after_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = Container.get_instance().reservation_service
    reservation = _FakeReservationConfirmSaveFailure()
    schedule = _FakeSchedule()
    schedule.available_slots = 0
    schedule.status = ScheduleStatus.FULL
    save_calls = 0

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules(self):
        return SimpleNamespace(min_days_in_advance=0, require_payment_proof_for_confirmation=True)

    async def _fake_schedule_get(_: str):
        return schedule

    async def _fake_commit(*, schedule_id: str, participant_count: int) -> str | None:
        assert schedule_id == schedule.id
        assert participant_count == reservation.participant_count
        return "available"

    async def _fake_rollback(
        *,
        schedule_id: str,
        participant_count: int,
        capacity_source: str,
    ) -> None:
        assert schedule_id == schedule.id
        assert participant_count == reservation.participant_count
        assert capacity_source == "available"
        schedule.available_slots += participant_count

    async def _fake_schedule_save() -> None:
        nonlocal save_calls
        save_calls += 1

    async def _noop(*args, **kwargs):
        return None

    schedule.save = _fake_schedule_save
    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ConfigService, "get_reservation_rules", _fake_rules)
    monkeypatch.setattr("app.services.reservation_service.ScheduleDocument.get", _fake_schedule_get)
    monkeypatch.setattr(service, "_commit_schedule_capacity", _fake_commit)
    monkeypatch.setattr(service, "_rollback_schedule_capacity", _fake_rollback)
    monkeypatch.setattr(service, "ensure_date_available", _noop)
    monkeypatch.setattr(service, "_sync_day_lock_fields", _noop)

    with pytest.raises(RuntimeError, match="forced reservation save error"):
        asyncio.run(service.confirm_reservation(str(reservation.id)))

    assert schedule.available_slots == reservation.participant_count
    assert schedule.status == ScheduleStatus.OPEN
    assert save_calls == 2


# ---------------------------------------------------------------------------
# NO-SHOW transition tests (COMPLETED without payment_received)
# ---------------------------------------------------------------------------


class TestNoShowTransition:
    """NO-SHOW: marking a reservation as COMPLETED without proper payment.

    Risk: completing a reservation without payment verification can lead
    to revenue loss. The status COMPLETED is terminal — no further transitions
    allowed.
    """

    def test_confirmed_to_completed_is_valid_transition(self) -> None:
        """CONFIRMED → COMPLETED should be in the allowed transitions."""
        assert ReservationStatus.COMPLETED in ALLOWED_RESERVATION_TRANSITIONS[
            ReservationStatus.CONFIRMED
        ]

    def test_completed_is_terminal_no_outgoing(self) -> None:
        """COMPLETED should have no outgoing transitions (terminal state)."""
        assert ALLOWED_RESERVATION_TRANSITIONS[ReservationStatus.COMPLETED] == set()

    def test_completed_cannot_transition_to_any_state(self) -> None:
        """Attempting any transition from COMPLETED should raise ApiError."""
        reservation = type(
            "ReservationStub",
            (),
            {"status": ReservationStatus.COMPLETED},
        )()

        # Build service with minimal mock deps
        async def _noop(*args: object, **kwargs: object) -> None:
            pass

        from app.services.reservation_service import ReservationService

        svc = ReservationService(
            notification_service=SimpleNamespace(
                enqueue_reservation_created=_noop,
                enqueue_payment_received=_noop,
                enqueue_post_service=_noop,
            ),
            form_link_service=SimpleNamespace(generate=_noop),
            config_service=SimpleNamespace(get_reservation_rules=_noop),
        )

        for target in [
            ReservationStatus.CONTACT,
            ReservationStatus.QUOTED,
            ReservationStatus.PRE_RESERVED,
            ReservationStatus.PENDING_PAYMENT,
            ReservationStatus.PAYMENT_RECEIVED,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CANCELLED,
            ReservationStatus.EXPIRED,
        ]:
            with pytest.raises(ApiError):
                asyncio.run(
                    svc.transition_status(reservation, target)
                )

    def test_set_status_to_completed_from_confirmed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """set_status to COMPLETED should succeed from CONFIRMED."""

        async def _mock_save() -> None:
            pass

        res = SimpleNamespace(
            id="660000000000000000000001",
            status=ReservationStatus.CONFIRMED,
            payment_status=PaymentStatus.VERIFIED,
            updated_by=None,
            blocks_day=False,
            availability_lock_key=None,
            requested_date=date(2026, 7, 15),
            save=_mock_save,
        )

        async def run() -> None:
            # Mock ReservationService.get
            async def _mock_get(_self: object, rid: str, **kwargs: object) -> object:
                return res

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            # Mock notification_service.enqueue_post_service
            async def _mock_notify(*args: object, **kwargs: object) -> None:
                pass

            # Mock _sync_day_lock_fields
            async def _mock_sync(*args: object, **kwargs: object) -> None:
                pass

            from app.services.reservation_service import ReservationService

            svc = ReservationService(
                notification_service=SimpleNamespace(
                    enqueue_post_service=_mock_notify,
                ),
                form_link_service=SimpleNamespace(generate=_mock_notify),
                config_service=SimpleNamespace(get_reservation_rules=_mock_notify),
            )
            monkeypatch.setattr(svc, "_sync_day_lock_fields", _mock_sync)

            result = await svc.set_status(
                reservation_id="660000000000000000000001",
                target_status=ReservationStatus.COMPLETED,
                actor_id="660000000000000000000050",
            )

            assert result.status == ReservationStatus.COMPLETED

        asyncio.run(run())

    def test_set_status_to_completed_from_cancelled_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CANCELLED → COMPLETED is an invalid transition."""

        async def _mock_save() -> None:
            pass

        res = SimpleNamespace(
            id="660000000000000000000001",
            status=ReservationStatus.CANCELLED,
            payment_status=PaymentStatus.PENDING,
            updated_by=None,
            blocks_day=False,
            availability_lock_key=None,
            save=_mock_save,
        )

        async def run() -> None:
            async def _mock_get(_self: object, rid: str, **kwargs: object) -> object:
                return res

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            async def _mock_sync(*args: object, **kwargs: object) -> None:
                pass

            from app.services.reservation_service import ReservationService

            svc = ReservationService(
                notification_service=SimpleNamespace(),
                form_link_service=SimpleNamespace(),
                config_service=SimpleNamespace(),
            )
            monkeypatch.setattr(svc, "_sync_day_lock_fields", _mock_sync)

            with pytest.raises(ApiError) as exc:
                await svc.set_status(
                    reservation_id="660000000000000000000001",
                    target_status=ReservationStatus.COMPLETED,
                    actor_id="660000000000000000000050",
                )

            assert exc.value.status_code == 409

        asyncio.run(run())

    def test_set_status_to_completed_from_pre_reserved_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PRE_RESERVED → COMPLETED is an invalid transition (skips confirmation)."""

        async def _mock_save() -> None:
            pass

        res = SimpleNamespace(
            id="660000000000000000000001",
            status=ReservationStatus.PRE_RESERVED,
            payment_status=PaymentStatus.PENDING,
            updated_by=None,
            blocks_day=False,
            availability_lock_key=None,
            save=_mock_save,
        )

        async def run() -> None:
            async def _mock_get(_self: object, rid: str, **kwargs: object) -> object:
                return res

            monkeypatch.setattr(
                "app.services.reservation_service.ReservationService.get",
                _mock_get,
            )

            async def _mock_sync(*args: object, **kwargs: object) -> None:
                pass

            from app.services.reservation_service import ReservationService

            svc = ReservationService(
                notification_service=SimpleNamespace(),
                form_link_service=SimpleNamespace(),
                config_service=SimpleNamespace(),
            )
            monkeypatch.setattr(svc, "_sync_day_lock_fields", _mock_sync)

            with pytest.raises(ApiError) as exc:
                await svc.set_status(
                    reservation_id="660000000000000000000001",
                    target_status=ReservationStatus.COMPLETED,
                    actor_id="660000000000000000000050",
                )

            assert exc.value.status_code == 409

        asyncio.run(run())
