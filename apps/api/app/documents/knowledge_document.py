from typing import Any, Literal

from pydantic import Field

from app.common.collections import Collections
from app.documents.base import AuditDocument


class KnowledgeDocument(AuditDocument):
    type: str = "knowledge"
    title: str = ""
    content: str = ""
    text: str = ""
    source: str = ""
    scope: Literal["public", "ops"] = "public"
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = Collections.KNOWLAGE
