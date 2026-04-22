from beanie import Indexed

from app.common.collections import Collections
from app.documents.base import AuditDocument


class SaddleDocument(AuditDocument):
    code: Indexed(str, unique=True)  # type: ignore[valid-type]
    name: str | None = None
    is_available: bool = True
    notes: str | None = None

    class Settings:
        name = Collections.SADDLES
