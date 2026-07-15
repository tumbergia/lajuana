import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.common.enums import NotificationChannel, NotificationStatus
from app.notifications.renderer import render_subject, render_template


def test_render_template() -> None:
    result = render_template("Hola {{name}}, tu código es {{code}}", {"name": "Juan", "code": "ABC"})
    assert result == "Hola Juan, tu código es ABC"


def test_render_template_missing_variable_keeps_placeholder() -> None:
    result = render_template("Hola {{name}}", {})
    assert result == "Hola {{name}}"


def test_render_subject() -> None:
    result = render_subject("Notif {{code}}", {"code": "RES-123"})
    assert result == "Notif RES-123"


def test_render_subject_none() -> None:
    result = render_subject(None, {})
    assert result is None


class _FakeProvider:
    def __init__(self) -> None:
        self.sent: list[object] = []
        self.channel = NotificationChannel.EMAIL
        self.should_fail = False

    async def send(self, entry: object) -> object:
        from app.notifications.provider import SendResult

        self.sent.append(entry)
        if self.should_fail:
            return SendResult(success=False, error_code="test_error", error_detail="Simulated failure")
        return SendResult(success=True, provider_message_id="fake-msg-id")

    async def validate_config(self) -> bool:
        return True


class _FakeDoc:
    def __init__(self, **kwargs: object) -> None:
        self.id = "660000000000000000000001"
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        return None

    async def save(self) -> None:
        return None


class _FakeOutboxStoreDoc(_FakeDoc):
    inserted: list["_FakeOutboxStoreDoc"] = []

    @classmethod
    async def find_one(cls, query: dict[str, object]) -> "_FakeOutboxStoreDoc | None":
        dedup_key = query["deduplication_key"]
        for doc in cls.inserted:
            if doc.deduplication_key == dedup_key and doc.status != NotificationStatus.CANCELLED:
                return doc
        return None

    async def insert(self) -> None:
        self.__class__.inserted.append(self)


def test_build_customer_vars() -> None:
    from app.services.notification_service import NotificationService

    svc = NotificationService()

    class _FakeReservation:
        def __init__(self) -> None:
            self.id = "660000000000000000000001"
            self.code = "RES-001"
            self.holder_name = "Juan Perez"
            self.holder_email = "juan@test.com"
            self.participant_count = 4
            self.completed_at = datetime(2026, 6, 1, 14, 0, tzinfo=UTC)

    vars = svc._build_customer_vars(_FakeReservation())
    assert vars["customer_name"] == "Juan Perez"
    assert vars["reservation_code"] == "RES-001"
    assert vars["participants_count"] == "4"


def test_send_from_outbox_marks_sent() -> None:
    from app.services.notification_service import NotificationService

    svc = NotificationService()
    fake_provider = _FakeProvider()
    svc._providers[NotificationChannel.EMAIL] = fake_provider

    entry = _FakeDoc(
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
        event_type="test",
        recipient_type="customer",
        recipient_identifier="test@example.com",
        attempt_count=0,
        max_attempts=3,
        last_error=None,
        sent_at=None,
        provider_message_id=None,
    )

    save_called = False

    async def _fake_save() -> None:
        nonlocal save_called
        save_called = True

    entry.save = _fake_save
    asyncio.run(svc.send_from_outbox(entry))  # type: ignore[arg-type]
    assert entry.status == NotificationStatus.SENT
    assert entry.sent_at is not None
    assert save_called


def test_send_from_outbox_failure_retries() -> None:
    from app.services.notification_service import NotificationService

    svc = NotificationService()
    fake_provider = _FakeProvider()
    fake_provider.should_fail = True
    svc._providers[NotificationChannel.EMAIL] = fake_provider

    entry = _FakeDoc(
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
        event_type="test",
        recipient_type="customer",
        recipient_identifier="test@example.com",
        attempt_count=0,
        max_attempts=3,
        last_error=None,
        sent_at=None,
        provider_message_id=None,
    )

    async def _fake_save() -> None:
        pass

    entry.save = _fake_save
    asyncio.run(svc.send_from_outbox(entry))  # type: ignore[arg-type]
    assert entry.status == NotificationStatus.PENDING
    assert entry.attempt_count == 1
    assert entry.last_error == "Simulated failure"


def test_send_from_outbox_exhausts_retries() -> None:
    from app.services.notification_service import NotificationService

    svc = NotificationService()
    fake_provider = _FakeProvider()
    fake_provider.should_fail = True
    svc._providers[NotificationChannel.EMAIL] = fake_provider

    entry = _FakeDoc(
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
        event_type="test",
        recipient_type="customer",
        recipient_identifier="test@example.com",
        attempt_count=0,
        max_attempts=1,
        last_error=None,
        sent_at=None,
        provider_message_id=None,
    )

    async def _fake_save() -> None:
        pass

    entry.save = _fake_save
    asyncio.run(svc.send_from_outbox(entry))  # type: ignore[arg-type]
    assert entry.status == NotificationStatus.FAILED
    assert entry.attempt_count == 1


