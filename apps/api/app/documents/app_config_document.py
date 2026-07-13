from typing import Literal

from pydantic import BaseModel, Field

from app.common.collections import Collections
from app.common.constants import DEFAULT_RESERVATION_MIN_DAYS
from app.documents.base import AuditDocument


class ReservationRules(BaseModel):
    min_days_in_advance: int = DEFAULT_RESERVATION_MIN_DAYS
    require_payment_proof_for_confirmation: bool = True
    reservation_draft_ttl_minutes: int = 30
    min_age: int = 12
    max_age: int = 65


class PaymentInstructionsConfig(BaseModel):
    manual_transfer_enabled: bool = True
    account_bank: str = "Bancolombia"
    account_type: str = "Ahorros"
    account_number: str = "7165 1544 758"
    account_holder_name: str = "Jairo Ramírez Londoño"
    account_holder_id: str = "C.C. No. 10.288.647"
    transfer_note: str = "Envia el comprobante con el codigo de pre-reserva."
    bold_enabled: bool = False
    bold_checkout_url: str | None = None
    bold_surcharge_percent: float = 7
    bold_note: str = "El pago por Bold tiene una comisión adicional."


class BusinessLocationConfig(BaseModel):
    name: str = "La Juana"
    address: str = "Ruta de la Arriería, vía a Salamina"
    municipality: str = "Manizales, Caldas"
    directions: str = (
        "A 30 minutos al norte de Manizales. En el km 16 toma el desvío "
        "hacia las ruinas de la antigua fábrica de Cementos Caldas."
    )
    latitude: float = 5.152583
    longitude: float = -75.501472


AiService = Literal["gemini", "openai", "groq", "openrouter"]
AiProviderMode = Literal["env", "manual"]


class AiRouteConfig(BaseModel):
    position: int = Field(ge=1, le=3)
    service: AiService | None = None
    model: str | None = None
    encrypted_api_key: str | None = None


class AiConfigurationConfig(BaseModel):
    enabled: bool = False
    # env = Gemini + fallbacks desde variables de entorno
    # manual = rutas/modelos configurados en la UI
    provider_mode: AiProviderMode = "env"
    muted_phones: list[str] = Field(default_factory=list)
    routes: list[AiRouteConfig] = Field(
        default_factory=lambda: [AiRouteConfig(position=i) for i in range(1, 4)]
    )


class AutomationConfig(BaseModel):
    birthday_messages_enabled: bool = False
    anniversary_messages_enabled: bool = False


class AppConfigDocument(AuditDocument):
    key: str
    reservation_rules: ReservationRules | None = None
    payment_instructions: PaymentInstructionsConfig | None = None
    business_location: BusinessLocationConfig | None = None
    ai_configuration: AiConfigurationConfig | None = None
    automation: AutomationConfig | None = None

    class Settings:
        name = Collections.APP_CONFIG
