from pydantic import BaseModel, EmailStr, Field

from app.documents.provider_document import ProviderStatus, ProviderType
from app.schemas.common import AuditMetadataSchema


class ProviderCreateSchema(BaseModel):
    name: str
    slug: str
    type: ProviderType
    status: ProviderStatus = ProviderStatus.ACTIVE
    service_categories: list[str] = Field(default_factory=list)
    contact_name: str | None = None
    email: EmailStr | None = None
    whatsapp_phone: str | None = None
    location_label: str | None = None
    capacity_notes: str | None = None
    operational_notes: str | None = None
    tariff_notes: str | None = None
    source_notes: str | None = None
    is_active: bool = True


class ProviderUpdateSchema(BaseModel):
    name: str | None = None
    slug: str | None = None
    type: ProviderType | None = None
    status: ProviderStatus | None = None
    service_categories: list[str] | None = None
    contact_name: str | None = None
    email: EmailStr | None = None
    whatsapp_phone: str | None = None
    location_label: str | None = None
    capacity_notes: str | None = None
    operational_notes: str | None = None
    tariff_notes: str | None = None
    source_notes: str | None = None
    is_active: bool | None = None


class ProviderListItemSchema(BaseModel):
    id: str
    name: str
    slug: str
    type: ProviderType
    status: ProviderStatus
    service_categories: list[str]
    contact_name: str | None
    email: EmailStr | None
    whatsapp_phone: str | None
    location_label: str | None
    is_active: bool


class ProviderResponseSchema(AuditMetadataSchema):
    id: str
    name: str
    slug: str
    type: ProviderType
    status: ProviderStatus
    service_categories: list[str]
    contact_name: str | None
    email: EmailStr | None
    whatsapp_phone: str | None
    location_label: str | None
    capacity_notes: str | None
    operational_notes: str | None
    tariff_notes: str | None
    source_notes: str | None
    is_active: bool
