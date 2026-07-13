from __future__ import annotations

from beanie import PydanticObjectId

from app.common.enums import NotificationChannel
from app.documents.in_app_notification_document import InAppNotificationDocument
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.notifications.provider import NotificationProvider, SendResult


class InAppNotificationProvider(NotificationProvider):
    channel = NotificationChannel.IN_APP

    async def send(self, entry: NotificationOutboxDocument) -> SendResult:
        user_id = PydanticObjectId(entry.recipient_identifier)
        doc = InAppNotificationDocument(
            user_id=user_id,
            reservation_id=entry.reservation_id,
            title=entry.subject or "Notificación",
            body=entry.rendered_body or "",
            event_type=entry.event_type,
            contact_phone=entry.contact_phone,
        )
        await doc.insert()
        return SendResult(success=True, provider_message_id=str(doc.id))

    async def validate_config(self) -> bool:
        return True
