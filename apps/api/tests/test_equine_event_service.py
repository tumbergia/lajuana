"""Tests for EquineEventService and unified equine timeline."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from beanie import PydanticObjectId

from app.common.enums import EquineOperationalStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents.equine_event_document import EquineEventType
from app.schemas.equine_event import EquineEventCreateSchema, EquineEventListFilters
from app.services.equine_event_service import EquineEventService
from app.services.equine_service import EquineService


EQUINE_ID = "660000000000000000000001"
OTHER_EQUINE_ID = "660000000000000000000002"


def _fake_equine(**overrides: object) -> SimpleNamespace:
    base = dict(
        id=PydanticObjectId(EQUINE_ID),
        name="Pegaso",
        is_available=True,
        operational_status=EquineOperationalStatus.AVAILABLE,
        weight_kg=None,
        height_m=None,
        last_weight_at=None,
        last_height_at=None,
        rest_until=None,
        availability_notes=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestEquineEventServiceCreate:

    def test_create_vaccination_without_reservation(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        inserted: list[object] = []
        equine = _fake_equine()

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                self.id = PydanticObjectId()
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted.append(self)

        async def fake_get(_id: str) -> SimpleNamespace:
            return equine

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)
        monkeypatch.setattr(mod, "EquineEventDocument", FakeDoc)

        async def run() -> None:
            service = EquineEventService()
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.VACCINATION,
                happened_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
                title="Vacuna influenza",
                next_due_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
            )
            doc = await service.create_for_equine(EQUINE_ID, payload)
            assert doc is not None
            assert len(inserted) == 1
            assert inserted[0].event_type == EquineEventType.VACCINATION
            assert inserted[0].reservation_id is None

        asyncio.run(run())

    def test_create_farrier_without_reservation(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        inserted: list[object] = []
        equine = _fake_equine()

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                self.id = PydanticObjectId()
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted.append(self)

        async def fake_get(_id: str) -> SimpleNamespace:
            return equine

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)
        monkeypatch.setattr(mod, "EquineEventDocument", FakeDoc)

        async def run() -> None:
            service = EquineEventService()
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.FARRIER,
                happened_at=datetime(2026, 5, 2, 9, 0, tzinfo=UTC),
                title="Herraje completo",
                performed_by="Herrador Juan",
            )
            await service.create_for_equine(EQUINE_ID, payload)
            assert inserted[0].event_type == EquineEventType.FARRIER

        asyncio.run(run())

    def test_create_note_without_reservation(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        inserted: list[object] = []
        equine = _fake_equine()

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                self.id = PydanticObjectId()
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted.append(self)

        async def fake_get(_id: str) -> SimpleNamespace:
            return equine

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)
        monkeypatch.setattr(mod, "EquineEventDocument", FakeDoc)

        async def run() -> None:
            service = EquineEventService()
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.NOTE,
                happened_at=datetime(2026, 5, 3, 8, 0, tzinfo=UTC),
                title="Nota de manejo",
                description="Prefiere salir primero en la cuadra.",
            )
            await service.create_for_equine(EQUINE_ID, payload)
            assert inserted[0].event_type == EquineEventType.NOTE

        asyncio.run(run())

    def test_create_weight_without_measurement_raises_400(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        async def fake_get(_id: str) -> SimpleNamespace:
            return _fake_equine()

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)

        async def run() -> None:
            service = EquineEventService()
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.WEIGHT,
                happened_at=datetime(2026, 5, 4, 8, 0, tzinfo=UTC),
                title="Pesaje",
            )
            with pytest.raises(ApiError) as exc:
                await service.create_for_equine(EQUINE_ID, payload)
            assert exc.value.status_code == 400
            assert exc.value.code == ErrorCode.EQUINE_EVENT_WEIGHT_REQUIRED

        asyncio.run(run())

    def test_create_rest_blocks_until_date(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        equine = _fake_equine()
        saved_equine: list[bool] = []

        async def fake_save() -> None:
            saved_equine.append(True)

        equine.save = fake_save

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                self.id = PydanticObjectId()
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                pass

        async def fake_get(_id: str) -> SimpleNamespace:
            return equine

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)
        monkeypatch.setattr(mod, "EquineEventDocument", FakeDoc)

        async def run() -> None:
            service = EquineEventService()
            rest_until = datetime(2026, 6, 1, 0, 0, tzinfo=UTC)
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.REST,
                happened_at=datetime(2026, 5, 10, 8, 0, tzinfo=UTC),
                title="Descanso post-servicio",
                description="Reposo programado",
                affects_availability=True,
                resulting_operational_status=EquineOperationalStatus.RESTING,
                rest_until=rest_until,
            )
            await service.create_for_equine(EQUINE_ID, payload)
            assert equine.is_available is False
            assert equine.operational_status == EquineOperationalStatus.RESTING
            assert equine.rest_until == rest_until
            assert equine.availability_reasons == "Reposo programado"
            assert len(saved_equine) == 1

        asyncio.run(run())

    def test_create_availability_recovery(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        equine = _fake_equine(
            is_available=False,
            operational_status=EquineOperationalStatus.INJURED,
            rest_until=datetime(2026, 6, 1, tzinfo=UTC),
            availability_reasons="Lesión previa",
        )
        saved_equine: list[bool] = []

        async def fake_save() -> None:
            saved_equine.append(True)

        equine.save = fake_save

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                self.id = PydanticObjectId()
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                pass

        async def fake_get(_id: str) -> SimpleNamespace:
            return equine

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)
        monkeypatch.setattr(mod, "EquineEventDocument", FakeDoc)

        async def run() -> None:
            service = EquineEventService()
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.AVAILABILITY_CHANGE,
                happened_at=datetime(2026, 5, 20, 9, 0, tzinfo=UTC),
                title="Alta operativa",
                description="Recuperado para servicio",
                resulting_operational_status=EquineOperationalStatus.AVAILABLE,
            )
            await service.create_for_equine(EQUINE_ID, payload)
            assert equine.is_available is True
            assert equine.operational_status == EquineOperationalStatus.AVAILABLE
            assert equine.rest_until is None
            assert equine.availability_reasons == "Recuperado para servicio"
            assert len(saved_equine) == 1

        asyncio.run(run())

    def test_create_injury_blocks_availability(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        equine = _fake_equine()
        saved_equine: list[bool] = []

        async def fake_save() -> None:
            saved_equine.append(True)

        equine.save = fake_save

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                self.id = PydanticObjectId()
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                pass

        async def fake_get(_id: str) -> SimpleNamespace:
            return equine

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)
        monkeypatch.setattr(mod, "EquineEventDocument", FakeDoc)

        async def run() -> None:
            service = EquineEventService()
            rest_until = datetime(2026, 5, 20, 0, 0, tzinfo=UTC)
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.INJURY,
                happened_at=datetime(2026, 5, 5, 14, 0, tzinfo=UTC),
                title="Lesión en pata delantera",
                description="Reposo 15 días",
                severity="high",
                affects_availability=True,
                resulting_operational_status=EquineOperationalStatus.INJURED,
                rest_until=rest_until,
            )
            await service.create_for_equine(EQUINE_ID, payload)
            assert equine.is_available is False
            assert equine.operational_status == EquineOperationalStatus.INJURED
            assert equine.rest_until == rest_until
            assert equine.availability_reasons == "Reposo 15 días"
            assert len(saved_equine) == 1

        asyncio.run(run())

    def test_assignment_equine_mismatch_raises_400(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        assignment_id = str(PydanticObjectId())

        async def fake_get_equine(_id: str) -> SimpleNamespace:
            return _fake_equine()

        async def fake_get_assignment(_id: str) -> SimpleNamespace:
            return SimpleNamespace(
                id=PydanticObjectId(assignment_id),
                equine_id=PydanticObjectId(OTHER_EQUINE_ID),
            )

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get_equine)
        monkeypatch.setattr(mod.AssignmentDocument, "get", fake_get_assignment)

        async def run() -> None:
            service = EquineEventService()
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.NOTE,
                happened_at=datetime(2026, 5, 6, 8, 0, tzinfo=UTC),
                title="Nota con asignación incorrecta",
                assignment_id=assignment_id,
            )
            with pytest.raises(ApiError) as exc:
                await service.create_for_equine(EQUINE_ID, payload)
            assert exc.value.status_code == 400
            assert exc.value.code == ErrorCode.EQUINE_EVENT_ASSIGNMENT_EQUINE_MISMATCH

        asyncio.run(run())


class TestEquineEventServiceList:

    def test_list_with_filters(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.services import equine_event_service as mod

        captured_query: dict[str, object] = {}

        class FakeFind:
            def __init__(self, query: dict[str, object]) -> None:
                captured_query.update(query)

            def sort(self, *_args: object) -> FakeFind:
                return self

            def limit(self, _n: int) -> FakeFind:
                return self

            async def to_list(self) -> list[object]:
                return []

            async def count(self) -> int:
                return 0

        async def fake_get(_id: str) -> SimpleNamespace:
            return _fake_equine()

        def fake_find(query: dict[str, object]) -> FakeFind:
            return FakeFind(query)

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)
        monkeypatch.setattr(mod.EquineEventDocument, "find", fake_find)

        async def run() -> None:
            service = EquineEventService()
            date_from = datetime(2026, 5, 1, tzinfo=UTC)
            date_to = datetime(2026, 5, 31, tzinfo=UTC)
            filters = EquineEventListFilters(
                event_type=EquineEventType.VACCINATION,
                date_from=date_from,
                date_to=date_to,
                limit=25,
            )
            result = await service.list_for_equine(EQUINE_ID, filters)
            assert result == []
            assert captured_query["event_type"] == EquineEventType.VACCINATION
            assert captured_query["happened_at"]["$gte"] == date_from
            assert captured_query["happened_at"]["$lte"] == date_to

        asyncio.run(run())


class TestEquineTimelineMerge:

    def test_timeline_merges_both_sources_sorted(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.documents.service_log_document import ServiceLogEventType
        from app.services import equine_service as mod

        log_old = SimpleNamespace(
            id=PydanticObjectId(),
            event_type=ServiceLogEventType.ARRIVAL,
            happened_at=datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
            checkpoint_name=None,
            reservation_id=PydanticObjectId(),
            related_participant_id=None,
            notes="Llegó a finca",
        )
        log_new = SimpleNamespace(
            id=PydanticObjectId(),
            event_type=ServiceLogEventType.CHECKPOINT,
            happened_at=datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
            checkpoint_name="Mirador",
            reservation_id=PydanticObjectId(),
            related_participant_id=PydanticObjectId(),
            notes=None,
        )
        event_mid = SimpleNamespace(
            id=PydanticObjectId(),
            event_type=EquineEventType.VACCINATION,
            happened_at=datetime(2026, 5, 5, 12, 0, tzinfo=UTC),
            title="Vacuna anual",
            reservation_id=None,
            assignment_id=None,
            participant_id=None,
            description="Sin reacción",
            severity="low",
            affects_availability=False,
            measured_weight_kg=None,
            measured_height_m=None,
            next_due_at=None,
            performed_by=None,
            medication_name=None,
            dosage=None,
            lab_result_summary=None,
            resulting_operational_status=None,
            rest_until=None,
        )

        class FakeFind:
            def __init__(self, items: list[object]) -> None:
                self._items = items

            def sort(self, *_args: object) -> FakeFind:
                return self

            def limit(self, _n: int) -> FakeFind:
                return self

            async def to_list(self) -> list[object]:
                return self._items

        async def fake_get_equine(_id: str) -> SimpleNamespace:
            return _fake_equine()

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get_equine)
        monkeypatch.setattr(
            mod.ServiceLogDocument,
            "find",
            lambda _q: FakeFind([log_old, log_new]),
        )
        monkeypatch.setattr(
            mod.EquineEventDocument,
            "find",
            lambda _q: FakeFind([event_mid]),
        )

        async def run() -> None:
            service = EquineService()
            timeline = await service.get_timeline(EQUINE_ID, limit=50)
            assert len(timeline) == 3
            assert timeline[0].source == "service_log"
            assert timeline[0].event_type == "checkpoint"
            assert timeline[1].source == "equine_event"
            assert timeline[1].event_type == "vaccination"
            assert timeline[2].source == "service_log"
            assert timeline[2].event_type == "arrival"

        asyncio.run(run())

    def test_timeline_future_happened_at_rejected(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import equine_event_service as mod

        async def fake_get(_id: str) -> SimpleNamespace:
            return _fake_equine()

        monkeypatch.setattr(mod.EquineDocument, "get", fake_get)

        async def run() -> None:
            service = EquineEventService()
            future = datetime.now(UTC) + timedelta(days=3)
            payload = EquineEventCreateSchema(
                event_type=EquineEventType.NOTE,
                happened_at=future,
                title="Evento futuro",
            )
            with pytest.raises(ApiError) as exc:
                await service.create_for_equine(EQUINE_ID, payload)
            assert exc.value.code == ErrorCode.EQUINE_EVENT_INVALID_HAPPENED_AT

        asyncio.run(run())
