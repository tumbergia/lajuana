from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import NotificationChannel, NotificationStatus
from app.schemas.common import AuditMetadataSchema


class NotificationTemplateCreateSchema(BaseModel):
    template_key: str
    channel: NotificationChannel
    language: str = "es"
    subject: str | None = None
    body: str
    variables_allowed: list[str] = Field(default_factory=list)


class NotificationTemplateUpdateSchema(BaseModel):
    channel: NotificationChannel | None = None
    language: str | None = None
    subject: str | None = None
    body: str | None = None
    variables_allowed: list[str] | None = None
    is_active: bool | None = None


class NotificationTemplateResponseSchema(AuditMetadataSchema):
    id: str
    template_key: str
    channel: NotificationChannel
    language: str
    subject: str | None
    body: str
    variables_allowed: list[str]
    is_active: bool


class NotificationOutboxResponseSchema(AuditMetadataSchema):
    id: str
    reservation_id: str | None
    event_type: str
    recipient_type: str
    recipient_identifier: str
    channel: NotificationChannel
    template_key: str | None
    subject: str | None
    status: NotificationStatus
    scheduled_for: datetime | None
    sent_at: datetime | None
    attempt_count: int
    last_error: str | None
    provider_message_id: str | None


class NotificationOutboxListSchema(BaseModel):
    id: str
    event_type: str
    recipient_type: str
    channel: NotificationChannel
    status: NotificationStatus
    scheduled_for: datetime | None
    sent_at: datetime | None
    attempt_count: int
    last_error: str | None
    created_at: datetime


class InAppNotificationResponseSchema(AuditMetadataSchema):
    id: str
    user_id: str
    reservation_id: str | None
    title: str
    body: str
    read: bool
    event_type: str
