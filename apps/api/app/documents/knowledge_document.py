from typing import Literal

from app.documents.base import AuditDocument


class KnowledgeDocument(AuditDocument):
    text: str  # El contenido legible
    source: str  # Archivo origen (ej. "seguridad.md")
    scope: Literal["public", "ops"]  # 'public' (WhatsApp) o 'ops' (App)
    embedding: list[float]  # El vector numérico
    metadata: dict | None = {}

    class Settings:
        name = "knowledge"
