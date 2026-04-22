from pydantic import BaseModel, Field

from app.common.enums import ExperienceLevel


class ExperienceCreateSchema(BaseModel):
    name: str
    slug: str
    description: str
    level: ExperienceLevel
    duration_hours: int | None = Field(default=None, gt=0)
    duration_days: int | None = Field(default=None, gt=0)
    base_capacity: int | None = Field(default=None, gt=0)
    is_active: bool = True


class ExperienceUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    level: ExperienceLevel | None = None
    duration_hours: int | None = Field(default=None, gt=0)
    duration_days: int | None = Field(default=None, gt=0)
    base_capacity: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class ExperienceResponseSchema(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    level: ExperienceLevel
    duration_hours: int | None
    duration_days: int | None
    base_capacity: int | None
    is_active: bool
