from datetime import date
from decimal import Decimal

from app.common.collections import Collections
from app.documents.base import AuditDocument


class EquineDocument(AuditDocument):
    name: str
    approximate_birth_date: date | None = None
    approximate_age_years: int | None = None
    weight_kg: Decimal | None = None
    sex: str | None = None
    breed: str | None = None
    gait: str | None = None
    is_available: bool = True
    availability_notes: str | None = None

    class Settings:
        name = Collections.EQUINES
