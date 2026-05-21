import asyncio

import pytest

from app.common.enums import NotificationChannel
from app.notifications.in_app_provider import InAppNotificationProvider
from app.notifications.whatsapp_provider import WhatsAppNotificationProvider


class _FakeDoc:
    def __init__(self, **kwargs: object) -> None:
        self.id = "660000000000000000000001"
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakeInAppDoc:
    def __init__(self, **kwargs: object) -> None:
        self.id = "660000000000000000000010"
        self.user_id = "660000000000000000000010"
        self.reservation_id = None
        self.title = "Test"
        self.body = "Body"
        self.read = False
        self.event_type = "test"
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        return None


def test_in_app_provider_creates_document(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.notifications.in_app_provider.InAppNotificationDocument",
        _FakeInAppDoc,
    )

    provider = InAppNotificationProvider()
    entry = _FakeDoc(
        event_type="test",
        recipient_type="internal",
        recipient_identifier="660000000000000000000010",
        channel=NotificationChannel.IN_APP,
        subject="Test Title",
        rendered_body="Test body content",
        status="pending",
        reservation_id=None,
    )
    result = asyncio.run(provider.send(entry))
    assert result.success
    assert result.provider_message_id is not None


def test_in_app_provider_validate() -> None:
    provider = InAppNotificationProvider()
    result = asyncio.run(provider.validate_config())
    assert result is True


def test_whatsapp_provider_not_implemented() -> None:
    provider = WhatsAppNotificationProvider()
    assert provider.channel == NotificationChannel.WHATSAPP
    with pytest.raises(NotImplementedError):
        asyncio.run(provider.send(None))  # type: ignore[arg-type]


def test_whatsapp_provider_validate() -> None:
    provider = WhatsAppNotificationProvider()
    result = asyncio.run(provider.validate_config())
    assert result is False


def test_email_provider_validate_no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.email_user", "")
    monkeypatch.setattr("app.core.config.settings.email_pass", "")
    from app.notifications.email_provider import EmailProvider

    provider = EmailProvider()
    result = asyncio.run(provider.validate_config())
    assert result is False
