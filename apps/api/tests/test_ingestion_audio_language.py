from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.channels.whatsapp import ingestion_service
from app.channels.whatsapp.ingestion_service import WhatsAppIngestionService


def _make_parsed(
    *,
    wa_message_id: str = "wamid-1",
    normalized_phone: str = "573138659839",
    message_type: str = "audio",
    media_id: str = "media-1",
) -> SimpleNamespace:
    return SimpleNamespace(
        wa_message_id=wa_message_id,
        from_phone=f"+{normalized_phone}",
        normalized_phone=normalized_phone,
        message_type=message_type,
        body=None,
        media_id=media_id,
        caption=None,
        provider_timestamp="1700000000",
        raw_payload={"type": message_type},
    )


def _make_payload(parsed: SimpleNamespace) -> dict[str, Any]:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": parsed.wa_message_id,
                                    "from": parsed.from_phone,
                                    "type": parsed.message_type,
                                    "audio": {"id": parsed.media_id},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }


class _FakeCollection:
    def __init__(self) -> None:
        self.upserts: list[dict[str, Any]] = []
        self.updates: list[dict[str, Any]] = []

    async def update_one(self, filter_: dict[str, Any], update: dict[str, Any], **_: Any) -> Any:
        if "$setOnInsert" in update:
            self.upserts.append(update["$setOnInsert"])
            return SimpleNamespace(upserted_id="fake-id")
        self.updates.append(update)
        return SimpleNamespace(upserted_id=None)


def _fake_orchestrator() -> SimpleNamespace:
    orch = SimpleNamespace()
    orch.ask = AsyncMock(return_value=SimpleNamespace(response="ok"))
    return orch


def _fake_outbound() -> SimpleNamespace:
    ob = SimpleNamespace()
    ob.send = AsyncMock(return_value=None)
    return ob


def _fake_resolver() -> SimpleNamespace:
    r = SimpleNamespace()
    r.resolve = AsyncMock(return_value=None)
    return r


def _fake_buffer() -> SimpleNamespace:
    b = SimpleNamespace()
    b.add_message = AsyncMock(
        return_value=SimpleNamespace(buffer_id="buf-1")
    )
    return b


def _build_service(
    monkeypatch: pytest.MonkeyPatch,
    *,
    collection: _FakeCollection,
) -> WhatsAppIngestionService:
    service = WhatsAppIngestionService(
        resolver=_fake_resolver(),  # type: ignore[arg-type]
        buffer_service=_fake_buffer(),  # type: ignore[arg-type]
        outbound_service=_fake_outbound(),  # type: ignore[arg-type]
    )
    service._orchestrator = _fake_orchestrator()  # type: ignore[assignment]
    monkeypatch.setattr(
        ingestion_service.WhatsAppInboundEventDocument,
        "get_motor_collection",
        classmethod(lambda cls: collection),
    )
    monkeypatch.setattr(ingestion_service, "_is_local_takeover", lambda: False)
    return service


@pytest.mark.asyncio
async def test_audio_is_buffered_not_processed_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audio entra al debounce buffer; no STT ni orchestrator en el ingest."""
    parsed = _make_parsed()
    collection = _FakeCollection()
    service = _build_service(monkeypatch, collection=collection)
    result = await service.ingest(_make_payload(parsed))

    assert result == 1
    service._orchestrator.ask.assert_not_called()  # type: ignore[attr-defined]
    service._outbound_service.send.assert_not_called()  # type: ignore[attr-defined]
    service._buffer_service.add_message.assert_called_once()  # type: ignore[attr-defined]
    call_kwargs = service._buffer_service.add_message.call_args.kwargs  # type: ignore[attr-defined]
    assert call_kwargs["message_id"] == "wamid-1"
    assert call_kwargs["body"] == "[audio]"


@pytest.mark.asyncio
async def test_two_audios_both_go_to_same_buffer_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dos audios se bufferizan (el merge/debounce los junta después)."""
    collection = _FakeCollection()
    service = _build_service(monkeypatch, collection=collection)

    p1 = _make_parsed(wa_message_id="a1", media_id="m1")
    p2 = _make_parsed(wa_message_id="a2", media_id="m2")
    await service.ingest(_make_payload(p1))
    # Second upsert needs a fresh upserted_id — reset collection behavior
    collection2 = _FakeCollection()
    monkeypatch.setattr(
        ingestion_service.WhatsAppInboundEventDocument,
        "get_motor_collection",
        classmethod(lambda cls: collection2),
    )
    await service.ingest(_make_payload(p2))

    assert service._buffer_service.add_message.call_count == 2  # type: ignore[attr-defined]
    service._orchestrator.ask.assert_not_called()  # type: ignore[attr-defined]
