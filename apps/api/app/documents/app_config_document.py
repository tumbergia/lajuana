from pydantic import BaseModel

from app.common.collections import Collections
from app.common.constants import DEFAULT_RESERVATION_MIN_DAYS
from app.documents.base import AuditDocument


class ReservationRules(BaseModel):
    min_days_in_advance: int = DEFAULT_RESERVATION_MIN_DAYS
    require_payment_proof_for_confirmation: bool = True


class AutomationConfig(BaseModel):
    birthday_messages_enabled: bool = False
    anniversary_messages_enabled: bool = False


class AppConfigDocument(AuditDocument):
    key: str
    reservation_rules: ReservationRules | None = None
    automation: AutomationConfig | None = None

    class Settings:
        name = Collections.APP_CONFIG
