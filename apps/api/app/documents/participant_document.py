from datetime import date
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
    blood_type: str | None = None
    eps: str | None = None
    travel_insurance: str | None = None
    medical_conditions: str | None = None
    functional_conditions: str | None = None
    dietary_restrictions: str | None = None
    diet: str | None = None
    emergency_contact: EmergencyContact
    accepted_data_processing: bool
    accepted_media_usage: bool | None = None
    is_completed: bool = False

    class Settings:
        name = Collections.PARTICIPANTS
