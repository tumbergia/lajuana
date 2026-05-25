from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import ExperienceLevel
from app.schemas.common import AuditMetadataSchema


class EmergencyContactSchema(BaseModel):
    name: str
    phone: str
    relationship: str | None = None
    country: str | None = None


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
    dietary_restrictions: str | None = None
    blood_type: str | None = None
    eps_or_travel_insurance: str | None = None
    health_conditions: str | None = None
    sensory_disabilities: str | None = None
    emergency_contact: EmergencyContactSchema
    accepted_data_processing: bool
    accepted_media_usage: bool | None = None
    accepted_risk_release: bool | None = None
    risk_release_text_version: str | None = None


class ParticipantNestedCreateSchema(BaseModel):
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
    experience_level: ExperienceLevel | None = None
    dietary_restrictions: str | None = None
    blood_type: str | None = None
    eps_or_travel_insurance: str | None = None
    health_conditions: str | None = None
    sensory_disabilities: str | None = None
    emergency_contact: EmergencyContactSchema
    accepted_data_processing: bool
    accepted_media_usage: bool | None = None
    accepted_risk_release: bool
    risk_release_text_version: str | None = None


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
    dietary_restrictions: str | None = None
    blood_type: str | None = None
    eps_or_travel_insurance: str | None = None
    health_conditions: str | None = None
    sensory_disabilities: str | None = None
    emergency_contact: EmergencyContactSchema | None = None
    accepted_data_processing: bool | None = None
    accepted_media_usage: bool | None = None
    accepted_risk_release: bool | None = None
    risk_release_text_version: str | None = None


class ParticipantResponseSchema(AuditMetadataSchema):
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
    dietary_restrictions: str | None
    blood_type: str | None
    eps_or_travel_insurance: str | None
    health_conditions: str | None
    sensory_disabilities: str | None
    emergency_contact: EmergencyContactSchema
    accepted_data_processing: bool
    accepted_media_usage: bool | None
    accepted_risk_release: bool | None
    risk_release_text_version: str | None
    is_completed: bool


class ParticipantPublicCreateSchema(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr | None = None
    birth_date: date
    document_type: str = Field(min_length=1)
    document_number: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    country: str = Field(min_length=1)
    city: str = Field(min_length=1)
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
    emergency_contact_name: str = Field(min_length=1)
    emergency_contact_phone: str = Field(min_length=1)
    emergency_contact_relationship: str | None = None
    emergency_contact_country: str | None = None
    accepted_data_processing: bool
    accepted_media_usage: bool | None = None
    accepted_risk_release: bool
    risk_release_text_version: str | None = None


class ParticipantFormInfoSchema(BaseModel):
    reservation_public_code: str
    experience_name: str
    scheduled_date: date | None = None
    start_time: str | None = None
    participant_limit: int
    participants_registered: int
    participants_remaining: int
    form_status: str


class ParticipantFormCreateRequest(BaseModel):
    force_regenerate: bool = False
    expires_in_days: int | None = None


class ParticipantFormCreateResponse(BaseModel):
    reservation_id: str
    public_reservation_code: str
    form_url: str
    expires_at: datetime | None = None
    participant_limit: int | None = None
    participants_registered: int = 0
    participants_remaining: int = 0
    form_status: str
