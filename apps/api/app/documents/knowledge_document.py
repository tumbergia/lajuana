from typing import Literal

from app.common.collections import Collections
from app.documents.base import AuditDocument

KnowledgeScope = Literal["public", "ops"]
KnowledgeStatus = Literal["processing", "ready", "failed"]


class KnowledgeDocument(AuditDocument):
    """Metadatos de un documento de la base de conocimiento del RAG.

    El binario original se guarda en el storage (``storage_key``) y el texto se
    trocea e indexa en :class:`KnowledgeChunkDocument`. ``scope`` controla la
    visibilidad: ``public`` para el chat de clientes y ``ops`` para uso interno.
    """

    title: str
    filename: str
    mime_type: str
    storage_key: str
    scope: KnowledgeScope = "public"
    source: str = "upload"
    size_bytes: int = 0
    sha256: str | None = None
    chunk_count: int = 0
    status: KnowledgeStatus = "processing"
    error: str | None = None
    uploaded_by: str | None = None

    class Settings:
        name = Collections.KNOWLEDGE_DOCUMENTS
        indexes = ["scope", "status"]
