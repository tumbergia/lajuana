from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.conversations.services.conversation_turn_worker import ConversationTurnWorker
from app.core.di import Container


class FakeTurn:
    def __init__(self) -> None:
        self.id = "turn-1"
        self.status = "processing"
        self.response_text = ""
        self.responded_at = None

    async def save(self) -> None:
        return None


@pytest.mark.asyncio
async def test_media_proof_attaches_when_single_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    _container = Container.get_instance()
    worker = ConversationTurnWorker(
        lock_service=_container._services["conversation_lock_service"],
        buffer_service=_container._services["message_buffer_service"],
        outbound_service=_container._services["whatsapp_outbound_service"],
    )
    sent: list[str] = []
    captured: dict[str, Any] = {}

    async def fake_find_active_candidates(_: str) -> list[Any]:
        return [SimpleNamespace(id="res-1", code="PR-1")]

    async def fake_registry_call(name: str, **kwargs: Any) -> dict[str, Any]:
        captured["name"] = name
        captured["kwargs"] = kwargs
        return {"response": "Comprobante recibido y en revision."}

    async def fake_send(**kwargs: Any) -> Any:
        sent.append(kwargs["text"])
        return None

    monkeypatch.setattr(worker, "_find_active_candidates", fake_find_active_candidates)
    monkeypatch.setattr(
        "app.conversations.services.conversation_turn_worker.registry.call", fake_registry_call
    )
    monkeypatch.setattr(worker._outbound_service, "send", fake_send)

    event = SimpleNamespace(
        wa_message_id="wamid.1",
        media_id="media-1",
        message_type="image",
        caption="soporte",
        raw_payload={"image": {"mime_type": "image/jpeg", "filename": "pago.jpg"}},
        received_at=datetime.now(UTC),
    )
    turn = FakeTurn()

    processed = await worker._try_process_media_proof(
        events=[event],
        trace_id="tr-1",
        conversation_id="conv-1",
        normalized_phone="+573001112233",
        turn=turn,
    )

    assert processed is True
    assert captured["name"] == "attach_payment_proof_to_reservation"
    assert captured["kwargs"]["media_id"] == "media-1"
    assert "raw_payload" not in captured["kwargs"]
    assert sent[-1] == "Comprobante recibido y en revision."


@pytest.mark.asyncio
async def test_media_proof_asks_code_when_multiple_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _container = Container.get_instance()
    worker = ConversationTurnWorker(
        lock_service=_container._services["conversation_lock_service"],
        buffer_service=_container._services["message_buffer_service"],
        outbound_service=_container._services["whatsapp_outbound_service"],
    )
    sent: list[str] = []

    async def fake_find_active_candidates(_: str) -> list[Any]:
        return [SimpleNamespace(id="res-1"), SimpleNamespace(id="res-2")]

    async def fake_send(**kwargs: Any) -> Any:
        sent.append(kwargs["text"])
        return None

    monkeypatch.setattr(worker, "_find_active_candidates", fake_find_active_candidates)
    monkeypatch.setattr(worker._outbound_service, "send", fake_send)

    event = SimpleNamespace(
        wa_message_id="wamid.1",
        media_id="media-1",
        message_type="document",
        caption=None,
        raw_payload={"document": {"mime_type": "application/pdf", "filename": "proof.pdf"}},
        received_at=datetime.now(UTC),
    )
    turn = FakeTurn()

    processed = await worker._try_process_media_proof(
        events=[event],
        trace_id="tr-1",
        conversation_id="conv-1",
        normalized_phone="+573001112233",
        turn=turn,
    )

    assert processed is True
    assert "enviame el codigo de la reserva" in sent[-1].lower()
