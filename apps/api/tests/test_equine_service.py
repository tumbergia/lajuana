"""P1: Equine CRUD — create, read, list, update, soft-delete.

Risk: equine inventory management is core to operations. Incorrect CRUD logic
can lead to assigning unavailable or inactive equines to reservations,
creating safety risks and operational failures.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.common.enums import (
    EquineExperienceFit,
    EquineLocationStatus,
    EquineOperationalStatus,
    EquineSex,
    EquineSpecies,
)
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.schemas.equine import EquineCreateSchema, EquineUpdateSchema
from app.services.equine_service import EquineService


def _fake_equine_doc(**overrides: object) -> SimpleNamespace:
    """Create a fake EquineDocument-like object for test stubs."""
    base = dict(
        id="660000000000000000000001",
        name="Pegaso",
        species=EquineSpecies.HORSE,
        sex=EquineSex.MALE,
        is_active=True,
        is_available=True,
        operational_status=EquineOperationalStatus.AVAILABLE,
        location_status=EquineLocationStatus.LA_JUANA,
        breed="Criollo",
        coat_color="Bayo",
        gait="Fino",
        experience_fit=EquineExperienceFit.ALL,
        max_rider_weight_kg=Decimal("80"),
        weight_kg=Decimal("350"),
        height_m=Decimal("1.50"),
        approximate_birth_date=date(2020, 1, 15),
        inventory_number=101,
        microchip="MIC-001",
        registry_number="REG-001",
        source_file=None,
        source_sheet=None,
        source_row_number=None,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestEquineServiceCreate:
    """EquineService.create — basic creation."""

    def test_create_equine_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Creating an equine with valid data should succeed."""
        inserted_docs: list[object] = []

        class FakeEquineDocument:
            def __init__(self, **kwargs: object) -> None:
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted_docs.append(self)

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument",
            FakeEquineDocument,
        )

        service = EquineService()

        async def run() -> None:
            payload = EquineCreateSchema(
                name="Pegaso",
                species=EquineSpecies.HORSE,
                sex=EquineSex.MALE,
                breed="Criollo",
                coat_color="Bayo",
            )
            result = await service.create(payload)
            assert result is not None
            assert result.name == "Pegaso"
            assert len(inserted_docs) == 1

        asyncio.run(run())


class TestEquineServiceGet:
    """EquineService.get — retrieval by ID."""

    def test_get_equine_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Getting an existing equine should return the document."""
        fake = _fake_equine_doc()

        async def _mock_get(_: str) -> object:
            return fake

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.get",
            _mock_get,
        )

        service = EquineService()

        async def run() -> None:
            result = await service.get("660000000000000000000001")
            assert result is not None
            assert result.id == "660000000000000000000001"

        asyncio.run(run())

    def test_get_equine_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Getting a non-existent equine should raise ApiError 404."""
        async def _mock_get(_: str) -> None:
            return None

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.get",
            _mock_get,
        )

        service = EquineService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.get("6600000000000000000999")
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.EQUINE_NOT_FOUND

        asyncio.run(run())


class TestEquineServiceList:
    """EquineService.list — paginated listing with filters."""

    def test_list_equines_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Listing all equines should return the full list."""
        fake_list = [
            _fake_equine_doc(id="660000000000000000001", name="Pegaso"),
            _fake_equine_doc(id="660000000000000000002", name="Relampago"),
        ]

        class FakeFindQuery:
            def __init__(self, items: list[SimpleNamespace]) -> None:
                self._items = items

            def skip(self, n: int) -> FakeFindQuery:
                return self

            def limit(self, n: int) -> FakeFindQuery:
                return self

            async def to_list(self) -> list[SimpleNamespace]:
                return self._items

        def _fake_find(query: dict) -> FakeFindQuery:
            return FakeFindQuery(fake_list)

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.find",
            _fake_find,
        )

        service = EquineService()

        async def run() -> None:
            results = await service.list()
            assert len(results) == 2

        asyncio.run(run())

    def test_list_equines_filtered_by_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Listing equines with a status filter should pass the filter."""
        captured_query: list[dict] = []

        class FakeFindQuery:
            def __init__(self, items: list[SimpleNamespace]) -> None:
                self._items = items

            def skip(self, n: int) -> FakeFindQuery:
                return self

            def limit(self, n: int) -> FakeFindQuery:
                return self

            async def to_list(self) -> list[SimpleNamespace]:
                return self._items

        def _fake_find(query: dict) -> FakeFindQuery:
            captured_query.append(query)
            return FakeFindQuery([])

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.find",
            _fake_find,
        )

        service = EquineService()

        async def run() -> None:
            await service.list(operational_status=EquineOperationalStatus.AVAILABLE)
            assert len(captured_query) == 1
            assert captured_query[0].get("operational_status") == EquineOperationalStatus.AVAILABLE

        asyncio.run(run())


class TestEquineServiceUpdate:
    """EquineService.update — field updates."""

    def test_update_equine_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Updating an existing equine should change fields."""
        fake = _fake_equine_doc()

        async def _mock_get(_: str) -> SimpleNamespace:
            return fake

        saved = False

        async def _mock_save() -> None:
            nonlocal saved
            saved = True

        fake.save = _mock_save  # type: ignore[assignment]

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.get",
            _mock_get,
        )

        service = EquineService()

        async def run() -> None:
            payload = EquineUpdateSchema(name="Pegaso Updated", breed="Lusitano")
            result = await service.update("660000000000000000000001", payload)
            assert result is not None
            assert saved
            assert result.name == "Pegaso Updated"

        asyncio.run(run())

    def test_update_equine_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Updating a non-existent equine should raise ApiError 404."""
        async def _mock_get(_: str) -> None:
            return None

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.get",
            _mock_get,
        )

        service = EquineService()

        async def run() -> None:
            payload = EquineUpdateSchema(name="Ghost")
            with pytest.raises(ApiError) as exc:
                await service.update("6600000000000000000999", payload)
            assert exc.value.status_code == 404

        asyncio.run(run())


class TestEquineServiceDeactivate:
    """EquineService.deactivate — soft delete."""

    def test_deactivate_equine_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Deactivating an equine should set is_active=False, is_available=False, RETIRED."""
        fake = _fake_equine_doc()

        async def _mock_get(_: str) -> SimpleNamespace:
            return fake

        async def _mock_save() -> None:
            pass

        fake.save = _mock_save  # type: ignore[assignment]

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.get",
            _mock_get,
        )

        service = EquineService()

        async def run() -> None:
            result = await service.deactivate("660000000000000000000001")
            assert result.is_active is False
            assert result.is_available is False
            assert result.operational_status == EquineOperationalStatus.RETIRED

        asyncio.run(run())

    def test_deactivate_equine_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Deactivating a non-existent equine should raise ApiError 404."""
        async def _mock_get(_: str) -> None:
            return None

        monkeypatch.setattr(
            "app.services.equine_service.EquineDocument.get",
            _mock_get,
        )

        service = EquineService()

        async def run() -> None:
            with pytest.raises(ApiError) as exc:
                await service.deactivate("6600000000000000000999")
            assert exc.value.status_code == 404

        asyncio.run(run())
