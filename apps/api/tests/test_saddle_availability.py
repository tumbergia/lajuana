"""P1: SaddleService.list_available_for_reservation — availability & exclusion logic.

Risk: Incorrect saddle availability can cause duplicate saddle bookings or
leave riders without proper equipment. Every exclusion reason must be tested.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.services.saddle_service import SaddleService

FAKE_ID = "660000000000000000000001"
FAKE_ID_2 = "660000000000000000000002"
FAKE_ID_3 = "660000000000000000000003"


def make_fake_saddle(**overrides: object) -> SimpleNamespace:
    defaults = dict(
        id=FAKE_ID,
        code="S-001",
        name="Silla Inglesa",
        is_available=True,
        deleted_at=None,
        notes=None,
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


class TestSaddleAvailableForReservation:
    """SaddleService.list_available_for_reservation — exclusion rules."""

    def _patch_beanie(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        saddles: list | None = None,
        assignments_for_reservation: list | None = None,
    ) -> None:
        """Mock Beanie document access used by list_available_for_reservation."""
        all_saddles = saddles or []
        my_assignments = assignments_for_reservation or []

        def _fake_saddle_find(_query: dict) -> FakeFindQuery:
            return FakeFindQuery(all_saddles)

        def _fake_assignment_find(_query: dict) -> FakeFindQuery:
            return FakeFindQuery(my_assignments)

        monkeypatch.setattr(
            "app.services.saddle_service.SaddleDocument.find",
            _fake_saddle_find,
        )
        monkeypatch.setattr(
            "app.services.saddle_service.AssignmentDocument.find",
            _fake_assignment_find,
        )

    def test_all_saddles_available_when_no_assignments(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """No assignments exist → all saddles returned with block_reason=None."""
        saddles = [
            make_fake_saddle(id=FAKE_ID, code="S-001"),
            make_fake_saddle(id=FAKE_ID_2, code="S-002"),
        ]
        self._patch_beanie(monkeypatch, saddles=saddles, assignments_for_reservation=[])

        service = SaddleService()

        async def run() -> None:
            results = await service.list_available_for_reservation(FAKE_ID)
            assert len(results) == 2
            for saddle, reason in results:
                assert reason is None, f"Saddle {saddle.code} should be available"

        asyncio.run(run())

    def test_excludes_already_assigned_saddle(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Saddle already assigned to this reservation → blocked with reason."""
        saddle = make_fake_saddle(id=FAKE_ID, code="S-001", is_available=True)
        assigned = SimpleNamespace(saddle_id=FAKE_ID)

        self._patch_beanie(
            monkeypatch,
            saddles=[saddle],
            assignments_for_reservation=[assigned],
        )

        service = SaddleService()

        async def run() -> None:
            results = await service.list_available_for_reservation(FAKE_ID)
            assert len(results) == 1
            _saddle, reason = results[0]
            assert reason is not None
            assert "asignada" in reason.lower()

        asyncio.run(run())

    def test_excludes_unavailable_saddle(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Saddle with is_available=False → blocked."""
        saddle = make_fake_saddle(id=FAKE_ID, is_available=False)
        self._patch_beanie(monkeypatch, saddles=[saddle], assignments_for_reservation=[])

        service = SaddleService()

        async def run() -> None:
            results = await service.list_available_for_reservation(FAKE_ID)
            assert len(results) == 1
            _saddle, reason = results[0]
            assert reason is not None
            assert "disponible" in reason.lower()

        asyncio.run(run())

    def test_excludes_deleted_saddle(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Saddle with deleted_at set → blocked."""
        from datetime import UTC, datetime

        saddle = make_fake_saddle(
            id=FAKE_ID,
            deleted_at=datetime.now(UTC),
        )
        self._patch_beanie(monkeypatch, saddles=[saddle], assignments_for_reservation=[])

        service = SaddleService()

        async def run() -> None:
            results = await service.list_available_for_reservation(FAKE_ID)
            assert len(results) == 1
            _saddle, reason = results[0]
            assert reason is not None
            assert "eliminada" in reason.lower()

        asyncio.run(run())

    def test_mixed_availability(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Mix of available, assigned, and unavailable saddles."""
        available = make_fake_saddle(id=FAKE_ID, code="S-001", is_available=True)
        assigned = make_fake_saddle(id=FAKE_ID_2, code="S-002", is_available=True)
        unavailable = make_fake_saddle(id=FAKE_ID_3, code="S-003", is_available=False)

        # Saddle FAKE_ID_2 is already assigned to this reservation
        existing_assignment = SimpleNamespace(saddle_id=FAKE_ID_2)

        self._patch_beanie(
            monkeypatch,
            saddles=[available, assigned, unavailable],
            assignments_for_reservation=[existing_assignment],
        )

        service = SaddleService()

        async def run() -> None:
            results = await service.list_available_for_reservation(FAKE_ID)
            assert len(results) == 3

            reasons_by_code: dict[str, str | None] = {r[0].code: r[1] for r in results}

            # S-001: no assignments, available → None
            assert reasons_by_code["S-001"] is None

            # S-002: assigned to this reservation → blocked
            assert reasons_by_code["S-002"] is not None
            assert "asignada" in reasons_by_code["S-002"].lower()

            # S-003: not available → blocked
            assert reasons_by_code["S-003"] is not None
            assert "disponible" in reasons_by_code["S-003"].lower()

        asyncio.run(run())

    def test_empty_saddle_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No saddles at all → empty result."""
        self._patch_beanie(monkeypatch, saddles=[], assignments_for_reservation=[])
        service = SaddleService()

        async def run() -> None:
            results = await service.list_available_for_reservation(FAKE_ID)
            assert results == []

        asyncio.run(run())

    def test_reservation_with_no_saddle_assignments(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Assignments exist but none have saddle_id → all saddles available."""
        saddles = [
            make_fake_saddle(id=FAKE_ID, code="S-001"),
            make_fake_saddle(id=FAKE_ID_2, code="S-002"),
        ]
        # Assignments exist but saddle_id is None for both
        assignments = [
            SimpleNamespace(saddle_id=None),
            SimpleNamespace(saddle_id=None),
        ]
        self._patch_beanie(monkeypatch, saddles=saddles, assignments_for_reservation=assignments)

        service = SaddleService()

        async def run() -> None:
            results = await service.list_available_for_reservation(FAKE_ID)
            assert len(results) == 2
            for _saddle, reason in results:
                assert reason is None

        asyncio.run(run())