def test_send_from_outbox_provider_exception_recovers() -> None:
    from app.services.notification_service import NotificationService

    class _CrashProvider:
        async def send(self, _entry: object) -> object:
            raise RuntimeError("boom")

        async def validate_config(self) -> bool:
            return True

    svc = NotificationService()
    svc._providers[NotificationChannel.EMAIL] = _CrashProvider()

    entry = _FakeDoc(
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
        event_type="test",
        recipient_type="customer",
        recipient_identifier="test@example.com",
        attempt_count=0,
        max_attempts=3,
        last_error=None,
        sent_at=None,
        provider_message_id=None,
    )

    save_calls = 0

    async def _fake_save() -> None:
        nonlocal save_calls
        save_calls += 1

    entry.save = _fake_save
    asyncio.run(svc.send_from_outbox(entry))  # type: ignore[arg-type]
    assert entry.status == NotificationStatus.PENDING
    assert entry.attempt_count == 1
    assert entry.last_error == "boom"
    assert save_calls == 2


@pytest.mark.asyncio
async def test_enqueue_payment_received_keeps_each_recipient_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.common.enums import NotificationEventType, UserRole
    from app.services import notification_service as ns

    async def _find_template(*_a: object, **_k: object) -> None:
        return None

    async def _list_admins() -> list[SimpleNamespace]:
        return [
            SimpleNamespace(
                id="660000000000000000000010",
                email="admin1@test.com",
                role=UserRole.ADMIN,
            ),
            SimpleNamespace(
                id="660000000000000000000011",
                email="admin2@test.com",
                role=UserRole.ADMIN,
            ),
        ]

    _FakeOutboxStoreDoc.inserted.clear()
    monkeypatch.setattr(ns, "NotificationOutboxDocument", _FakeOutboxStoreDoc)
    monkeypatch.setattr(ns.NotificationTemplateDocument, "find_one", staticmethod(_find_template))
    monkeypatch.setattr(
        ns.UserDocument,
        "find",
        lambda *_a, **_k: SimpleNamespace(to_list=_list_admins),
    )

    reservation = SimpleNamespace(
        id="660000000000000000000099",
        code="RES-99",
        holder_name="Juan Perez",
        holder_email="juan@test.com",
        participant_count=2,
        completed_at=None,
    )

    svc = ns.NotificationService()
    entries = await svc.enqueue_payment_received(reservation)

    assert len(entries) == 4
    assert len(_FakeOutboxStoreDoc.inserted) == 4
    assert {entry.recipient_identifier for entry in entries} == {
        "admin1@test.com",
        "admin2@test.com",
        "660000000000000000000010",
        "660000000000000000000011",
    }
    assert all(
        entry.event_type == NotificationEventType.RESERVATION_CONFIRMED.value for entry in entries
    )


def test_get_provider_returns_correct_provider() -> None:
    from app.services.notification_service import NotificationService

    svc = NotificationService()
    provider = svc.get_provider(NotificationChannel.EMAIL)
    from app.notifications.email_provider import EmailProvider

    assert isinstance(provider, EmailProvider)

    in_app = svc.get_provider(NotificationChannel.IN_APP)
    from app.notifications.in_app_provider import InAppNotificationProvider

    assert isinstance(in_app, InAppNotificationProvider)

    wa = svc.get_provider(NotificationChannel.WHATSAPP)
    from app.notifications.whatsapp_provider import WhatsAppNotificationProvider

    assert isinstance(wa, WhatsAppNotificationProvider)


def test_process_pending_batch_calls_send(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.notification_service import NotificationService

    svc = NotificationService()

    sent_entries: list[object] = []

    async def _fake_send(entry: object) -> None:
        sent_entries.append(entry)

    class _FakeQuery:
        def sort(self, _: str) -> "_FakeQuery":
            return self

        def limit(self, _: int) -> "_FakeQuery":
            return self

        async def to_list(self) -> list[object]:
            return [_FakeDoc(
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.PENDING,
            )]

    monkeypatch.setattr(
        "app.services.notification_service.NotificationOutboxDocument.find",
        lambda *a, **kw: _FakeQuery(),
    )
    monkeypatch.setattr(svc, "send_from_outbox", _fake_send)

    count = asyncio.run(svc.process_pending_batch())
    assert count == 1
    assert len(sent_entries) == 1
