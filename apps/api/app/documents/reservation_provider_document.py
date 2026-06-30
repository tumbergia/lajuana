from enum import StrEnum

from beanie import PydanticObjectId
from pymongo import IndexModel

from app.common.collections import Collections
from app.documents.base import AuditDocument


class ReservationProviderStatus(StrEnum):
    PENDING = "pending"
    CONTACTED = "contacted"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ReservationProviderDocument(AuditDocument):
    reservation_id: PydanticObjectId
    provider_id: PydanticObjectId
    service_label: str | None = None
    notes: str | None = None
    status: ReservationProviderStatus = ReservationProviderStatus.PENDING

    class Settings:
        name = Collections.RESERVATION_PROVIDERS
        indexes = [
            IndexModel([("reservation_id", 1)]),
            IndexModel([("provider_id", 1)]),
            IndexModel(
                [("reservation_id", 1), ("provider_id", 1), ("service_label", 1)],
                unique=True,
            ),
        ]
