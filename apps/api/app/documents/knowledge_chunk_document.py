from pydantic import Field

from app.common.collections import Collections
from app.documents.base import AuditDocument
from app.documents.knowledge_document import KnowledgeScope


class KnowledgeChunkDocument(AuditDocument):
    """Fragmento indexado de un :class:`KnowledgeDocument`.

    Cada chunk guarda su texto y el vector de embedding. La búsqueda calcula
    similitud coseno en Python sobre los chunks del ``scope`` solicitado, así que
    no se requiere MongoDB Atlas ni ``$vectorSearch``.
    """

    source_document_id: str
    chunk_index: int
    text: str
    embedding: list[float] = Field(default_factory=list)
    scope: KnowledgeScope = "public"
    title: str = ""

    class Settings:
        name = Collections.KNOWLEDGE_CHUNKS
        indexes = ["source_document_id", "scope"]
