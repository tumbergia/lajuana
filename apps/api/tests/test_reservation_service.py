"""Emisión de cambios de sync (`record_change`) desde ReservationService.

P1: si estas mutaciones no emiten, `/sync/pull` nunca se entera de cambios
en reservas y el modo offline móvil queda desactualizado silenciosamente.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.common.enums import ReservationStatus, UserRole
from app.core.di import Container
from app.services import sync_change_recorder as rec


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
        confirmed_at=None,
        cancelled_at=None,
        deleted_at=None,
        updated_by=None,
        version=1,
        updated_at=datetime.now(UTC),
        blocks_day=False,
        availability_lock_key=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class _CapturingSyncChangeDocument:
    """Fake de SyncChangeDocument — captura kwargs sin tocar Mongo."""

    captured: list[dict] = []

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        _CapturingSyncChangeDocument.captured.append(kwargs)

    async def insert(self) -> _CapturingSyncChangeDocument:
        return self


@pytest.fixture(autouse=True)
def _capture_sync_changes(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    _CapturingSyncChangeDocument.captured = []
    monkeypatch.setattr(rec, "SyncChangeDocument", _CapturingSyncChangeDocument)

    async def _fake_payload(entity_type: str, doc: object) -> dict:
        return {"entity_type": entity_type, "id": getattr(doc, "id", None)}

    monkeypatch.setattr(rec, "_build_payload", _fake_payload)
    return _CapturingSyncChangeDocument.captured


def test_update_emits_reservation_change(
    monkeypatch: pytest.MonkeyPatch, _capture_sync_changes: list[dict]
) -> None:
    res = _reservation()

    async def run() -> None:
        async def _mock_get(_rid: str, **_kwargs: object) -> object:
            return res

        async def _mock_save() -> None:
            pass

        res.save = _mock_save  # type: ignore[assignment]

        svc = Container.get_instance().reservation_service
        monkeypatch.setattr(svc, "get", _mock_get)

        await svc.update("660000000000000000000001", {"holder_name": "Nuevo"})

        assert len(_capture_sync_changes) == 1
        assert _capture_sync_changes[0]["stream"] == "reservations"
        assert _capture_sync_changes[0]["entity_type"] == "reservation"
        assert _capture_sync_changes[0]["change_type"] == "upsert"

    asyncio.run(run())


def test_set_status_emits_reservation_change(
    monkeypatch: pytest.MonkeyPatch, _capture_sync_changes: list[dict]
) -> None:
    res = _reservation(status=ReservationStatus.QUOTED)

    async def run() -> None:
        async def _mock_get(_rid: str, **_kwargs: object) -> object:
            return res

        async def _mock_save() -> None:
            pass

        res.save = _mock_save  # type: ignore[assignment]

        svc = Container.get_instance().reservation_service
        monkeypatch.setattr(svc, "get", _mock_get)

        await svc.set_status(
            "660000000000000000000001", ReservationStatus.PRE_RESERVED
        )

        assert len(_capture_sync_changes) == 1
        assert _capture_sync_changes[0]["entity_type"] == "reservation"

    asyncio.run(run())


def test_cancel_reservation_emits_reservation_change(
    monkeypatch: pytest.MonkeyPatch, _capture_sync_changes: list[dict]
) -> None:
    res = _reservation()

    async def run() -> None:
        async def _mock_get(_rid: str, **_kwargs: object) -> object:
            return res

        async def _mock_save() -> None:
            pass

        res.save = _mock_save  # type: ignore[assignment]

        async def _noop(*_args: object, **_kwargs: object) -> None:
            pass

        svc = Container.get_instance().reservation_service
        monkeypatch.setattr(svc, "get", _mock_get)
        monkeypatch.setattr(svc, "_sync_day_lock_fields", _noop)
        monkeypatch.setattr(svc.notification_service, "enqueue_reservation_cancelled", _noop)

        await svc.cancel_reservation(
            reservation_id="660000000000000000000001",
            actor_id="660000000000000000000050",
            notify_client=False,
        )

        assert len(_capture_sync_changes) == 1
        assert _capture_sync_changes[0]["entity_type"] == "reservation"

    asyncio.run(run())


def test_soft_delete_emits_delete_change(
    monkeypatch: pytest.MonkeyPatch, _capture_sync_changes: list[dict]
) -> None:
    res = _reservation()

    async def run() -> None:
        async def _mock_get(_rid: str, **_kwargs: object) -> object:
            return res

        async def _mock_save() -> None:
            pass

        res.save = _mock_save  # type: ignore[assignment]

        svc = Container.get_instance().reservation_service
        monkeypatch.setattr(svc, "get", _mock_get)

        await svc.soft_delete("660000000000000000000001")

        assert len(_capture_sync_changes) == 1
        assert _capture_sync_changes[0]["change_type"] == "delete"

    asyncio.run(run())


def test_restore_emits_upsert_change(
    monkeypatch: pytest.MonkeyPatch, _capture_sync_changes: list[dict]
) -> None:
    res = _reservation(deleted_at=datetime.now(UTC))

    async def run() -> None:
        async def _mock_get(_rid: str, **_kwargs: object) -> object:
            return res

        async def _mock_save() -> None:
            pass

        res.save = _mock_save  # type: ignore[assignment]

        svc = Container.get_instance().reservation_service
        monkeypatch.setattr(svc, "get", _mock_get)

        await svc.restore("660000000000000000000001")

        assert len(_capture_sync_changes) == 1
        assert _capture_sync_changes[0]["change_type"] == "upsert"

    asyncio.run(run())


class TestListForBootstrap:
    """list_for_bootstrap — ventana activa+reciente, sin tocar Mongo real."""

    def test_admin_query_includes_active_and_recent_terminal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured_queries: list[dict] = []

        class _FakeFind:
            def __init__(self, query: dict) -> None:
                captured_queries.append(query)

            def sort(self, *_args: object) -> _FakeFind:
                return self

            def limit(self, *_args: object) -> _FakeFind:
                return self

            async def to_list(self) -> list[object]:
                return []

        async def run() -> None:
            from app.documents import ReservationDocument

            monkeypatch.setattr(ReservationDocument, "find", _FakeFind)
            svc = Container.get_instance().reservation_service
            await svc.list_for_bootstrap(actor_role=UserRole.ADMIN)

            assert len(captured_queries) == 1
            query = captured_queries[0]
            assert query["deleted_at"] is None
            assert "$or" in query
            # Rama 1: estados activos (sin filtro de fecha).
            active_clause = query["$or"][0]
            assert "status" in active_clause
            # Rama 2: terminales recientes con filtro de updated_at.
            recent_clause = query["$or"][1]
            assert "updated_at" in recent_clause
            assert "$gte" in recent_clause["updated_at"]

        asyncio.run(run())

    def test_guide_query_only_confirmed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured_queries: list[dict] = []

        class _FakeFind:
            def __init__(self, query: dict) -> None:
                captured_queries.append(query)

            def sort(self, *_args: object) -> _FakeFind:
                return self

            def limit(self, *_args: object) -> _FakeFind:
                return self

            async def to_list(self) -> list[object]:
                return []

        async def run() -> None:
            from app.documents import ReservationDocument

            monkeypatch.setattr(ReservationDocument, "find", _FakeFind)
            svc = Container.get_instance().reservation_service
            await svc.list_for_bootstrap(actor_role=UserRole.GUIDE)

            assert len(captured_queries) == 1
            query = captured_queries[0]
            assert query["status"] == ReservationStatus.CONFIRMED
            assert "$or" not in query

        asyncio.run(run())
