from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.ai.providers.stt_provider import TranscriptionResult
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
    """Replica del motor collection: idempotente sobre `wa_message_id`."""

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
    orch.ask = AsyncMock(
        return_value=SimpleNamespace(response="reservaré la fecha")
    )
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
    b.add_message = AsyncMock(return_value=None)
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
    # Reemplazar orchestrator por uno fake.
    service._orchestrator = _fake_orchestrator()  # type: ignore[assignment]
    # Reemplazar la collection Mongo por la fake.
    monkeypatch.setattr(
        ingestion_service.WhatsAppInboundEventDocument,
        "get_motor_collection",
        classmethod(lambda cls: collection),
    )
    # Evitar el touch de Beanie sobre Mongo (los tests no inicializan Beanie).
    class _FakeTurnDoc:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.id = "fake-turn-id"

        async def insert(self) -> None:
            return None

        async def save(self) -> None:
            return None

    monkeypatch.setattr(
        ingestion_service, "ConversationTurnDocument", _FakeTurnDoc
    )
    return service


@pytest.mark.asyncio
async def test_audio_in_unsupported_language_returns_unsupported_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cuando el STT detecta un idioma fuera del catálogo soportado, el
    servicio responde con `unsupported_language_message` y NO invoca al
    orchestrator. Ver ADR-0013."""
    parsed = _make_parsed()
    collection = _FakeCollection()

    async def fake_transcribe(media_id: str) -> TranscriptionResult:
        return TranscriptionResult(
            text="안녕하세요",
            language="ko",
            language_probability=0.95,
            duration=2.0,
        )

    monkeypatch.setattr(
        ingestion_service, "download_and_transcribe", fake_transcribe
    )

    service = _build_service(monkeypatch, collection=collection)
    result = await service.ingest(_make_payload(parsed))

    assert result == 1
    # El orchestrator NO debe haber sido invocado.
    service._orchestrator.ask.assert_not_called()  # type: ignore[attr-defined]
    # Debe haberse enviado el mensaje de idioma no soportado.
    service._outbound_service.send.assert_called_once()  # type: ignore[attr-defined]
    # El documento debe registrar el idioma detectado.
    persisted = collection.updates
    assert any(
        u.get("$set", {}).get("transcription_language") == "ko" for u in persisted
    )


@pytest.mark.asyncio
async def test_audio_in_supported_language_routes_to_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audio en español (detectado por STT) sigue el flujo normal y se
    procesa por el orchestrator. Verifica que `audio_language` se pasa
    correctamente en el `AskRequest`."""
    parsed = _make_parsed()
    collection = _FakeCollection()

    async def fake_transcribe(media_id: str) -> TranscriptionResult:
        return TranscriptionResult(
            text="Quiero reservar para mañana",
            language="es",
            language_probability=0.98,
            duration=3.0,
        )

    monkeypatch.setattr(
        ingestion_service, "download_and_transcribe", fake_transcribe
    )

    service = _build_service(monkeypatch, collection=collection)
    await service.ingest(_make_payload(parsed))

    # El orchestrator SÍ se invoca.
    service._orchestrator.ask.assert_called_once()  # type: ignore[attr-defined]
    call_args = service._orchestrator.ask.call_args  # type: ignore[attr-defined]
    ask_request = call_args.args[0]
    assert ask_request.message == "Quiero reservar para mañana"
    assert ask_request.audio_language == "es"
    # La respuesta del orchestrator se envía al cliente.
    service._outbound_service.send.assert_called_once()  # type: ignore[attr-defined]
    # El documento persiste el idioma detectado.
    persisted = collection.updates
    assert any(
        u.get("$set", {}).get("transcription_language") == "es" for u in persisted
    )


@pytest.mark.asyncio
async def test_audio_in_mandarin_routes_to_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audio en chino mandarín debe procesarse normalmente (zh está en el
    catálogo soportado) y `audio_language="zh"` debe llegar al orchestrator."""
    parsed = _make_parsed()
    collection = _FakeCollection()

    async def fake_transcribe(media_id: str) -> TranscriptionResult:
        return TranscriptionResult(
            text="我想预订",
            language="zh",
            language_probability=0.93,
            duration=2.4,
        )

    monkeypatch.setattr(
        ingestion_service, "download_and_transcribe", fake_transcribe
    )

    service = _build_service(monkeypatch, collection=collection)
    await service.ingest(_make_payload(parsed))

    service._orchestrator.ask.assert_called_once()  # type: ignore[attr-defined]
    ask_request = service._orchestrator.ask.call_args.args[0]  # type: ignore[attr-defined]
    assert ask_request.audio_language == "zh"
    assert ask_request.message == "我想预订"
