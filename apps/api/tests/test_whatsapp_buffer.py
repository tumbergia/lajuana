from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.channels.whatsapp.normalizer import normalize_phone, build_conversation_id
from app.channels.whatsapp.parser import parse_whatsapp_payload
from app.conversations.services.conversation_lock_service import (
    ConversationLockService,
    LOCK_SECONDS,
)
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
    def __init__(self, *, body: str | None = None, media_id: str | None = None, message_type: str = "text"):
        self.body = body
        self.media_id = media_id
        self.message_type = message_type


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
    parsed = parse_whatsapp_payload(_fake_payload(phone="573001112233", messages=[("id-1", "hola")]))
    assert len(parsed) == 1
    assert parsed[0].body == "hola"
    assert parsed[0].normalized_phone == "+573001112233"


def test_parse_empty() -> None:
    assert parse_whatsapp_payload({}) == []


def test_parse_ignores_statuses() -> None:
    payload = {"entry": [{"changes": [{"value": {"statuses": [{"id": "s1"}]}}]}]}
    assert parse_whatsapp_payload(payload) == []


def test_parse_buttons() -> None:
    payload = {"entry": [{"changes": [{"value": {"messages": [{"id": "b1", "from": "57", "type": "button", "button": {"text": "Sí"}}]}}]}]}
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

    monkeypatch.setattr("app.conversations.services.message_buffer_service.MessageBufferDocument", FakeBuf)

    svc = MessageBufferService()
    buf = await svc.add_message(conversation_id="w:+57", normalized_phone="+57", channel="whatsapp", message_id="m1", body="hola")
    assert buf is not None
    assert buf.combined_preview == "hola"


@pytest.mark.asyncio
async def test_buffer_appends(monkeypatch: pytest.MonkeyPatch) -> None:
    existing = FakeDoc(
        buffer_id="b1", conversation_id="w:+57", message_ids=["m1"], combined_preview="hola",
        status="scheduled", first_message_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC),
        scheduled_for=datetime(2026, 1, 1, 0, 0, 4, tzinfo=UTC), version=1,
    )

    class FakeBuf(FakeDoc):
        @classmethod
        async def find_one(cls, *a: Any, **kw: Any) -> Any:
            filt = kw.get("filter", a[0] if a else {})
            if isinstance(filt, dict) and filt.get("conversation_id") == "w:+57":
                return existing
            return None

    monkeypatch.setattr("app.conversations.services.message_buffer_service.MessageBufferDocument", FakeBuf)

    svc = MessageBufferService()
    buf = await svc.add_message(conversation_id="w:+57", normalized_phone="+57", channel="whatsapp", message_id="m2", body="mundo")
    assert buf.message_ids == ["m1", "m2"]
    assert buf.combined_preview == "hola\nmundo"


# ── Lock service (requires MongoDB, basic integration) ──

@pytest.mark.asyncio
async def test_lock_service_acquire_release() -> None:
    from app.documents.conversation_session_document import ConversationSessionDocument

    svc = ConversationLockService()
    cid = "whatsapp:+573001112233"

    session = ConversationSessionDocument(
        channel="whatsapp", conversation_key=cid, from_phone="+573001112233",
        conversation_id=cid, normalized_phone="+573001112233",
    )
    await session.insert()

    a1 = await svc.acquire(conversation_id=cid)
    assert a1 is True

    a2 = await svc.acquire(conversation_id=cid)
    assert a2 is False

    await svc.release(conversation_id=cid)

    a3 = await svc.acquire(conversation_id=cid)
    assert a3 is True
    await svc.release(conversation_id=cid)


# ── Constants ──

def test_constants() -> None:
    assert DEBOUNCE_SECONDS == 10
    assert MAX_BUFFER_SECONDS == 30
    assert MAX_MESSAGES_PER_BUFFER == 15
    assert LOCK_SECONDS == 60
