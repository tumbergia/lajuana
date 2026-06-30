from datetime import date

from pydantic import BaseModel, EmailStr

from app.documents.provider_document import ProviderType
from app.documents.reservation_provider_document import ReservationProviderStatus


class ReservationProviderCreateSchema(BaseModel):
    provider_id: str
    service_label: str | None = None
    notes: str | None = None
    status: ReservationProviderStatus = ReservationProviderStatus.PENDING


class ReservationProviderUpdateSchema(BaseModel):
    service_label: str | None = None
    notes: str | None = None
    status: ReservationProviderStatus | None = None


class ReservationProviderTabItemSchema(BaseModel):
    reservation_provider_id: str
    reservation_id: str
    provider_id: str
    provider_name: str
    provider_type: ProviderType
    status: ReservationProviderStatus
    service_label: str | None
    contact_name: str | None
    email: EmailStr | None
    whatsapp_phone: str | None
    location_label: str | None
    capacity_notes: str | None
    operational_notes: str | None
    tariff_notes: str | None
    notes: str | None
    reservation_code: str
    experience_name: str | None
    scheduled_date: date | None
    participants_count: int
