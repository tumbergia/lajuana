from pydantic import BaseModel, Field

from app.common.enums import (
    ExperienceCategory,
    ExperienceDifficulty,
    ExperienceLevel,
    ExperienceStatus,
)
from app.schemas.common import AuditMetadataSchema


class ExperienceDurationSchema(BaseModel):
    activity_minutes: int = Field(gt=0)
    route_minutes: int = Field(gt=0)
    display_text: str | None = None


class ExperienceRouteDetailsSchema(BaseModel):
    distance_km: float | None = Field(default=None, gt=0)
    terrain: str = Field(min_length=3, max_length=300)
    terrain_notes: str | None = Field(default=None, max_length=500)


class ExperiencePricingTierSchema(BaseModel):
    min_participants: int = Field(ge=1)
    max_participants: int = Field(ge=1)
    price_per_person: int = Field(gt=0)


class ExperiencePricingSchema(BaseModel):
    currency: str = Field(default="COP", min_length=3, max_length=3)
    prices_are_net: bool = True
    pricing_notes: str | None = Field(default=None, max_length=300)
    tiers: list[ExperiencePricingTierSchema] = Field(default_factory=list)
    require_contiguous_tiers: bool = False


class ExperienceInclusionsSchema(BaseModel):
    items: list[str] = Field(default_factory=list)
    display_text: str | None = None


class ExperienceCreateSchema(BaseModel):
    name: str
    slug: str
    subtitle: str | None = None
    description: str
    image_url: str | None = None

    level: ExperienceLevel
    difficulty: ExperienceDifficulty = ExperienceDifficulty.BASIC
    category: ExperienceCategory = ExperienceCategory.EXPERIENCE
    status: ExperienceStatus = ExperienceStatus.PUBLISHED

    # Compatibilidad con contrato previo.
    duration_hours: int | None = Field(default=None, gt=0)
    duration_days: int | None = Field(default=None, gt=0)
    base_capacity: int | None = Field(default=None, gt=0)

    duration: ExperienceDurationSchema | None = None
    route_details: ExperienceRouteDetailsSchema | None = None
    pricing: ExperiencePricingSchema | None = None
    inclusions: ExperienceInclusionsSchema | None = None
    standard_max_participants: int | None = Field(default=None, ge=1)
    min_participants: int | None = Field(default=None, ge=1)
    tags: list[str] = Field(default_factory=list)

    is_active: bool = True


class ExperienceUpdateSchema(BaseModel):
    name: str | None = None
    subtitle: str | None = None
    description: str | None = None
    image_url: str | None = None
    level: ExperienceLevel | None = None
    difficulty: ExperienceDifficulty | None = None
    category: ExperienceCategory | None = None
    status: ExperienceStatus | None = None

    duration_hours: int | None = Field(default=None, gt=0)
    duration_days: int | None = Field(default=None, gt=0)
    base_capacity: int | None = Field(default=None, gt=0)

    duration: ExperienceDurationSchema | None = None
    route_details: ExperienceRouteDetailsSchema | None = None
    pricing: ExperiencePricingSchema | None = None
    inclusions: ExperienceInclusionsSchema | None = None
    standard_max_participants: int | None = Field(default=None, ge=1)
    min_participants: int | None = Field(default=None, ge=1)
    tags: list[str] | None = None

    is_active: bool | None = None


class ExperienceResponseSchema(AuditMetadataSchema):
    id: str
    name: str
    slug: str
    subtitle: str | None
    description: str
    image_url: str | None

    level: ExperienceLevel
    difficulty: ExperienceDifficulty
    category: ExperienceCategory
    status: ExperienceStatus

    duration_hours: int | None
    duration_days: int | None
    base_capacity: int | None

    duration: ExperienceDurationSchema | None
    route_details: ExperienceRouteDetailsSchema | None
    pricing: ExperiencePricingSchema | None
    inclusions: ExperienceInclusionsSchema | None
    standard_max_participants: int | None
    min_participants: int | None
    tags: list[str]

    is_active: bool


class ExperienceQuoteRequestSchema(BaseModel):
    participants_count: int = Field(ge=1)
    schedule_id: str | None = None
    special_conditions: list[str] = Field(default_factory=list)


class ExperienceQuoteResponseSchema(BaseModel):
    experience_id: str
    participants_count: int
    unit_price: int
    subtotal: int
    currency: str
    pricing_tier: ExperiencePricingTierSchema
    notes: str | None = None
