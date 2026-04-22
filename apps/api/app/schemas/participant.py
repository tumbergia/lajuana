from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import ExperienceLevel


class EmergencyContactSchema(BaseModel):
    name: str
    phone: str
    relationship: str | None = None


class ParticipantCreateSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None
    birth_date: date
    document_type: str
    document_number: str
    phone: str
    country: str
    city: str
    height_cm: Decimal = Field(gt=0)
    weight_kg: Decimal = Field(gt=0)
    experience_level: ExperienceLevel
    blood_type: str | None = None
    eps: str | None = None
    travel_insurance: str | None = None
    medical_conditions: str | None = None
    functional_conditions: str | None = None
    dietary_restrictions: str | None = None
    diet: str | None = None
    emergency_contact: EmergencyContactSchema
    accepted_data_processing: bool
    accepted_media_usage: bool | None = None


class ParticipantUpdateSchema(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    birth_date: date | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    height_cm: Decimal | None = Field(default=None, gt=0)
    weight_kg: Decimal | None = Field(default=None, gt=0)
    experience_level: ExperienceLevel | None = None
    medical_conditions: str | None = None
    functional_conditions: str | None = None
    dietary_restrictions: str | None = None
    diet: str | None = None
    emergency_contact: EmergencyContactSchema | None = None
    accepted_data_processing: bool | None = None
    accepted_media_usage: bool | None = None


class ParticipantResponseSchema(BaseModel):
    id: str
    reservation_id: str
    first_name: str
    last_name: str
    birth_date: date
    document_type: str
    document_number: str
    phone: str
    country: str
    city: str
    height_cm: Decimal
    weight_kg: Decimal
    experience_level: ExperienceLevel
    emergency_contact: EmergencyContactSchema
    accepted_data_processing: bool
    accepted_media_usage: bool | None
    is_completed: bool
    created_at: datetime
