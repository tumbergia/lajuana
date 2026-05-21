from __future__ import annotations

from app.common.enums import NotificationChannel
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.notifications.provider import NotificationProvider, SendResult


class WhatsAppNotificationProvider(NotificationProvider):
    channel = NotificationChannel.WHATSAPP

    async def send(self, entry: NotificationOutboxDocument) -> SendResult:
        raise NotImplementedError("WhatsApp provider not implemented yet.")

    async def validate_config(self) -> bool:
        return False
