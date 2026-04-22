from enum import StrEnum

from pydantic import EmailStr

from app.common.collections import Collections
from app.documents.base import AuditDocument


class ProviderType(StrEnum):
    LODGING = "lodging"
    MULE_TRANSPORT = "mule_transport"
    FOOD = "food"
    OTHER = "other"


class ProviderDocument(AuditDocument):
    name: str
    provider_type: ProviderType
    contact_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    location: str | None = None
    capacity_notes: str | None = None
    rate_notes: str | None = None
    is_active: bool = True

    class Settings:
        name = Collections.PROVIDERS
