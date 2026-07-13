from beanie import PydanticObjectId

from app.common.collections import Collections
from app.documents.base import AuditDocument


class InAppNotificationDocument(AuditDocument):
    user_id: PydanticObjectId
    reservation_id: PydanticObjectId | None = None
    title: str
    body: str
    read: bool = False
    read_at: str | None = None
    event_type: str
    contact_phone: str | None = None

    class Settings:
        name = Collections.IN_APP_NOTIFICATIONS
        indexes = [
            "user_id",
            [("user_id", 1), ("read", 1)],
        ]
