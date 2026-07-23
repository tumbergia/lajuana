from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.channels.whatsapp.normalizer import build_conversation_id, normalize_phone
from app.channels.whatsapp.parser import parse_whatsapp_payload
from app.conversations.services.conversation_lock_service import LOCK_SECONDS  # noqa: F401  # backward-compat
from app.conversations.services.conversation_turn_worker import combine_messages
from app.conversations.services.message_buffer_service import (
    DEBOUNCE_SECONDS,
    MAX_BUFFER_SECONDS,
    MAX_MESSAGES_PER_BUFFER,
    MessageBufferService,
)


def _fake_payload(*, phone: str, messages: list[tuple[str, str]]) -> dict:
    raw = []
    for mid, txt in messages:
        raw.append({"id": mid, "from": phone, "type": "text", "text": {"body": txt}})
    return {"entry": [{"changes": [{"value": {"messages": raw}}]}]}


class FakeDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = str(uuid4())

    async def save(self) -> None:
        pass

    @classmethod
    async def find_one(cls, *args: Any, **kwargs: Any) -> Any:
        return None


class FakeEvent:
    def __init__(  # noqa: E501
        self,
        *,
        body: str | None = None,
        media_id: str | None = None,
        message_type: str = "text",
        transcription: str | None = None,
    ):
        self.body = body
        self.media_id = media_id
        self.message_type = message_type
        self.transcription = transcription


# ── Normalizer ──


def test_normalize_phone() -> None:
    assert normalize_phone("+57 (300) 111-22-33") == "+573001112233"


def test_normalize_phone_raises_on_empty() -> None:
    with pytest.raises(ValueError):
        normalize_phone("")


def test_build_conversation_id() -> None:
    assert build_conversation_id("whatsapp", "+573001112233") == "whatsapp:+573001112233"


# ── Parser ──


def test_parse_text() -> None:
    payload = _fake_payload(phone="573001112233", messages=[("id-1", "hola")])
    parsed = parse_whatsapp_payload(payload)
    assert len(parsed) == 1
    assert parsed[0].body == "hola"
    assert parsed[0].normalized_phone == "+573001112233"


def test_parse_empty() -> None:
    assert parse_whatsapp_payload({}) == []


def test_parse_ignores_statuses() -> None:
    payload = {"entry": [{"changes": [{"value": {"statuses": [{"id": "s1"}]}}]}]}
    assert parse_whatsapp_payload(payload) == []


def test_parse_buttons() -> None:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "b1",
                                    "from": "57",
                                    "type": "button",
                                    "button": {"text": "Sí"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    parsed = parse_whatsapp_payload(payload)
    assert parsed[0].body == "Sí"


# ── Combine messages ──


def test_combine_single() -> None:
    assert combine_messages([FakeEvent(body="hola")]) == "hola"


def test_combine_multiple() -> None:
    msgs = [FakeEvent(body=s) for s in ["sí", "hola", "necesito", "la más", "barata"]]
    assert combine_messages(msgs) == "sí\nhola\nnecesito\nla más\nbarata"


# ── Buffer service ──


@pytest.mark.asyncio
async def test_buffer_creates_new(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeBuf(FakeDoc):
        async def insert(self) -> None:
            self.id = "b1"
            self.buffer_id = str(uuid4())

    monkeypatch.setattr(  # noqa: E501
        "app.conversations.services.message_buffer_service.MessageBufferDocument", FakeBuf
    )

    svc = MessageBufferService()
    buf = await svc.add_message(
        conversation_id="w:+57",
        normalized_phone="+57",
        channel="whatsapp",
        message_id="m1",
        body="hola",
    )
    assert buf is not None
    assert buf.combined_preview == "hola"


@pytest.mark.asyncio
async def test_buffer_appends(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime.now(UTC)
    existing = FakeDoc(
        buffer_id="b1",
        conversation_id="w:+57",
        message_ids=["m1"],
        combined_preview="hola",
        status="scheduled",
        first_message_at=now,
        last_message_at=now,
        scheduled_for=now + timedelta(seconds=4),
        version=1,
    )

    class FakeBuf(FakeDoc):
        @classmethod
        async def find_one(cls, *a: Any, **kw: Any) -> Any:
            filt = kw.get("filter", a[0] if a else {})
            if isinstance(filt, dict) and filt.get("conversation_id") == "w:+57":
                return existing
            return None

    monkeypatch.setattr(  # noqa: E501
        "app.conversations.services.message_buffer_service.MessageBufferDocument", FakeBuf
    )

    svc = MessageBufferService()
    buf = await svc.add_message(
        conversation_id="w:+57",
        normalized_phone="+57",
        channel="whatsapp",
        message_id="m2",
        body="mundo",
    )
    assert buf.message_ids == ["m1", "m2"]
    assert buf.combined_preview == "hola\nmundo"


# ── Constants ──


def test_constants() -> None:
    assert DEBOUNCE_SECONDS == 10
    assert MAX_BUFFER_SECONDS == 30
    assert MAX_MESSAGES_PER_BUFFER == 15
    # LOCK_SECONDS es el valor legacy de la constante importada. Hoy se
    # sigue exponiendo por compatibilidad, pero el valor operativo real
    # está en settings.buffer_lock_seconds (default 90s para turnos
    # legítimamente largos sin perder el lock).
    assert LOCK_SECONDS == 90
