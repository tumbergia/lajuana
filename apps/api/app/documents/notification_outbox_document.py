from datetime import datetime

from beanie import Indexed, PydanticObjectId

from app.common.collections import Collections
from app.common.enums import NotificationChannel, NotificationStatus
from app.documents.base import AuditDocument


class NotificationOutboxDocument(AuditDocument):
    reservation_id: PydanticObjectId | None = None
    event_type: str
    recipient_type: str
    recipient_identifier: str
    channel: NotificationChannel
    template_key: str | None = None
    subject: str | None = None
    rendered_body: str | None = None
    status: NotificationStatus = NotificationStatus.PENDING
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    attempt_count: int = 0
    max_attempts: int = 3
    last_error: str | None = None
    provider_message_id: str | None = None
    deduplication_key: Indexed(str, unique=True, sparse=True) | None = None  # type: ignore[valid-type]

    class Settings:
        name = Collections.NOTIFICATION_OUTBOX
        indexes = [
            "status",
            "scheduled_for",
            "event_type",
            [("status", 1), ("scheduled_for", 1)],
        ]
