from pydantic import BaseModel

from app.common.collections import Collections
from app.common.constants import DEFAULT_RESERVATION_MIN_DAYS
from app.documents.base import AuditDocument


class ReservationRules(BaseModel):
    min_days_in_advance: int = DEFAULT_RESERVATION_MIN_DAYS
    require_payment_proof_for_confirmation: bool = True
    reservation_draft_ttl_minutes: int = 30


class PaymentInstructionsConfig(BaseModel):
    account_bank: str = "Bancolombia"
    account_type: str = "Ahorros"
    account_number: str = "00000000000"
    account_holder_name: str = "La Juana"
    account_holder_id: str = "NIT 000000000-0"
    transfer_note: str = "Envia el comprobante con el codigo de pre-reserva."


class AutomationConfig(BaseModel):
    birthday_messages_enabled: bool = False
    anniversary_messages_enabled: bool = False


class AppConfigDocument(AuditDocument):
    key: str
    reservation_rules: ReservationRules | None = None
    payment_instructions: PaymentInstructionsConfig | None = None
    automation: AutomationConfig | None = None

    class Settings:
        name = Collections.APP_CONFIG
