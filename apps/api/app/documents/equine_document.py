from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from beanie import Indexed
from bson import Decimal128
from pydantic import BeforeValidator, Field


def _decimal_from_mongo(v: object) -> Decimal | None:
    """Convert MongoDB Decimal128 to Python Decimal."""
    if v is None:
        return None
    if isinstance(v, Decimal128):
        return v.to_decimal()
    if isinstance(v, Decimal):
        return v
    if isinstance(v, (int, float, str)):
        return Decimal(v)
    return v


DecimalField = Annotated[Decimal | None, BeforeValidator(_decimal_from_mongo)]

from app.common.collections import Collections
from app.common.enums import (
    EquineExperienceFit,
    EquineLocationStatus,
    EquineOperationalStatus,
    EquineSex,
    EquineSpecies,
)
from app.documents.base import AuditDocument


class EquineDocument(AuditDocument):
    name: Indexed(str)
    inventory_number: int | None = None

    species: EquineSpecies = EquineSpecies.MULE
    location_status: EquineLocationStatus = EquineLocationStatus.LA_JUANA
    location_notes: str | None = None

    breed: str | None = None
    sex: EquineSex = EquineSex.UNKNOWN
    coat_color: str | None = None
    gait: str | None = None

    approximate_birth_date: date | None = None
    approximate_age_years: int | None = Field(default=None, ge=0)
    birth_date_is_approximate: bool = True
    birth_date_raw: str | None = None
    birth_place: str | None = None

    registry_number: str | None = None
    microchip: str | None = None

    sire_name: str | None = None
    dam_name: str | None = None

    weight_kg: DecimalField = Field(default=None, gt=0)
    height_m: DecimalField = Field(default=None, gt=0)
    last_weight_at: date | None = None
    last_height_at: date | None = None

    is_active: bool = True
    is_available: bool = True
    operational_status: EquineOperationalStatus = EquineOperationalStatus.AVAILABLE
    availability_notes: str | None = None
    availability_reasons: str | None = None
    rest_until: datetime | None = None

    max_rider_weight_kg: DecimalField = Field(default=None, gt=0)
    experience_fit: EquineExperienceFit | None = EquineExperienceFit.ALL
    image_base64: str | None = None

    last_service_at: datetime | None = None
    workload_last_7_days: int = Field(default=0, ge=0)

    source_file: str | None = None
    source_sheet: str | None = None
    source_row_number: int | None = Field(default=None, ge=1)
    source_updated_at_label: str | None = None

    class Settings:
        name = Collections.EQUINES
        indexes = [
            "name",
            "inventory_number",
            "species",
            "operational_status",
            "is_active",
            "is_available",
            "microchip",
            "registry_number",
        ]
