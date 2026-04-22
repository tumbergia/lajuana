from beanie import Indexed, PydanticObjectId

from app.common.collections import Collections
from app.common.enums import ExperienceLevel
from app.documents.base import AuditDocument


class ExperienceDocument(AuditDocument):
    name: str
    slug: Indexed(str, unique=True)  # type: ignore[valid-type]
    description: str
    level: ExperienceLevel
    duration_hours: int | None = None
    duration_days: int | None = None
    base_capacity: int | None = None
    is_active: bool = True
    route_ids: list[PydanticObjectId] = []

    class Settings:
        name = Collections.EXPERIENCES
