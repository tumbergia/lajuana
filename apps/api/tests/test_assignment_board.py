"""P1: AssignmentService.get_board — board construction with full participant logic.

Risk: The assignment board is the operational cockpit for guides. Missing
blocking reasons, wrong summary counts, or incorrect assignment mapping can
lead to unsafe or incomplete ride preparations.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.common.enums import (
    AssignmentStatus,
    EquineExperienceFit,
    EquineOperationalStatus,
    EquineSex,
    EquineSpecies,
    ExperienceLevel,
    ReservationStatus,
)
from app.services.assignment_service import AssignmentService

FAKE_ID = "660000000000000000000001"
FAKE_ID_2 = "660000000000000000000002"
FAKE_ID_3 = "660000000000000000000003"
FAKE_EQ_ID = "660000000000000000000010"
FAKE_EQ_ID_2 = "660000000000000000000011"
FAKE_SD_ID = "660000000000000000000020"


class FakeFindQuery:
    """Reusable fake for Beanie find().skip().limit().to_list() chains."""

    def __init__(self, items: list) -> None:
        self._items = items

    def skip(self, n: int) -> "FakeFindQuery":
        return self

    def limit(self, n: int) -> "FakeFindQuery":
        return self

    async def to_list(self) -> list:
        return self._items


def make_fake_equine_doc(**overrides: object) -> SimpleNamespace:
    """Fake EquineDocument for EquineDocument.get() calls inside get_board()."""
    defaults = dict(
        id=FAKE_EQ_ID,
        name="Pegaso",
        species=EquineSpecies.HORSE,
        sex=EquineSex.MALE,
        is_active=True,
        is_available=True,
        operational_status=EquineOperationalStatus.AVAILABLE,
        breed="Criollo",
        coat_color="Bayo",
        gait="Fino",
        experience_fit=EquineExperienceFit.ALL,
        max_rider_weight_kg=Decimal("100"),
        weight_kg=Decimal("350"),
        height_m=Decimal("1.50"),
        inventory_number=101,
        microchip=None,
        registry_number=None,
        location_status="la_juana",
        approximate_age_years=6,
        last_service_at=None,
        workload_last_7_days=0,
        source_file=None,
        source_sheet=None,
        source_row_number=None,
        location_notes=None,
        availability_notes=None,
        availability_reasons=None,
        rest_until=None,
        image_base64=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_fake_saddle_doc(**overrides: object) -> SimpleNamespace:
    """Fake SaddleDocument for SaddleDocument.get() calls inside get_board()."""
    defaults = dict(
        id=FAKE_SD_ID,
        code="S-001",
        name="Silla Inglesa",
        is_available=True,
        notes=None,
        deleted_at=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)




class TestGetBoard:
    """AssignmentService.get_board — full board construction."""

    def _patch_documents(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        reservation: SimpleNamespace | None = None,
        participants: list[SimpleNamespace] | None = None,
        assignments: list[SimpleNamespace] | None = None,
    ) -> dict[str, SimpleNamespace]:
        """Mock all Beanie Document access used by get_board.

        Returns a lookup dict for created fake objects so the test can assert
        on the board output.
        """
        created: dict[str, SimpleNamespace] = {}
        reservation = reservation or self._default_reservation()
        participants = participants or self._default_participants()
        assignments = assignments or self._default_assignments()
        created["reservation"] = reservation
        created["participants"] = {str(p.id): p for p in participants}
        created["assignments"] = {str(a.id): a for a in assignments}

        async def _mock_get_reservation(_rid: str) -> SimpleNamespace | None:
            return reservation

        def _mock_participant_find(query: dict) -> FakeFindQuery:
            # Return only participants whose IDs are in the query
            return FakeFindQuery(participants)

        def _mock_assignment_find(query: dict) -> FakeFindQuery:
            return FakeFindQuery(assignments)

        def _mock_equine_find(query: dict) -> FakeFindQuery:
            eq_ids = query.get("_id", {}).get("$in", [])
            return FakeFindQuery([make_fake_equine_doc(id=eid) for eid in eq_ids])

        def _mock_saddle_find(query: dict) -> FakeFindQuery:
            sd_ids = query.get("_id", {}).get("$in", [])
            return FakeFindQuery([make_fake_saddle_doc(id=sid) for sid in sd_ids])

        monkeypatch.setattr(
            "app.services.assignment_service.ReservationDocument.get",
            _mock_get_reservation,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.ParticipantDocument.find",
            _mock_participant_find,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.AssignmentDocument.find",
            _mock_assignment_find,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.EquineDocument.find",
            _mock_equine_find,
        )
        monkeypatch.setattr(
            "app.services.assignment_service.SaddleDocument.find",
            _mock_saddle_find,
        )

        return created

    def _default_reservation(self) -> SimpleNamespace:
        return SimpleNamespace(
            id=FAKE_ID,
            status=ReservationStatus.CONFIRMED,
            participant_ids=[FAKE_ID, FAKE_ID_2, FAKE_ID_3],
            requested_date=date(2026, 6, 15),
        )

    def _default_participants(self) -> list[SimpleNamespace]:
        """Three participants: assigned, pending, blocked."""
        return [
            # Participant 1 — fully completed, will be assigned
            SimpleNamespace(
                id=FAKE_ID,
                first_name="Juan",
                last_name="Pérez",
                birth_date=date(1990, 1, 1),
                weight_kg=Decimal("70"),
                height_cm=Decimal("170"),
                experience_level=ExperienceLevel.INTERMEDIATE,
                is_completed=True,
                assigned_equine_id=FAKE_EQ_ID,
            ),
            # Participant 2 — fully completed, NOT assigned (pending)
            SimpleNamespace(
                id=FAKE_ID_2,
                first_name="María",
                last_name="Gómez",
                birth_date=date(1995, 5, 10),
                weight_kg=Decimal("60"),
                height_cm=Decimal("165"),
                experience_level=ExperienceLevel.BASIC,
                is_completed=True,
            ),
            # Participant 3 — missing data (blocking)
            SimpleNamespace(
                id=FAKE_ID_3,
                first_name="Don",
                last_name="Quijote",
                birth_date=date(1985, 3, 20),
                weight_kg=None,
                height_cm=None,
                experience_level=None,
                is_completed=False,
            ),
        ]

    def _default_assignments(self) -> list[SimpleNamespace]:
        """One assignment: Participant 1 gets equine + saddle."""
        return [
            SimpleNamespace(
                id="assign-001",
                reservation_id=FAKE_ID,
                participant_id=FAKE_ID,
                equine_id=FAKE_EQ_ID,
                saddle_id=FAKE_SD_ID,
                status=AssignmentStatus.CONFIRMED,
                validation_warnings=[],
            ),
        ]

    def test_get_board_full_flow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Full board with assigned, pending, and blocked participants.

        Also exercises equine and saddle availability listing.
        """
        created = self._patch_documents(monkeypatch)
        reservation = created["reservation"]

        # Mock equine service
        async def mock_equine_list(_rid: str) -> list[tuple[SimpleNamespace, str | None]]:
            return [
                (make_fake_equine_doc(), None),
                (make_fake_equine_doc(id=FAKE_EQ_ID_2, name="Relámpago"), "Equino inactivo"),
            ]

        # Mock saddle service
        async def mock_saddle_list(_rid: str) -> list[tuple[SimpleNamespace, str | None]]:
            return [
                (make_fake_saddle_doc(), None),
            ]

        mock_equine_service = SimpleNamespace(list_available_for_reservation=mock_equine_list)
        mock_saddle_service = SimpleNamespace(list_available_for_reservation=mock_saddle_list)

        # Mappers no longer needed — service reads attributes directly
        service = AssignmentService(
            equine_service=mock_equine_service,  # type: ignore[arg-type]
            saddle_service=mock_saddle_service,  # type: ignore[arg-type]
        )

        async def run() -> None:
            board = await service.get_board(FAKE_ID)

            # ── Top-level fields ──
            assert board["reservation_id"] == FAKE_ID
            assert board["reservation_status"] == ReservationStatus.CONFIRMED.value
            assert board["scheduled_date"] == "2026-06-15"

            # ── Summary ──
            summary = board["summary"]
            assert summary["participants_total"] == 3
            assert summary["assigned_total"] == 1
            assert summary["pending_total"] == 1
            assert summary["blocking_total"] == 1

            # ── Participants ──
            participants = board["participants"]
            assert len(participants) == 3

            # Participant 1: assigned
            p1 = next(p for p in participants if p["participant_id"] == FAKE_ID)
            assert p1["full_name"] == "Juan Pérez"
            assert p1["age_years"] == 36  # 2026 - 1990 = 36
            assert p1["weight_kg"] == "70"  # Decimal is serialized as string in mode="json"
            assert p1["experience_level"] == ExperienceLevel.INTERMEDIATE.value
            assert p1["blocking_reasons"] == []
            assert p1["assignment"] is not None
            assert p1["assignment"]["equine_name"] == "Pegaso"
            assert p1["assignment"]["saddle_label"] is not None
            assert "S-001" in p1["assignment"]["saddle_label"]
            assert p1["assignment"]["status"] == AssignmentStatus.CONFIRMED.value

            # Participant 2: pending (no assignment, no blockers)
            p2 = next(p for p in participants if p["participant_id"] == FAKE_ID_2)
            assert p2["full_name"] == "María Gómez"
            assert p2["blocking_reasons"] == []
            assert p2["assignment"] is None

            # Participant 3: blocked (missing data)
            p3 = next(p for p in participants if p["participant_id"] == FAKE_ID_3)
            assert p3["full_name"] == "Don Quijote"
            assert p3["assignment"] is None
            assert len(p3["blocking_reasons"]) >= 2
            assert any("peso" in r.lower() for r in p3["blocking_reasons"])
            assert any("experiencia" in r.lower() for r in p3["blocking_reasons"])

            # ── Available equines ──
            equines = board["available_equines"]
            assert len(equines) == 2
            eq1 = next(e for e in equines if e["id"] == FAKE_EQ_ID)
            eq2 = next(e for e in equines if e["id"] == FAKE_EQ_ID_2)
            assert eq1["block_reason"] is None
            assert eq2["block_reason"] is not None

            # ── Available saddles ──
            saddles = board["available_saddles"]
            assert len(saddles) == 1
            assert saddles[0]["block_reason"] is None

        asyncio.run(run())

    def test_get_board_no_equine_saddle_services(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Without equine/saddle services, those lists are empty."""
        self._patch_documents(monkeypatch)
        service = AssignmentService(equine_service=None, saddle_service=None)

        async def run() -> None:
            board = await service.get_board(FAKE_ID)
            assert board["available_equines"] == []
            assert board["available_saddles"] == []
            assert board["summary"]["participants_total"] == 3

        asyncio.run(run())

    def test_get_board_reservation_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Non-existent reservation → 404."""
        async def _mock_get_none(_rid: str) -> None:
            return None

        monkeypatch.setattr(
            "app.services.assignment_service.ReservationDocument.get",
            _mock_get_none,
        )

        service = AssignmentService()

        async def run() -> None:
            from app.core.errors import ApiError
            from app.common.labels import ErrorCode
            with pytest.raises(ApiError) as exc:
                await service.get_board(FAKE_ID_3)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.RESERVATION_NOT_FOUND

        asyncio.run(run())

    def test_get_board_with_child_and_senior_blocking_reasons(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Participants < 12 or > 65 get appropriate blocking reasons."""
        reservation = SimpleNamespace(
            id=FAKE_ID,
            status=ReservationStatus.CONFIRMED,
            participant_ids=[FAKE_ID, FAKE_ID_2],
            requested_date=date(2026, 6, 15),
        )
        child = SimpleNamespace(
            id=FAKE_ID,
            first_name="Niño",
            last_name="Chico",
            birth_date=date(2015, 6, 15),  # age 10
            weight_kg=Decimal("30"),
            height_cm=Decimal("120"),
            experience_level=ExperienceLevel.BASIC,
            is_completed=True,
        )
        senior = SimpleNamespace(
            id=FAKE_ID_2,
            first_name="Viejo",
            last_name="Mayor",
            birth_date=date(1955, 1, 1),  # age 71
            weight_kg=Decimal("70"),
            height_cm=Decimal("170"),
            experience_level=ExperienceLevel.ADVANCED,
            is_completed=True,
        )
        self._patch_documents(
            monkeypatch,
            reservation=reservation,
            participants=[child, senior],
            assignments=[],
        )
        service = AssignmentService()

        async def run() -> None:
            board = await service.get_board(FAKE_ID)
            participants = board["participants"]
            assert len(participants) == 2

            child_p = next(p for p in participants if p["participant_id"] == FAKE_ID)
            senior_p = next(p for p in participants if p["participant_id"] == FAKE_ID_2)

            assert any("12" in r for r in child_p["blocking_reasons"])
            assert any("65" in r for r in senior_p["blocking_reasons"])

        asyncio.run(run())

    def test_get_board_no_participants(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reservation with no participant_ids returns empty participants."""
        reservation = SimpleNamespace(
            id=FAKE_ID,
            status=ReservationStatus.CONFIRMED,
            participant_ids=[],
            requested_date=date(2026, 6, 15),
        )
        self._patch_documents(
            monkeypatch,
            reservation=reservation,
            participants=[],
            assignments=[],
        )
        service = AssignmentService()

        async def run() -> None:
            board = await service.get_board(FAKE_ID)
            assert board["participants"] == []
            assert board["summary"]["participants_total"] == 0
            assert board["summary"]["assigned_total"] == 0
            assert board["summary"]["pending_total"] == 0
            assert board["summary"]["blocking_total"] == 0

        asyncio.run(run())
