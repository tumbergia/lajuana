from datetime import datetime

from beanie import Indexed
from pydantic import EmailStr, Field

from app.common.collections import Collections
from app.common.enums import UserRole
from app.documents.base import AuditDocument


class UserDocument(AuditDocument):
    email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    password_hash: str
    full_name: str = Field(min_length=3, max_length=120)
    role: UserRole = UserRole.UNASSIGNED
    is_active: bool = True
    last_login_at: datetime | None = None
    refresh_token_hash: str | None = None
    # event_type -> enabled. Missing keys default to True (all on).
    notification_preferences: dict[str, bool] = Field(default_factory=dict)
    # Home leads (legacy): { "pinned_lead_ids": [...], "excluded_lead_ids": [...] }
    leads_preferences: dict = Field(default_factory=dict)
    # Analytics v2: { schema_version, selected_module_ids, module_order, default_range, updated_at }
    analytics_preferences: dict = Field(default_factory=dict)

    class Settings:
        name = Collections.USERS

    def prefers_notification(self, event_type: str) -> bool:
        """Return whether this user wants in-app notifications for an event type."""
        return self.notification_preferences.get(event_type, True)
