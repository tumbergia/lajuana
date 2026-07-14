"""Unit tests for admin in-app fan-out, preferences and mark-as-read helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.common.enums import (
    NOTIFICATION_PREFERENCE_KEYS,
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
)
from app.documents.user_document import UserDocument
from app.schemas.notification import NotificationPreferencesSchema


class _FakeOutboxDoc:
    inserted: list["_FakeOutboxDoc"] = []

    def __init__(self, **kwargs: object) -> None:
        self.id = kwargs.get("id", "outbox-1")
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def insert(self) -> None:
        _FakeOutboxDoc.inserted.append(self)

    async def save(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _reset_outbox() -> None:
    _FakeOutboxDoc.inserted.clear()


def test_user_prefers_notification_defaults_true() -> None:
    user = UserDocument.model_construct(
        email="a@test.com",
        password_hash="x",
        full_name="Admin",
        notification_preferences={},
    )
    assert user.prefers_notification(NotificationEventType.RESERVATION_CREATED.value) is True


def test_user_prefers_notification_respects_false() -> None:
    user = UserDocument.model_construct(
        email="a@test.com",
        password_hash="x",
        full_name="Admin",
        notification_preferences={
            NotificationEventType.WHATSAPP_MESSAGE_UNATTENDED.value: False,
        },
    )
    assert (
        user.prefers_notification(NotificationEventType.WHATSAPP_MESSAGE_UNATTENDED.value)
        is False
    )
    assert user.prefers_notification(NotificationEventType.RESERVATION_CREATED.value) is True


def test_preferences_schema_fills_defaults() -> None:
    schema = NotificationPreferencesSchema.from_user_prefs(
        {NotificationEventType.CONFIGURATION_CHANGED.value: False}
    )
    assert set(schema.preferences.keys()) == set(NOTIFICATION_PREFERENCE_KEYS)
    assert schema.preferences[NotificationEventType.CONFIGURATION_CHANGED.value] is False
    assert schema.preferences[NotificationEventType.RESERVATION_CREATED.value] is True


@pytest.mark.asyncio
async def test_enqueue_admin_in_app_excludes_actor_and_prefs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.notification_service import NotificationService

    actor = SimpleNamespace(
        id="aaaaaaaaaaaaaaaaaaaaaaaa",
        prefers_notification=lambda _e: True,
    )
    muted = SimpleNamespace(
        id="bbbbbbbbbbbbbbbbbbbbbbbb",
        prefers_notification=lambda event: event
        != NotificationEventType.PAYMENT_PROOF_REGISTERED.value,
    )
    eligible = SimpleNamespace(
        id="cccccccccccccccccccccccc",
        prefers_notification=lambda _e: True,
    )

    monkeypatch.setattr(
        "app.services.notification_service.UserDocument.find",
        lambda *_a, **_k: SimpleNamespace(
            to_list=AsyncMock(return_value=[actor, muted, eligible])
        ),
    )

    enqueued: list[dict] = []

    async def _fake_enqueue(**kwargs: object) -> object:
        enqueued.append(kwargs)
        return SimpleNamespace(id="outbox")

    svc = NotificationService()
    monkeypatch.setattr(svc, "enqueue", _fake_enqueue)

    result = await svc.enqueue_admin_in_app(
        event_type=NotificationEventType.PAYMENT_PROOF_REGISTERED,
        title="Nuevo comprobante",
        body="Cliente — RES-1",
        reservation_id="dddddddddddddddddddddddd",
        actor_user_id=str(actor.id),
        dedup_suffix="proof-1",
    )

    assert len(result) == 1
    assert len(enqueued) == 1
    assert enqueued[0]["recipient_identifier"] == str(eligible.id)
    assert enqueued[0]["channel"] == NotificationChannel.IN_APP
    assert enqueued[0]["skip_template"] is True
    assert enqueued[0]["subject"] == "Nuevo comprobante"
    assert "proof-1" in str(enqueued[0]["dedup_suffix"])


@pytest.mark.asyncio
async def test_enqueue_skip_template_writes_subject_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import notification_service as ns

    async def _find_one(*_a: object, **_k: object) -> None:
        return None

    _FakeOutboxDoc.find_one = staticmethod(_find_one)  # type: ignore[attr-defined]
    monkeypatch.setattr(ns, "NotificationOutboxDocument", _FakeOutboxDoc)

    svc = ns.NotificationService()
    entry = await svc.enqueue(
        event_type=NotificationEventType.HUMAN_REVIEW_REQUESTED,
        reservation_id=None,
        channel=NotificationChannel.IN_APP,
        recipient_type="internal",
        recipient_identifier="cccccccccccccccccccccccc",
        subject="Atención humana",
        body="Cliente pide ayuda",
        skip_template=True,
        dedup_suffix="review-1",
    )

    assert entry.subject == "Atención humana"
    assert entry.rendered_body == "Cliente pide ayuda"
    assert entry.template_key is None
    assert entry.reservation_id is None
    assert entry.status == NotificationStatus.PENDING


@pytest.mark.asyncio
async def test_whatsapp_failure_enqueues_admin_alert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.notifications.provider import SendResult
    from app.services.notification_service import NotificationService

    class _FailProvider:
        async def send(self, entry: object) -> SendResult:
            return SendResult(success=False, error_code="fail", error_detail="boom")

        async def validate_config(self) -> bool:
            return True

    svc = NotificationService()
    svc._providers[NotificationChannel.WHATSAPP] = _FailProvider()

    called: list[dict] = []

    async def _fake_admin(**kwargs: object) -> list:
        called.append(kwargs)
        return []

    monkeypatch.setattr(svc, "enqueue_admin_in_app", _fake_admin)

    entry = SimpleNamespace(
        id="outbox-fail",
        channel=NotificationChannel.WHATSAPP,
        status=NotificationStatus.PENDING,
        event_type="reservation_cancelled",
        subject="Cancelación",
        recipient_identifier="+573001112233",
        reservation_id="dddddddddddddddddddddddd",
        attempt_count=2,
        max_attempts=3,
        last_error=None,
        sent_at=None,
        provider_message_id=None,
        save=AsyncMock(),
    )

    await svc.send_from_outbox(entry)
    assert entry.status == NotificationStatus.FAILED
    assert len(called) == 1
    assert called[0]["event_type"] == NotificationEventType.WHATSAPP_DELIVERY_FAILED
    assert called[0]["contact_phone"] == "+573001112233"


@pytest.mark.asyncio
async def test_enqueue_passes_contact_phone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import notification_service as ns

    async def _find_one(*_a: object, **_k: object) -> None:
        return None

    _FakeOutboxDoc.find_one = staticmethod(_find_one)  # type: ignore[attr-defined]
    monkeypatch.setattr(ns, "NotificationOutboxDocument", _FakeOutboxDoc)

    svc = ns.NotificationService()
    entry = await svc.enqueue(
        event_type=NotificationEventType.WHATSAPP_MESSAGE_UNATTENDED,
        reservation_id=None,
        channel=NotificationChannel.IN_APP,
        recipient_type="internal",
        recipient_identifier="cccccccccccccccccccccccc",
        subject="WhatsApp",
        body="+573001112233: hola",
        skip_template=True,
        contact_phone="+573001112233",
        dedup_suffix="wa-1",
    )

    assert entry.contact_phone == "+573001112233"


@pytest.mark.asyncio
async def test_clear_in_app_soft_deletes_and_excludes_from_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import UTC, datetime

    from app.api.endpoints import notifications as endpoints

    now = datetime.now(UTC)

    class _FakeDoc:
        def __init__(self, **kwargs: object) -> None:
            self.id = kwargs.get("id", "n1")
            self.user_id = kwargs["user_id"]
            self.read = kwargs.get("read", False)
            self.deleted_at = kwargs.get("deleted_at")
            self.title = "t"
            self.body = "b"
            self.event_type = "reservation_created"
            self.reservation_id = None
            self.contact_phone = None
            self.version = 1
            self.created_at = now
            self.updated_at = now
            self.read_at = None

        async def save(self) -> None:
            return None

    user = SimpleNamespace(id="aaaaaaaaaaaaaaaaaaaaaaaa")
    docs = [
        _FakeDoc(id="n1", user_id=user.id, read=True),
        _FakeDoc(id="n2", user_id=user.id, read=False),
    ]

    class _FindResult:
        def __init__(self, matched: list[_FakeDoc]) -> None:
            self._matched = matched

        async def update_many(self, update: dict) -> SimpleNamespace:
            for doc in self._matched:
                for key, value in update.get("$set", {}).items():
                    setattr(doc, key, value)
            return SimpleNamespace(modified_count=len(self._matched))

        def sort(self, *_a: object, **_k: object) -> "_FindResult":
            return self

        def limit(self, *_a: object, **_k: object) -> "_FindResult":
            return self

        async def to_list(self) -> list[_FakeDoc]:
            return list(self._matched)

        async def count(self) -> int:
            return len(self._matched)

    def _find(query: dict) -> _FindResult:
        matched = []
        for doc in docs:
            if doc.user_id != query.get("user_id"):
                continue
            if "deleted_at" in query and query["deleted_at"] is None and doc.deleted_at is not None:
                continue
            if "read" in query and doc.read != query["read"]:
                continue
            matched.append(doc)
        return _FindResult(matched)

    monkeypatch.setattr(endpoints.InAppNotificationDocument, "find", staticmethod(_find))

    cleared = await endpoints.clear_in_app_notifications(current_user=user, read_only=True)
    assert cleared.cleared_count == 1
    assert docs[0].deleted_at is not None
    assert docs[1].deleted_at is None

    listed = await endpoints.list_in_app(
        current_user=user,
        limit=50,
        before_id=None,
        unread_only=False,
    )
    assert [item.id for item in listed] == ["n2"]

    unread = await endpoints.get_in_app_unread_count(current_user=user)
    assert unread.unread_count == 1


@pytest.mark.asyncio
async def test_delete_in_app_notification_soft_deletes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import UTC, datetime

    from app.api.endpoints import notifications as endpoints

    user = SimpleNamespace(id="aaaaaaaaaaaaaaaaaaaaaaaa")
    doc = SimpleNamespace(
        id="n1",
        user_id=user.id,
        deleted_at=None,
        read=False,
        title="t",
        body="b",
        event_type="reservation_created",
        reservation_id=None,
        contact_phone="+57300",
        version=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        read_at=None,
        save=AsyncMock(),
    )

    async def _get(_id: str) -> object:
        return doc

    monkeypatch.setattr(endpoints.InAppNotificationDocument, "get", staticmethod(_get))

    result = await endpoints.delete_in_app_notification(
        notification_id="n1",
        current_user=user,
    )
    assert result.cleared_count == 1
    assert doc.deleted_at is not None
    doc.save.assert_awaited()
