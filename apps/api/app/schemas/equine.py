from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import AuditMetadataSchema


class EquineCreateSchema(BaseModel):
    name: str
    approximate_birth_date: date | None = None
    approximate_age_years: int | None = Field(default=None, ge=0)
    weight_kg: Decimal | None = Field(default=None, gt=0)
    sex: str | None = None
    breed: str | None = None
    gait: str | None = None
    is_available: bool = True
    availability_notes: str | None = None


class EquineUpdateSchema(BaseModel):
    name: str | None = None
    approximate_birth_date: date | None = None
    approximate_age_years: int | None = Field(default=None, ge=0)
    weight_kg: Decimal | None = Field(default=None, gt=0)
    sex: str | None = None
    breed: str | None = None
    gait: str | None = None
    is_available: bool | None = None
    availability_notes: str | None = None


class EquineResponseSchema(AuditMetadataSchema):
    id: str
    name: str
    approximate_birth_date: date | None
    approximate_age_years: int | None
    weight_kg: Decimal | None
    sex: str | None
    breed: str | None
    gait: str | None
    is_available: bool
    availability_notes: str | None
