from pydantic import BaseModel, Field


class ReservationRulesSchema(BaseModel):
    min_days_in_advance: int = Field(ge=0)
    require_payment_proof_for_confirmation: bool = True


class ReservationRulesUpdateSchema(BaseModel):
    min_days_in_advance: int | None = Field(default=None, ge=0)
    require_payment_proof_for_confirmation: bool | None = None
