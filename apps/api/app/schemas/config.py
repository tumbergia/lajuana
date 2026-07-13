from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator


class EmergencyCatalogContactSchema(BaseModel):
    code: str
    name: str
    description: str
    phone_number: str
    category: str
    is_primary: bool
    is_national: bool


class EmergencyContactsResponseSchema(BaseModel):
    items: list[EmergencyCatalogContactSchema]


class ReservationRulesSchema(BaseModel):
    min_days_in_advance: int = Field(ge=0)
    require_payment_proof_for_confirmation: bool = True
    reservation_draft_ttl_minutes: int = Field(default=30, ge=5, le=1440)
    min_age: int = Field(default=12, ge=0)
    max_age: int = Field(default=65, ge=0)


class ReservationRulesUpdateSchema(BaseModel):
    min_days_in_advance: int | None = Field(default=None, ge=0)
    require_payment_proof_for_confirmation: bool | None = None
    reservation_draft_ttl_minutes: int | None = Field(default=None, ge=5, le=1440)
    min_age: int | None = Field(default=None, ge=0)
    max_age: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_age_range(self) -> "ReservationRulesUpdateSchema":
        if self.min_age is not None and self.max_age is not None and self.min_age > self.max_age:
            raise ValueError("min_age no puede ser mayor que max_age")
        return self


class PaymentInstructionsSchema(BaseModel):
    manual_transfer_enabled: bool
    account_bank: str
    account_type: str
    account_number: str
    account_holder_name: str
    account_holder_id: str
    transfer_note: str
    bold_enabled: bool
    bold_checkout_url: str | None = None
    bold_surcharge_percent: float
    bold_note: str


class PaymentInstructionsUpdateSchema(BaseModel):
    manual_transfer_enabled: bool = True
    account_bank: str = Field(default="Bancolombia", min_length=1, max_length=100)
    account_type: str = Field(default="Ahorros", min_length=1, max_length=30)
    account_number: str = Field(default="7165 1544 758", min_length=4, max_length=40)
    account_holder_name: str = Field(default="Jairo Ramírez Londoño", min_length=1, max_length=150)
    account_holder_id: str = Field(default="C.C. No. 10.288.647", min_length=1, max_length=80)
    transfer_note: str = Field(
        default="Envia el comprobante con el codigo de pre-reserva.", max_length=500
    )
    bold_enabled: bool = False
    bold_checkout_url: HttpUrl | None = None
    bold_surcharge_percent: float = Field(default=7, ge=0, le=30)
    bold_note: str = Field(default="El pago por Bold tiene una comisión adicional.", max_length=500)

    @model_validator(mode="after")
    def validate_methods(self) -> "PaymentInstructionsUpdateSchema":
        provided = self.model_fields_set
        if (
            {"manual_transfer_enabled", "bold_enabled"}.issubset(provided)
            and not self.manual_transfer_enabled
            and not self.bold_enabled
        ):
            raise ValueError("Debe existir al menos un método de pago activo")
        if (
            {"bold_enabled", "bold_checkout_url"}.issubset(provided)
            and self.bold_enabled
            and self.bold_checkout_url is None
        ):
            raise ValueError("El enlace Bold es obligatorio cuando Bold está activo")
        return self


class BusinessLocationSchema(BaseModel):
    name: str
    address: str
    municipality: str
    directions: str
    latitude: float
    longitude: float
    google_maps_url: str


class BusinessLocationUpdateSchema(BaseModel):
    name: str = Field(default="La Juana", min_length=1, max_length=120)
    address: str = Field(
        default="Ruta de la Arriería, vía a Salamina", min_length=1, max_length=300
    )
    municipality: str = Field(default="Manizales, Caldas", min_length=1, max_length=120)
    directions: str = Field(default="", max_length=1000)
    latitude: float = Field(default=5.152583, ge=-90, le=90)
    longitude: float = Field(default=-75.501472, ge=-180, le=180)


AiService = Literal["gemini", "openai", "groq", "openrouter"]


class AiRouteSchema(BaseModel):
    position: int = Field(ge=1, le=3)
    service: AiService | None = None
    model: str | None = None
    credential_configured: bool = False


class AiConfigurationSchema(BaseModel):
    enabled: bool
    source: str
    routes: list[AiRouteSchema]
    version: int = 1
    updated_at: datetime | None = None


class AiRouteUpdateSchema(BaseModel):
    position: int = Field(ge=1, le=3)
    service: AiService | None = None
    model: str | None = Field(default=None, max_length=150)
    api_key: SecretStr | None = None
    clear_api_key: bool = False


class AiConfigurationUpdateSchema(BaseModel):
    enabled: bool = False
    routes: list[AiRouteUpdateSchema]
    expected_version: int | None = None

    @model_validator(mode="after")
    def validate_routes(self) -> "AiConfigurationUpdateSchema":
        if len(self.routes) != 3 or {r.position for r in self.routes} != {1, 2, 3}:
            raise ValueError("Se requieren exactamente tres rutas en posiciones 1, 2 y 3")
        if self.enabled:
            for route in self.routes:
                if route.service is None or not (route.model or "").strip():
                    raise ValueError("Las tres rutas deben tener servicio y modelo para activar IA")
        return self


class ConfigurationSummarySchema(BaseModel):
    reservation_rules_configured: bool
    ai_enabled: bool
    ai_source: str
    payment_methods_enabled: list[str]
    location_configured: bool
