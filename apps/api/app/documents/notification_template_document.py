from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.collections import Collections
from app.common.enums import NotificationChannel
from app.documents.base import AuditDocument


class NotificationTemplateDocument(AuditDocument):
    template_key: str
    channel: NotificationChannel
    language: str = "es"
    subject: str | None = None
    body: str
    variables_allowed: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_by: str | None = None
    updated_by: str | None = None

    class Settings:
        name = Collections.NOTIFICATION_TEMPLATES
        indexes = [
            IndexModel(
                [("template_key", ASCENDING), ("channel", ASCENDING)],
                unique=True,
                name="uq_notification_template_key_channel",
            ),
        ]
