from enum import StrEnum

from beanie import Indexed
from pydantic import EmailStr

from app.common.collections import Collections
from app.documents.base import AuditDocument


class ProviderStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class ProviderType(StrEnum):
    LODGING = "lodging"
    FOOD = "food"
    TRANSPORT_PEOPLE = "transport_people"
    EQUINE_TRANSPORT = "equine_transport"
    EXPERIENCE_ALLY = "experience_ally"
    GUIDE_ALLY = "guide_ally"
    PARK_OR_ACCESS = "park_or_access"
    INSURANCE = "insurance"
    OTHER = "other"


class ProviderDocument(AuditDocument):
    name: str
    slug: Indexed(str, unique=True)  # type: ignore[valid-type]
    type: ProviderType
    status: ProviderStatus = ProviderStatus.ACTIVE
    service_categories: list[str] = []
    contact_name: str | None = None
    email: EmailStr | None = None
    whatsapp_phone: str | None = None
    location_label: str | None = None
    capacity_notes: str | None = None
    operational_notes: str | None = None
    tariff_notes: str | None = None
    source_notes: str | None = None
    is_active: bool = True

    class Settings:
        name = Collections.PROVIDERS
