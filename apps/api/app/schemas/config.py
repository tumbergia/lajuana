from pydantic import BaseModel, Field


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
    reservation_draft_ttl_minutes: int = 30


class ReservationRulesUpdateSchema(BaseModel):
    min_days_in_advance: int | None = Field(default=None, ge=0)
    require_payment_proof_for_confirmation: bool | None = None
    reservation_draft_ttl_minutes: int | None = None


class PaymentInstructionsSchema(BaseModel):
    account_bank: str
    account_type: str
    account_number: str
    account_holder_name: str
    account_holder_id: str
    transfer_note: str
