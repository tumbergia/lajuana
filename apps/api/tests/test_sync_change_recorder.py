"""Unit tests for the sync change recorder (pull change feed emission)."""

import asyncio
import os
from datetime import UTC, datetime
from types import SimpleNamespace

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.services import sync_change_recorder as rec
from app.services.sync_service import SYNC_REQUIRED_PERMISSION


def test_stream_map_covers_all_pushable_entities() -> None:
    """Toda entidad que se puede pushear debe tener un stream de pull."""
    pushable = {entity for (entity, _op) in SYNC_REQUIRED_PERMISSION}
    missing = pushable - set(rec.STREAM_BY_ENTITY)
    assert missing == set(), f"streams faltantes para: {missing}"


def test_record_change_unknown_entity_is_noop(monkeypatch) -> None:
    inserted = []

    class _FakeChange:
        def __init__(self, **kwargs):
            inserted.append(kwargs)

        async def insert(self):
            return self

    monkeypatch.setattr(rec, "SyncChangeDocument", _FakeChange)
    asyncio.run(
        rec.record_change(entity_type="not_a_real_entity", doc=SimpleNamespace(id="x"))
    )
    assert inserted == []


def test_record_change_builds_document(monkeypatch) -> None:
    captured = {}

    class _FakeChange:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        async def insert(self):
            return self

    async def _fake_payload(entity_type, doc):
        return {"hello": "world"}

    monkeypatch.setattr(rec, "SyncChangeDocument", _FakeChange)
    monkeypatch.setattr(rec, "_build_payload", _fake_payload)

    doc = SimpleNamespace(id="e1", version=3, updated_at=datetime.now(UTC))
    asyncio.run(rec.record_change(entity_type="experience", doc=doc, change_type="delete"))

    assert captured["stream"] == "experiences"
    assert captured["entity_type"] == "experience"
    assert captured["entity_id"] == "e1"
    assert captured["change_type"] == "delete"
    assert captured["version"] == 3
    assert captured["payload"] == {"hello": "world"}


def test_record_change_swallows_errors(monkeypatch) -> None:
    """Un fallo del feed nunca debe propagarse a la mutación de negocio."""

    async def _boom(entity_type, doc):
        raise RuntimeError("db down")

    monkeypatch.setattr(rec, "_build_payload", _boom)
    # No debe lanzar.
    asyncio.run(
        rec.record_change(entity_type="experience", doc=SimpleNamespace(id="e1"))
    )


def test_config_payload_shape() -> None:
    """El cambio de config lleva la forma que el cliente sabe aplicar."""
    doc = SimpleNamespace(id="cfg", version=2, updated_at=datetime.now(UTC))
    payload = asyncio.run(rec._build_payload("reservation_rules", doc))
    assert payload["key"] == "reservation_rules"
    assert "reservation_rules" in payload
    assert payload["version"] == 2
