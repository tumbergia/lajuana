from beanie import Indexed, PydanticObjectId
from pydantic import BaseModel, Field

from app.common.collections import Collections
from app.common.enums import (
    ExperienceCategory,
    ExperienceDifficulty,
    ExperienceLevel,
    ExperienceStatus,
)
from app.documents.base import AuditDocument


class ExperienceDurationData(BaseModel):
    activity_minutes: int
    route_minutes: int
    display_text: str | None = None


class ExperienceRouteDetailsData(BaseModel):
    distance_km: float | None = None
    terrain: str
    terrain_notes: str | None = None


class ExperiencePricingTierData(BaseModel):
    min_participants: int
    max_participants: int
    price_per_person: int


class ExperiencePricingData(BaseModel):
    currency: str = "COP"
    prices_are_net: bool = True
    pricing_notes: str | None = None
    tiers: list[ExperiencePricingTierData] = Field(default_factory=list)


class ExperienceInclusionsData(BaseModel):
    items: list[str] = Field(default_factory=list)
    display_text: str | None = None


class ExperienceDocument(AuditDocument):
    name: str
    slug: Indexed(str, unique=True)  # type: ignore[valid-type]
    subtitle: str | None = None
    description: str
    image_url: str | None = None

    level: ExperienceLevel
    difficulty: ExperienceDifficulty = ExperienceDifficulty.BASIC
    category: ExperienceCategory = ExperienceCategory.EXPERIENCE
    status: ExperienceStatus = ExperienceStatus.PUBLISHED

    duration_hours: int | None = None
    duration_days: int | None = None
    base_capacity: int | None = None

    duration: ExperienceDurationData | None = None
    route_details: ExperienceRouteDetailsData | None = None
    pricing: ExperiencePricingData | None = None
    inclusions: ExperienceInclusionsData | None = None
    standard_max_participants: int | None = None
    min_participants: int | None = None
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)

    is_active: bool = True
    route_ids: list[PydanticObjectId] = Field(default_factory=list)

    class Settings:
        name = Collections.EXPERIENCES
