"""P1: AssignmentService — create, get, update, finalize, validate with full domain validation.

Risk: Incorrect assignment logic can lead to equine overload, rider safety issues,
duplicate bookings, and operational chaos. Every validation path must be tested.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.common.enums import (
    AssignmentSource,
    AssignmentStatus,
    ExperienceLevel,
    ReservationStatus,
)
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.schemas.assignment import AssignmentCreateSchema, AssignmentUpdateSchema
from app.services.assignment_service import AssignmentService

FAKE_ID = "660000000000000000000001"
FAKE_ID_2 = "660000000000000000000002"
FAKE_ID_3 = "660000000000000000000003"
FAKE_ACTOR_ID = "660000000000000000000099"

# Sentinel to distinguish "not provided" from "explicitly None"
_UNSET = object()


# ── Fake factory helpers ──


def make_fake_reservation(**overrides: object) -> SimpleNamespace:
    defaults = dict(
        id=FAKE_ID,
        status=ReservationStatus.CONFIRMED,
        participant_ids=[FAKE_ID],
        requested_date=date(2026, 6, 15),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_fake_participant(**overrides: object) -> SimpleNamespace:
    defaults = dict(
        id=FAKE_ID,
        reservation_id=FAKE_ID,
        first_name="Juan",
        last_name="Pérez",
        birth_date=date(1990, 1, 1),
        weight_kg=Decimal("70"),
        height_cm=Decimal("170"),
        experience_level=ExperienceLevel.INTERMEDIATE,
        is_completed=True,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_fake_equine(**overrides: object) -> SimpleNamespace:
    defaults = dict(
        id=FAKE_ID,
        name="Pegaso",
        is_active=True,
        is_available=True,
        max_rider_weight_kg=Decimal("100"),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_fake_saddle(**overrides: object) -> SimpleNamespace:
    defaults = dict(
        id=FAKE_ID,
        code="S-001",
        name="Silla Inglesa",
        is_available=True,
        deleted_at=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class FakeFindQuery:
    """Reusable fake for Beanie find().skip().limit().to_list() chains."""

    def __init__(self, items: list) -> None:
        self._items = items

    def skip(self, n: int) -> FakeFindQuery:
        return self

    def limit(self, n: int) -> FakeFindQuery:
        return self

    async def to_list(self) -> list:
        return self._items


# ── Configurable AssignmentDocument stand-in ──


class FakeAssignmentDocument:
    """Replaces AssignmentDocument in the service module for testing.

    Each test configures class-level attrs (find_one, get, find) via
    monkeypatch before calling the service method.
    """

    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._insert_called = False
        self._save_called = False

    async def insert(self) -> None:
        self._insert_called = True
        if not hasattr(self, "id") or self.id is None:
            self.id = FAKE_ID

    async def save(self) -> None:
        self._save_called = True


# ======================================================================
# CREATE
# ======================================================================


class TestCreate:
    """AssignmentService.create — full validation chain."""

    def _patch_base(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        reservation: object = _UNSET,
        participant: object = _UNSET,
        equine: object = _UNSET,
        saddle: object = _UNSET,
        find_one_result: object = None,
        find_results: list | None = None,
    ) -> type[FakeAssignmentDocument]:
        """Set up common mocks for create() tests.

        Use keyword args to override specific fakes. Pass a kwarg as ``None``
        explicitly to simulate a "not found" case (e.g. reservation=None).

        Returns the FakeAssignmentDocument class so tests can override
        classmethods further.
        """
        if reservation is _UNSET:
            reservation = make_fake_reservation()
        if participant is _UNSET:
            participant = make_fake_participant()
        if equine is _UNSET:
            equine = make_fake_equine()
        if saddle is _UNSET:
            saddle = make_fake_saddle()
        find_results = find_results or []

        async def _mock_get_reservation(_rid: str) -> object | None:
            return reservation

        async def _mock_get_participant(_pid: str) -> object | None:
            return participant

        async def _mock_get_equine(_eid: str) -> object | None:
            return equine

        async def _mock_get_saddle(_sid: str) -> object | None:
            # Return a saddle with the requested ID AND the same properties as
            # the outer saddle (is_available, deleted_at, etc.)
            if saddle is None:
                return None
            return make_fake_saddle(
                id=_sid,
                is_available=getattr(saddle, "is_available", True),
                deleted_at=getattr(saddle, "deleted_at", None),
            )

        async def _mock_find_one(_query: dict) -> object | None:
            return find_one_result

        monkeypatch.setattr(
            "app.services.assignment_service.ReservationDocument.get",
            _mock_get_reservation,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.ParticipantDocument.get",
            _mock_get_participant,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.EquineDocument.get",
            _mock_get_equine,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.SaddleDocument.get",
            _mock_get_saddle,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument",
            FakeAssignmentDocument,
        )
        FakeAssignmentDocument.find_one = _mock_find_one  # type: ignore[attr-defined]

        def _mock_find(_query: dict) -> FakeFindQuery:
            return FakeFindQuery(find_results)

        FakeAssignmentDocument.find = _mock_find  # type: ignore[attr-defined]

        return FakeAssignmentDocument

    # ── Success path ──

    def test_create_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Full valid chain creates a CONFIRMED assignment with no flags."""
        self._patch_base(monkeypatch)

        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
                notes="Sin notas.",
            )
            result = await service.create(payload, actor_id=FAKE_ACTOR_ID)

            assert result.status == AssignmentStatus.CONFIRMED
            assert result.safety_flags == []
            assert result.validation_warnings == []
            assert result.assigned_by_user_id == FAKE_ACTOR_ID
            assert result.source == AssignmentSource.MANUAL_ADMIN
            assert result.is_active is True
            assert result._insert_called is True

        asyncio.run(run())

    def test_create_with_saddle(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Providing a valid saddle_id should attach it."""
        self._patch_base(monkeypatch)  # saddle defaults to a valid saddle

        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
                saddle_id=FAKE_ID_2,
            )
            result = await service.create(payload, actor_id=FAKE_ACTOR_ID)
            # _mock_get_saddle returns a saddle whose id matches the requested id
            assert result.saddle_id == FAKE_ID_2

        asyncio.run(run())

    def test_create_no_actor_sets_system_source(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When actor_id is None, source must be SYSTEM_SUGGESTED."""
        self._patch_base(monkeypatch)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            result = await service.create(payload, actor_id=None)
            assert result.source == AssignmentSource.SYSTEM_SUGGESTED
            assert result.assigned_by_user_id is None

        asyncio.run(run())

    # ── Error: reservation ──

    def test_create_reservation_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reservation.get returns None → RESERVATION_NOT_FOUND."""
        self._patch_base(monkeypatch, reservation=None)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.RESERVATION_NOT_FOUND

        asyncio.run(run())

    def test_create_reservation_not_confirmed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reservation status != CONFIRMED → ASSIGNMENT_RESERVATION_NOT_CONFIRMED."""
        self._patch_base(
            monkeypatch,
            reservation=make_fake_reservation(status=ReservationStatus.QUOTED),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_RESERVATION_NOT_CONFIRMED

        asyncio.run(run())

    # ── Error: participant ──

    def test_create_participant_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Participant.get returns None → PARTICIPANT_NOT_FOUND."""
        self._patch_base(monkeypatch, participant=None)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.PARTICIPANT_NOT_FOUND

        asyncio.run(run())

    def test_create_participant_not_in_reservation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Participant.reservation_id differs → ASSIGNMENT_PARTICIPANT_NOT_IN_RESERVATION."""
        self._patch_base(
            monkeypatch,
            participant=make_fake_participant(reservation_id=FAKE_ID_2),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 400
            assert exc.value.code == ErrorCode.ASSIGNMENT_PARTICIPANT_NOT_IN_RESERVATION

        asyncio.run(run())

    def test_create_participant_missing_weight(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """weight_kg=None → ASSIGNMENT_PARTICIPANT_MISSING_REQUIRED_DATA."""
        self._patch_base(
            monkeypatch,
            participant=make_fake_participant(weight_kg=None),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_PARTICIPANT_MISSING_REQUIRED_DATA
            assert "weight_kg" in str(exc.value.details.get("missing_fields", []))

        asyncio.run(run())

    def test_create_participant_missing_birth_date(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """birth_date=None → ASSIGNMENT_PARTICIPANT_MISSING_REQUIRED_DATA."""
        self._patch_base(
            monkeypatch,
            participant=make_fake_participant(birth_date=None),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert "birth_date" in str(exc.value.details.get("missing_fields", []))

        asyncio.run(run())

    def test_create_participant_missing_experience_level(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """experience_level=None → ASSIGNMENT_PARTICIPANT_MISSING_REQUIRED_DATA."""
        self._patch_base(
            monkeypatch,
            participant=make_fake_participant(experience_level=None),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert "experience_level" in str(exc.value.details.get("missing_fields", []))

        asyncio.run(run())

    # ── Error: equine ──

    def test_create_equine_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Equine.get returns None → EQUINE_NOT_FOUND."""
        self._patch_base(monkeypatch, equine=None)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.EQUINE_NOT_FOUND

        asyncio.run(run())

    def test_create_equine_not_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """is_available=False → ASSIGNMENT_EQUINE_NOT_AVAILABLE."""
        self._patch_base(
            monkeypatch,
            equine=make_fake_equine(is_available=False),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_EQUINE_NOT_AVAILABLE

        asyncio.run(run())

    def test_create_equine_already_assigned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Equine already in an active assignment for this reservation."""
        self._patch_base(
            monkeypatch,
            find_one_result=SimpleNamespace(id=FAKE_ID_3),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_EQUINE_ALREADY_ASSIGNED

        asyncio.run(run())

    # ── Error: saddle ──

    def test_create_saddle_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Saddle.get returns None → SADDLE_NOT_FOUND."""
        self._patch_base(monkeypatch, saddle=None)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
                saddle_id=FAKE_ID_2,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.SADDLE_NOT_FOUND

        asyncio.run(run())

    def test_create_saddle_not_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """saddle.is_available=False → ASSIGNMENT_SADDLE_NOT_AVAILABLE."""
        self._patch_base(
            monkeypatch,
            saddle=make_fake_saddle(is_available=False),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
                saddle_id=FAKE_ID_2,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_SADDLE_NOT_AVAILABLE

        asyncio.run(run())

    # ── Error: rider weight ──

    def test_create_rider_weight_exceeds_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Rider weight exceeds equine max_rider_weight_kg → error."""
        self._patch_base(
            monkeypatch,
            equine=make_fake_equine(max_rider_weight_kg=Decimal("50")),
            participant=make_fake_participant(weight_kg=Decimal("70")),
        )
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_RIDER_WEIGHT_EXCEEDS_LIMIT

        asyncio.run(run())

    # ── Error: duplicate participant ──

    def test_create_duplicate_participant(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Participant already has active assignment for this reservation."""
        self._patch_base(monkeypatch, find_one_result=None)

        # Override find_one: first call (equine dup check) → None,
        # second call (_validate_no_active_assignment) → existing doc
        # (saddle dup check is skipped since payload has no saddle_id)
        call_count = 0

        async def _mock_find_one(query: dict) -> object | None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None
            return SimpleNamespace(id=FAKE_ID_3)

        FakeAssignmentDocument.find_one = _mock_find_one  # type: ignore[attr-defined]

        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_DUPLICATE_FOR_PARTICIPANT

        asyncio.run(run())

    # ── Safety flags & warnings ──

    def test_create_child_rider_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Participant birth_date < 12 years → child_rider safety_flag."""
        child = make_fake_participant(birth_date=date(2015, 6, 15))  # age 10
        self._patch_base(monkeypatch, participant=child)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            result = await service.create(payload)
            assert "child_rider" in result.safety_flags
            assert any("menor" in w.lower() for w in result.validation_warnings)

        asyncio.run(run())

    def test_create_senior_rider_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Participant birth_date > 65 years → senior_rider safety_flag."""
        senior = make_fake_participant(birth_date=date(1960, 1, 1))  # age 66
        self._patch_base(monkeypatch, participant=senior)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            result = await service.create(payload)
            assert "senior_rider" in result.safety_flags
            assert any("mayor" in w.lower() for w in result.validation_warnings)

        asyncio.run(run())

    def test_create_missing_max_weight_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Equine has no max_rider_weight_kg → warning added."""
        unwarned_equine = make_fake_equine(max_rider_weight_kg=None)
        self._patch_base(monkeypatch, equine=unwarned_equine)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentCreateSchema(
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_ID,
            )
            result = await service.create(payload)
            assert "límite de peso" in str(result.validation_warnings).lower()

        asyncio.run(run())


# ======================================================================
# GET
# ======================================================================


class TestGet:
    """AssignmentService.get — retrieval by ID."""

    def test_get_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Existing assignment returns the document."""
        fake_doc = SimpleNamespace(id=FAKE_ID, status=AssignmentStatus.CONFIRMED)

        async def _mock_get(_aid: str) -> object:
            return fake_doc

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )

        service = AssignmentService()

        async def run() -> None:
            result = await service.get(FAKE_ID)
            assert result is not None
            assert result.id == FAKE_ID

        asyncio.run(run())

    def test_get_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Non-existent assignment → ASSIGNMENT_NOT_FOUND."""

        async def _mock_get(_aid: str) -> None:
            return None

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )

        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.get(FAKE_ID_3)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.ASSIGNMENT_NOT_FOUND

        asyncio.run(run())


# ======================================================================
# UPDATE
# ======================================================================


class TestUpdate:
    """AssignmentService.update — field updates with validation."""

    def _patch_update_base(
        self,
        monkeypatch: pytest.MonkeyPatch,
        **overrides: object,
    ) -> SimpleNamespace:
        """Set up a fake assignment document with save tracking."""
        defaults = dict(
            id=FAKE_ID,
            version=1,
            reservation_id=FAKE_ID,
            participant_id=FAKE_ID,
            equine_id=FAKE_ID,
            saddle_id=None,
            status=AssignmentStatus.CONFIRMED,
            is_active=True,
            validation_warnings=[],
            _save_called=False,
        )
        defaults.update(overrides)
        doc = SimpleNamespace(**defaults)

        async def _mock_save() -> None:
            doc._save_called = True

        doc.save = _mock_save  # type: ignore[attr-defined]

        async def _mock_get(_aid: str) -> SimpleNamespace:
            return doc

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )

        async def _mock_get_equine(_eid: str) -> SimpleNamespace | None:
            if _eid == FAKE_ID_2:
                return make_fake_equine(id=FAKE_ID_2, name="Relámpago")
            return make_fake_equine()

        async def _mock_get_saddle(_sid: str) -> SimpleNamespace | None:
            return make_fake_saddle(id=_sid, code="S-002")

        async def _mock_find_one(_query: dict) -> None:
            return None

        monkeypatch.setattr(
            "app.services.assignment_service.EquineDocument.get",
            _mock_get_equine,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.SaddleDocument.get",
            _mock_get_saddle,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.find_one",
            _mock_find_one,
        )

        return doc

    def test_update_equine_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Changing equine_id should update the document."""
        self._patch_update_base(monkeypatch)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentUpdateSchema(equine_id=FAKE_ID_2)
            result = await service.update(FAKE_ID, payload)
            assert result.equine_id == FAKE_ID_2
            assert result._save_called is True

        asyncio.run(run())

    def test_update_saddle_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Changing saddle_id to a valid saddle should update it."""
        self._patch_update_base(monkeypatch)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentUpdateSchema(saddle_id=FAKE_ID_2)
            result = await service.update(FAKE_ID, payload)
            assert result.saddle_id == FAKE_ID_2
            assert result._save_called is True

        asyncio.run(run())

    def test_update_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Changing status should work."""
        self._patch_update_base(monkeypatch)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentUpdateSchema(status=AssignmentStatus.DRAFT)
            result = await service.update(FAKE_ID, payload)
            assert result.status == AssignmentStatus.DRAFT
            assert result._save_called is True

        asyncio.run(run())

    def test_update_notes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Updating only notes should work."""
        self._patch_update_base(monkeypatch)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentUpdateSchema(notes="Nota actualizada.")
            result = await service.update(FAKE_ID, payload)
            assert result.notes == "Nota actualizada."
            assert result._save_called is True

        asyncio.run(run())

    def test_update_final_blocks_equine_change(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FINAL assignment cannot change equine_id."""
        self._patch_update_base(monkeypatch, status=AssignmentStatus.FINAL)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentUpdateSchema(equine_id=FAKE_ID_2)
            with pytest.raises(ApiError) as exc:
                await service.update(FAKE_ID, payload)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_INVALID_PRIORITY

        asyncio.run(run())

    def test_update_final_allows_notes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FINAL assignment can still update notes."""
        self._patch_update_base(monkeypatch, status=AssignmentStatus.FINAL)
        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentUpdateSchema(notes="Nota en finalizado.")
            result = await service.update(FAKE_ID, payload)
            assert result.notes == "Nota en finalizado."
            assert result._save_called is True

        asyncio.run(run())

    def test_update_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Updating a non-existent assignment raises 404."""

        async def _mock_get(_aid: str) -> None:
            return None

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )

        service = AssignmentService()

        async def run() -> None:
            payload = AssignmentUpdateSchema(notes="Nope.")
            with pytest.raises(ApiError) as exc:
                await service.update(FAKE_ID_3, payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.ASSIGNMENT_NOT_FOUND

        asyncio.run(run())


# ======================================================================
# FINALIZE
# ======================================================================


class TestFinalize:
    """AssignmentService.finalize — lock assignment as FINAL."""

    def _patch_finalize_base(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: AssignmentStatus = AssignmentStatus.CONFIRMED,
    ) -> SimpleNamespace:
        doc = SimpleNamespace(
            id=FAKE_ID,
            reservation_id=FAKE_ID,
            status=status,
            finalized_by_user_id=None,
            finalized_at=None,
            _save_called=False,
        )

        async def _mock_save() -> None:
            doc._save_called = True

        doc.save = _mock_save  # type: ignore[attr-defined]

        async def _mock_get(_aid: str) -> SimpleNamespace:
            return doc

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )
        return doc

    def test_finalize_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Confirming a CONFIRMED assignment sets status=FINAL and timestamps."""
        self._patch_finalize_base(monkeypatch, status=AssignmentStatus.CONFIRMED)
        service = AssignmentService()

        async def run() -> None:
            result = await service.finalize(FAKE_ID, actor_id=FAKE_ACTOR_ID)
            assert result.status == AssignmentStatus.FINAL
            assert result.finalized_by_user_id == FAKE_ACTOR_ID
            assert result.finalized_at is not None
            assert result._save_called is True

        asyncio.run(run())

    def test_finalize_not_confirmed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Assignment not CONFIRMED → error."""
        self._patch_finalize_base(monkeypatch, status=AssignmentStatus.DRAFT)
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.finalize(FAKE_ID)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_RESERVATION_NOT_CONFIRMED

        asyncio.run(run())

    def test_finalize_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Non-existent assignment → 404."""

        async def _mock_get(_aid: str) -> None:
            return None

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )

        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.finalize(FAKE_ID_3)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.ASSIGNMENT_NOT_FOUND

        asyncio.run(run())


class TestUnfinalize:
    """AssignmentService.unfinalize — reopen FINAL assignment."""

    def _patch_unfinalize_base(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: AssignmentStatus = AssignmentStatus.FINAL,
    ) -> SimpleNamespace:
        doc = SimpleNamespace(
            id=FAKE_ID,
            reservation_id=FAKE_ID,
            status=status,
            finalized_by_user_id=FAKE_ACTOR_ID,
            finalized_at=datetime(2026, 1, 1, tzinfo=UTC),
            _save_called=False,
        )

        async def _mock_save() -> None:
            doc._save_called = True

        doc.save = _mock_save  # type: ignore[attr-defined]

        async def _mock_get(_aid: str) -> SimpleNamespace:
            return doc

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )
        return doc

    def test_unfinalize_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_unfinalize_base(monkeypatch, status=AssignmentStatus.FINAL)
        service = AssignmentService()

        async def run() -> None:
            result = await service.unfinalize(FAKE_ID, actor_id=FAKE_ACTOR_ID)
            assert result.status == AssignmentStatus.CONFIRMED
            assert result.finalized_by_user_id is None
            assert result.finalized_at is None
            assert result._save_called is True

        asyncio.run(run())

    def test_unfinalize_not_final(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_unfinalize_base(monkeypatch, status=AssignmentStatus.CONFIRMED)
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.unfinalize(FAKE_ID)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_INVALID_PRIORITY

        asyncio.run(run())


class TestRemoveAssignment:
    """AssignmentService.remove — cancel assignment from board."""

    def _patch_remove_base(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: AssignmentStatus = AssignmentStatus.CONFIRMED,
    ) -> SimpleNamespace:
        doc = SimpleNamespace(
            id=FAKE_ID,
            reservation_id=FAKE_ID,
            status=status,
            is_active=True,
            _save_called=False,
        )

        async def _mock_save() -> None:
            doc._save_called = True

        doc.save = _mock_save  # type: ignore[attr-defined]

        async def _mock_get(_aid: str) -> SimpleNamespace:
            return doc

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.get",
            _mock_get,
        )
        return doc

    def test_remove_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_remove_base(monkeypatch, status=AssignmentStatus.CONFIRMED)
        service = AssignmentService()

        async def run() -> None:
            result = await service.remove(FAKE_ID, actor_id=FAKE_ACTOR_ID)
            assert result.status == AssignmentStatus.CANCELLED
            assert result.is_active is False
            assert result._save_called is True

        asyncio.run(run())

    def test_remove_final_not_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_remove_base(monkeypatch, status=AssignmentStatus.FINAL)
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.remove(FAKE_ID)
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.ASSIGNMENT_INVALID_PRIORITY

        asyncio.run(run())


# ======================================================================
# VALIDATE ASSIGNMENT CANDIDATE
# ======================================================================


class TestValidateAssignmentCandidate:
    """AssignmentService.validate_assignment_candidate — pre-flight checks."""

    @staticmethod
    def _make_fake_doc_class(get_fn) -> type:
        """Create a minimal fake Document class with a given async ``get``."""

        class _FakeDoc:
            get = get_fn  # type: ignore[assignment]

        return _FakeDoc

    def _patch_validate_base(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        reservation: object = _UNSET,
        participant: object = _UNSET,
        equine: object = _UNSET,
        saddle: object = _UNSET,
    ) -> None:
        if reservation is _UNSET:
            reservation = make_fake_reservation()
        if participant is _UNSET:
            participant = make_fake_participant()
        if equine is _UNSET:
            equine = make_fake_equine()
        if saddle is _UNSET:
            saddle = make_fake_saddle()

        async def _mock_get_reservation(_rid: str) -> object | None:
            return reservation

        async def _mock_get_participant(_pid: str) -> object | None:
            return participant

        async def _mock_get_equine(_eid: str) -> object | None:
            return equine

        async def _mock_get_saddle(_sid: str) -> object | None:
            if saddle is None:
                return None
            return make_fake_saddle(
                id=_sid,
                is_available=getattr(saddle, "is_available", True),
                deleted_at=getattr(saddle, "deleted_at", None),
            )

        # Replace the entire class reference — avoids descriptor/gate issues
        # with monkeypatching classmethods on Beanie Documents.
        monkeypatch.setattr(
            "app.services.assignment_service.ReservationDocument",
            self._make_fake_doc_class(_mock_get_reservation),
        )
        monkeypatch.setattr(
            "app.services.assignment_service.ParticipantDocument",
            self._make_fake_doc_class(_mock_get_participant),
        )
        monkeypatch.setattr(
            "app.services.assignment_service.EquineDocument",
            self._make_fake_doc_class(_mock_get_equine),
        )
        monkeypatch.setattr(
            "app.services.assignment_service.SaddleDocument",
            self._make_fake_doc_class(_mock_get_saddle),
        )

        monkeypatch.setattr(
            "app.services.assignment_service.ParticipantDocument.get",
            _mock_get_participant,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.ParticipantDocument.get",
            _mock_get_participant,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.EquineDocument.get",
            _mock_get_equine,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.SaddleDocument.get",
            _mock_get_saddle,
        )

        # _validate_and_prepare (dry_run path) runs extra DB checks:
        # _validate_equine_not_duplicate → AssignmentDocument.find_one
        # _validate_no_active_assignment → AssignmentDocument.find
        async def _mock_find_one(_query: object) -> None:
            return None

        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.find_one",
            _mock_find_one,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.find",
            lambda _q: FakeFindQuery([]),
        )

    def test_validate_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Valid candidate returns empty safety flags and warnings."""
        self._patch_validate_base(monkeypatch)
        service = AssignmentService()

        async def run() -> None:
            flags, warnings = await service.validate_assignment_candidate(
                FAKE_ID,
                FAKE_ID,
                FAKE_ID,
            )
            assert flags == []
            assert warnings == []

        asyncio.run(run())

    def test_validate_with_saddle(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Saddle_id provided and valid → no errors."""
        self._patch_validate_base(monkeypatch)  # saddle defaults to valid
        service = AssignmentService()

        async def run() -> None:
            flags, warnings = await service.validate_assignment_candidate(
                FAKE_ID,
                FAKE_ID,
                FAKE_ID,
                saddle_id=FAKE_ID_2,
            )
            assert flags == []
            assert warnings == []

        asyncio.run(run())

    def test_validate_reservation_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_validate_base(monkeypatch, reservation=None)
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.validate_assignment_candidate(FAKE_ID, FAKE_ID, FAKE_ID)
            assert exc.value.code == ErrorCode.RESERVATION_NOT_FOUND

        asyncio.run(run())

    def test_validate_participant_not_belongs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_validate_base(
            monkeypatch,
            participant=make_fake_participant(reservation_id=FAKE_ID_2),
        )
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.validate_assignment_candidate(FAKE_ID, FAKE_ID, FAKE_ID)
            assert exc.value.code == ErrorCode.ASSIGNMENT_PARTICIPANT_NOT_IN_RESERVATION

        asyncio.run(run())

    def test_validate_equine_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_validate_base(monkeypatch, equine=None)
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.validate_assignment_candidate(FAKE_ID, FAKE_ID, FAKE_ID)
            assert exc.value.code == ErrorCode.EQUINE_NOT_FOUND

        asyncio.run(run())

    def test_validate_saddle_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_validate_base(monkeypatch, saddle=None)
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.validate_assignment_candidate(
                    FAKE_ID,
                    FAKE_ID,
                    FAKE_ID,
                    saddle_id=FAKE_ID_2,
                )
            assert exc.value.code == ErrorCode.SADDLE_NOT_FOUND

        asyncio.run(run())

    def test_validate_rider_weight_exceeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_validate_base(
            monkeypatch,
            equine=make_fake_equine(max_rider_weight_kg=Decimal("50")),
            participant=make_fake_participant(weight_kg=Decimal("70")),
        )
        service = AssignmentService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.validate_assignment_candidate(FAKE_ID, FAKE_ID, FAKE_ID)
            assert exc.value.code == ErrorCode.ASSIGNMENT_RIDER_WEIGHT_EXCEEDS_LIMIT

        asyncio.run(run())

    def test_validate_child_rider_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        child = make_fake_participant(birth_date=date(2015, 6, 15))
        self._patch_validate_base(monkeypatch, participant=child)
        service = AssignmentService()

        async def run() -> None:
            flags, warnings = await service.validate_assignment_candidate(
                FAKE_ID,
                FAKE_ID,
                FAKE_ID,
            )
            assert "child_rider" in flags
            assert any("menor" in w.lower() for w in warnings)

        asyncio.run(run())

    def test_validate_missing_max_weight_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        equine = make_fake_equine(max_rider_weight_kg=None)
        self._patch_validate_base(monkeypatch, equine=equine)
        service = AssignmentService()

        async def run() -> None:
            flags, warnings = await service.validate_assignment_candidate(
                FAKE_ID,
                FAKE_ID,
                FAKE_ID,
            )
            assert flags == []
            assert any("límite de peso" in w.lower() for w in warnings)

        asyncio.run(run())
