from __future__ import annotations

from beanie import PydanticObjectId

from app.common.collections import Collections
from app.documents.base import AuditDocument


class ConfigurationAuditDocument(AuditDocument):
    actor_user_id: PydanticObjectId
    section: str
    changed_fields: list[str]
    config_version: int

    class Settings:
        name = Collections.CONFIGURATION_AUDITS
