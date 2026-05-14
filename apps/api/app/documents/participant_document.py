from datetime import date, datetime
from decimal import Decimal

from beanie import PydanticObjectId
from pydantic import BaseModel, EmailStr

from app.common.collections import Collections
from app.common.enums import ExperienceLevel
from app.documents.base import AuditDocument


class EmergencyContact(BaseModel):
    name: str
    phone: str
    relationship: str | None = None
    country: str | None = None


class ParticipantDocument(AuditDocument):
    reservation_id: PydanticObjectId
    first_name: str
    last_name: str
    email: EmailStr | None = None
    birth_date: date
    document_type: str
    document_number: str
    phone: str
    country: str
    city: str
    height_cm: Decimal
    weight_kg: Decimal
    experience_level: ExperienceLevel
    riding_experience: str | None = None
    dietary_restrictions: str | None = None
    blood_type: str | None = None
    eps_or_travel_insurance: str | None = None
    health_conditions: str | None = None
    sensory_disabilities: str | None = None
    emergency_contact: EmergencyContact
    accepted_data_processing: bool
    accepted_media_usage: bool | None = None
    accepted_risk_release: bool | None = None
    risk_release_text_version: str | None = None
    submitted_at: datetime | None = None
    source_form_link_id: PydanticObjectId | None = None
    is_completed: bool = False

    class Settings:
        name = Collections.PARTICIPANTS
