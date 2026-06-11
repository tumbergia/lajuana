from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.common.enums import (
    EquineExperienceFit,
    EquineLocationStatus,
    EquineOperationalStatus,
    EquineSex,
    EquineSpecies,
)
from app.schemas.common import AuditMetadataSchema


class EquineCreateSchema(BaseModel):
    # Identificación base / CV
    name: str = Field(min_length=1, max_length=120)
    inventory_number: int | None = Field(default=None, ge=1)

    # Equivalente a CLASE: MUL. / ASN. / CAB.
    species: EquineSpecies = EquineSpecies.MULE

    # Equivalente a UBICACIÓN: LA JUANA / OTROS
    location_status: EquineLocationStatus = EquineLocationStatus.LA_JUANA
    location_notes: str | None = None

    # Datos zootécnicos / ficha
    breed: str | None = None                 # RAZA real: Criolla, Lusitana, Criolla x Lusitana
    sex: EquineSex = EquineSex.UNKNOWN
    coat_color: str | None = None            # COLOR
    gait: str | None = None                  # PASO: Fino, Trocha, etc.

    # Nacimiento
    approximate_birth_date: date | None = None
    approximate_age_years: int | None = Field(default=None, ge=0)
    birth_date_is_approximate: bool = True
    birth_date_raw: str | None = None        # Texto original del Excel: "Oct. 15 de 2008"
    birth_place: str | None = None

    # Identificación externa
    registry_number: str | None = None       # # REGISTRO
    microchip: str | None = None             # MICROCHIP

    # Genealogía
    sire_name: str | None = None             # PADRE
    dam_name: str | None = None              # MADRE

    # Medidas actuales resumidas
    weight_kg: Decimal | None = Field(default=None, gt=0)
    height_m: Decimal | None = Field(default=None, gt=0)
    last_weight_at: date | None = None
    last_height_at: date | None = None

    # Operación
    is_active: bool = True
    is_available: bool = True
    operational_status: EquineOperationalStatus = EquineOperationalStatus.AVAILABLE
    availability_notes: str | None = None
    availability_reasons: str | None = None
    rest_until: datetime | None = None

    # Asignación
    max_rider_weight_kg: Decimal | None = Field(default=None, gt=0)
    experience_fit: EquineExperienceFit | None = EquineExperienceFit.ALL
    image_base64: str | None = None

    # Resumen calculado / mantenido por servicios
    last_service_at: datetime | None = None
    workload_last_7_days: int = Field(default=0, ge=0)

    # Trazabilidad de importación
    source_file: str | None = None
    source_sheet: str | None = None
    source_row_number: int | None = Field(default=None, ge=1)
    source_updated_at_label: str | None = None


class EquineUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    inventory_number: int | None = Field(default=None, ge=1)

    species: EquineSpecies | None = None
    location_status: EquineLocationStatus | None = None
    location_notes: str | None = None

    breed: str | None = None
    sex: EquineSex | None = None
    coat_color: str | None = None
    gait: str | None = None

    approximate_birth_date: date | None = None
    approximate_age_years: int | None = Field(default=None, ge=0)
    birth_date_is_approximate: bool | None = None
    birth_date_raw: str | None = None
    birth_place: str | None = None

    registry_number: str | None = None
    microchip: str | None = None

    sire_name: str | None = None
    dam_name: str | None = None

    weight_kg: Decimal | None = Field(default=None, gt=0)
    height_m: Decimal | None = Field(default=None, gt=0)
    last_weight_at: date | None = None
    last_height_at: date | None = None

    is_active: bool | None = None
    is_available: bool | None = None
    operational_status: EquineOperationalStatus | None = None
    availability_notes: str | None = None
    availability_reasons: str | None = None
    rest_until: datetime | None = None

    max_rider_weight_kg: Decimal | None = Field(default=None, gt=0)
    experience_fit: EquineExperienceFit | None = None
    image_base64: str | None = None

    last_service_at: datetime | None = None
    workload_last_7_days: int | None = Field(default=None, ge=0)

    source_file: str | None = None
    source_sheet: str | None = None
    source_row_number: int | None = Field(default=None, ge=1)
    source_updated_at_label: str | None = None


class EquineResponseSchema(AuditMetadataSchema):
    id: str

    name: str
    inventory_number: int | None

    species: EquineSpecies
    location_status: EquineLocationStatus
    location_notes: str | None

    breed: str | None
    sex: EquineSex
    coat_color: str | None
    gait: str | None

    approximate_birth_date: date | None
    approximate_age_years: int | None
    birth_date_is_approximate: bool
    birth_date_raw: str | None
    birth_place: str | None

    registry_number: str | None
    microchip: str | None

    sire_name: str | None
    dam_name: str | None

    weight_kg: Decimal | None
    height_m: Decimal | None
    last_weight_at: date | None
    last_height_at: date | None

    is_active: bool
    is_available: bool
    operational_status: EquineOperationalStatus
    availability_notes: str | None
    availability_reasons: str | None
    rest_until: datetime | None

    max_rider_weight_kg: Decimal | None
    experience_fit: EquineExperienceFit | None
    image_base64: str | None = None

    last_service_at: datetime | None = None
    workload_last_7_days: int

    source_file: str | None
    source_sheet: str | None
    source_row_number: int | None
    source_updated_at_label: str | None


class EquineListItemSchema(AuditMetadataSchema):
    """Versión compacta para listados — omite genealogía, fechas de importación, trazabilidad.

    Incluye todos los campos necesarios para las cards de listado y el perfil
    del equino seleccionado, eliminando la necesidad de un request extra por detalle.
    """

    id: str
    name: str
    inventory_number: int | None
    species: EquineSpecies
    location_status: EquineLocationStatus = EquineLocationStatus.LA_JUANA
    location_notes: str | None = None
    breed: str | None
    sex: EquineSex
    coat_color: str | None
    gait: str | None
    weight_kg: Decimal | None
    height_m: Decimal | None
    is_active: bool
    is_available: bool
    operational_status: EquineOperationalStatus
    approximate_age_years: int | None = None
    max_rider_weight_kg: Decimal | None
    experience_fit: EquineExperienceFit | None
    image_base64: str | None = None
    last_service_at: datetime | None = None
    workload_last_7_days: int
    rest_until: datetime | None = None
    availability_reasons: str | None = None
    block_reason: str | None = None
    """Non-null when this equine is excluded from being assignable to a reservation."""


class EquineTimelineEntrySchema(BaseModel):
    """Entrada unificada del timeline: bitácora de servicio o evento de cuidado."""

    id: str
    source: Literal["service_log", "equine_event"]
    event_type: str
    happened_at: datetime
    title: str
    reservation_id: str | None = None
    assignment_id: str | None = None
    participant_id: str | None = None
    notes: str | None = None
    severity: str | None = None
    affects_availability: bool = False
