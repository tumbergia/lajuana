from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import NOTIFICATION_PREFERENCE_KEYS, NotificationChannel, NotificationStatus
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
    reservation_id: str | None = None
    title: str
    body: str
    read: bool
    event_type: str
    contact_phone: str | None = None


class InAppUnreadCountSchema(BaseModel):
    unread_count: int = Field(ge=0)


class InAppClearResultSchema(BaseModel):
    cleared_count: int = Field(ge=0)


class NotificationPreferencesSchema(BaseModel):
    """Per-user toggles for in-app notification event types. Missing keys default to True."""

    preferences: dict[str, bool] = Field(default_factory=dict)

    @classmethod
    def from_user_prefs(cls, prefs: dict[str, bool] | None) -> "NotificationPreferencesSchema":
        stored = prefs or {}
        return cls(
            preferences={
                key: stored.get(key, True) for key in NOTIFICATION_PREFERENCE_KEYS
            }
        )


class NotificationPreferencesUpdateSchema(BaseModel):
    preferences: dict[str, bool] = Field(default_factory=dict)
