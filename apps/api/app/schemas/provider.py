from pydantic import BaseModel, EmailStr

from app.documents import ProviderType


class ProviderCreateSchema(BaseModel):
    name: str
    provider_type: ProviderType
    contact_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    location: str | None = None
    capacity_notes: str | None = None
    rate_notes: str | None = None
    is_active: bool = True


class ProviderUpdateSchema(BaseModel):
    name: str | None = None
    provider_type: ProviderType | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    location: str | None = None
    capacity_notes: str | None = None
    rate_notes: str | None = None
    is_active: bool | None = None


class ProviderResponseSchema(BaseModel):
    id: str
    name: str
    provider_type: ProviderType
    contact_name: str | None
    phone: str | None
    email: EmailStr | None
    location: str | None
    capacity_notes: str | None
    rate_notes: str | None
    is_active: bool
