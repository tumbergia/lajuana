from beanie import Indexed
from pydantic import Field

from app.common.collections import Collections
from app.common.enums import NotificationChannel
from app.documents.base import AuditDocument


class NotificationTemplateDocument(AuditDocument):
    # La unicidad se garantiza por la combinación (template_key, channel, language).
    # Antes el índice era unique sobre template_key solo, lo que impedía tener
    # la misma plantilla en español e inglés. Si vienes de una versión previa,
    # ejecuta el script `drop_notification_template_unique_index.py` para
    # eliminar el índice legacy `template_key_1` antes de iniciar.
    template_key: Indexed(str, name="nt_template_key_idx")
    channel: NotificationChannel
    language: str = "es"
    subject: str | None = None
    body: str
    variables_allowed: list[str] = Field(default_factory=list)
    is_active: bool = True
    created_by: str | None = None
    updated_by: str | None = None

    class Settings:
        name = Collections.NOTIFICATION_TEMPLATES
        indexes = [
            "channel",
            "language",
            # Búsqueda principal: plantilla activa por (key, channel, lang)
            ("template_key", "channel", "language", "is_active"),
        ]
