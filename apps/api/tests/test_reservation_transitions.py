import asyncio
from datetime import date
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.common.enums import PaymentStatus, ReservationStatus, ScheduleStatus, UserRole
from app.core.errors import ApiError
from app.documents import ReservationDocument
from app.services.payment_proof_service import PaymentProofService
from app.services.reservation_service import ALLOWED_RESERVATION_TRANSITIONS, ReservationService
from app.schemas.payment_proof import PaymentProofUpdateSchema


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
    service = ReservationService()
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


def test_admin_verify_success_leaves_reservation_unconfirmed(monkeypatch: pytest.MonkeyPatch) -> None:
    service = PaymentProofService()
    proof = _FakePaymentProof("660000000000000000000001")
    reservation = _FakeReservation()

    async def _fake_get(_: str) -> _FakePaymentProof:
        return proof

    async def _fake_reservation_get(_: str) -> _FakeReservation:
        return reservation

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ReservationDocument, "get", _fake_reservation_get)

    payload = SimpleNamespace(confirmation_token="VERIFY_PAYMENT", amount=None, reference=None, note=None)
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

    payload = SimpleNamespace(confirmation_token="VERIFY_PAYMENT", amount=None, reference=None, note=None)
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


def test_verify_rolls_back_proof_when_reservation_save_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    service = PaymentProofService()
    proof = _FakePaymentProofWithRollback("660000000000000000000001", status=PaymentStatus.RECEIVED)
    reservation = _FakeReservationSaveFailure()

    async def _fake_get(_: str) -> _FakePaymentProofWithRollback:
        return proof

    async def _fake_reservation_get(_: str) -> _FakeReservationSaveFailure:
        return reservation

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(ReservationDocument, "get", _fake_reservation_get)

    payload = SimpleNamespace(confirmation_token="VERIFY_PAYMENT", amount=None, reference=None, note=None)
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


def test_reject_rolls_back_proof_when_reservation_save_fails(monkeypatch: pytest.MonkeyPatch) -> None:
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

    async def save(self) -> None:
        return None


class _FakeReservationConfirmSaveFailure(_FakeReservationConfirm):
    async def save(self) -> None:
        raise RuntimeError("forced reservation save error")


def test_confirm_success_with_capacity_updates_schedule(monkeypatch: pytest.MonkeyPatch) -> None:
    service = ReservationService()
    reservation = _FakeReservationConfirm()
    schedule = _FakeSchedule()

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules():
        return SimpleNamespace(min_days_in_advance=0, require_payment_proof_for_confirmation=True)

    async def _fake_schedule_get(_: str):
        return schedule

    async def _fake_commit(*, schedule_id: str, participant_count: int) -> str | None:
        assert schedule_id == schedule.id
        assert participant_count == reservation.participant_count
        return "available"

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(service, "get", _fake_get)
    monkeypatch.setattr(service.config_service, "get_reservation_rules", _fake_rules)
    monkeypatch.setattr("app.services.reservation_service.ScheduleDocument.get", _fake_schedule_get)
    monkeypatch.setattr(service, "_commit_schedule_capacity", _fake_commit)
    monkeypatch.setattr(service, "ensure_date_available", _noop)
    monkeypatch.setattr(service, "_sync_day_lock_fields", _noop)

    result = asyncio.run(service.confirm_reservation(str(reservation.id)))

    assert result.status == ReservationStatus.CONFIRMED
    assert schedule.status == ScheduleStatus.FULL


def test_confirm_failure_without_capacity_keeps_status(monkeypatch: pytest.MonkeyPatch) -> None:
    service = ReservationService()
    reservation = _FakeReservationConfirm()
    original_status = reservation.status
    schedule = _FakeSchedule()

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules():
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
    monkeypatch.setattr(service.config_service, "get_reservation_rules", _fake_rules)
    monkeypatch.setattr("app.services.reservation_service.ScheduleDocument.get", _fake_schedule_get)
    monkeypatch.setattr(service, "_commit_schedule_capacity", _fake_commit)
    monkeypatch.setattr(service, "ensure_date_available", _noop)

    with pytest.raises(ApiError):
        asyncio.run(service.confirm_reservation(str(reservation.id)))

    assert reservation.status == original_status


def test_confirm_failure_after_capacity_commit_rolls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    service = ReservationService()
    reservation = _FakeReservationConfirm()
    schedule = _FakeSchedule()
    rollback_calls: list[tuple[str, int, str]] = []

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules():
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
    monkeypatch.setattr(service.config_service, "get_reservation_rules", _fake_rules)
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
    service = ReservationService()
    reservation = _FakeReservationConfirmSaveFailure()
    schedule = _FakeSchedule()
    schedule.available_slots = 0
    schedule.status = ScheduleStatus.FULL
    save_calls = 0

    async def _fake_get(_: str):
        return reservation

    async def _fake_rules():
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
    monkeypatch.setattr(service.config_service, "get_reservation_rules", _fake_rules)
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
