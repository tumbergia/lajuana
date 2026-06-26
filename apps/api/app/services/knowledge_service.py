"""Servicio de gestión de la base de conocimiento del RAG.

Orquesta el ciclo de vida de un documento: subir → extraer texto → trocear →
embeber → indexar; listar; reindexar; y borrar (chunks + binario). El RAG se
adapta automáticamente: al crear o borrar un documento, sus chunks (y por tanto
los resultados de búsqueda) se actualizan de inmediato.
"""

from __future__ import annotations

from hashlib import sha256

from app.ai.rag.embeddings import EmbeddingError, get_embedder
from app.ai.rag.pdf_extractor import (
    SUPPORTED_MIME_TYPES,
    UnsupportedDocumentError,
    chunk_text,
    extract_text,
)
from app.common.labels import ErrorCode
from app.core.config import settings
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents.knowledge_chunk_document import KnowledgeChunkDocument
from app.documents.knowledge_document import KnowledgeDocument, KnowledgeScope
from app.services.storage import get_storage_adapter

_STORAGE_PREFIX = "knowledge"


class KnowledgeService:
    def __init__(self) -> None:
        self._storage = get_storage_adapter()

    # ── Lectura ────────────────────────────────────────────────────────
    async def list_documents(
        self, *, scope: KnowledgeScope | None = None
    ) -> list[KnowledgeDocument]:
        query = {"scope": scope} if scope else {}
        return await KnowledgeDocument.find(query).sort("-created_at").to_list()

    async def get_document(self, document_id: str) -> KnowledgeDocument:
        doc = await KnowledgeDocument.get(document_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.KNOWLEDGE_NOT_FOUND,
                message="Documento de conocimiento no encontrado.",
            )
        return doc

    # ── Ingesta ────────────────────────────────────────────────────────
    async def ingest_document(
        self,
        *,
        filename: str,
        mime_type: str,
        content: bytes,
        title: str | None = None,
        scope: KnowledgeScope = "public",
        uploaded_by: str | None = None,
    ) -> KnowledgeDocument:
        self._validate_upload(mime_type=mime_type, content=content)

        doc = KnowledgeDocument(
            title=(title or filename).strip(),
            filename=filename,
            mime_type=mime_type,
            storage_key="",
            scope=scope,
            source="upload",
            size_bytes=len(content),
            sha256=sha256(content).hexdigest(),
            status="processing",
            uploaded_by=uploaded_by,
        )
        await doc.insert()

        storage_key = f"{_STORAGE_PREFIX}/{doc.id}/{filename}"
        await self._storage.write_bytes(storage_key, content)
        doc.storage_key = storage_key
        await doc.save()

        try:
            await self._index_document(doc, content)
        except ApiError:
            await self._mark_failed(doc, "embedding_or_extraction_failed")
            raise
        except Exception as exc:  # noqa: BLE001
            await self._mark_failed(doc, str(exc))
            raise ApiError(
                status_code=502,
                code=ErrorCode.KNOWLEDGE_EMBEDDING_FAILED,
                message="No se pudo indexar el documento en el RAG.",
            ) from exc
        return doc

    @staticmethod
    def _compute_metadata_changes(
        *,
        current_title: str,
        current_scope: KnowledgeScope,
        title: str | None,
        scope: KnowledgeScope | None,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Calcula qué cambios aplicar al documento y a sus chunks (lógica pura).

        Devuelve ``(doc_changes, chunk_changes)``. ``scope`` y ``title`` se
        propagan a los chunks (que los denormalizan para filtrar y mostrar).
        Solo incluye un campo si su valor cambia realmente.
        """
        doc_changes: dict[str, str] = {}
        chunk_changes: dict[str, str] = {}
        if title is not None:
            new_title = title.strip()
            if new_title and new_title != current_title:
                doc_changes["title"] = new_title
                chunk_changes["title"] = new_title
        if scope is not None and scope != current_scope:
            doc_changes["scope"] = scope
            chunk_changes["scope"] = scope
        return doc_changes, chunk_changes

    async def update_document(
        self,
        document_id: str,
        *,
        title: str | None = None,
        scope: KnowledgeScope | None = None,
    ) -> KnowledgeDocument:
        """Actualiza la metadata (título/scope). Propaga el cambio a los chunks."""
        doc = await self.get_document(document_id)
        doc_changes, chunk_changes = self._compute_metadata_changes(
            current_title=doc.title,
            current_scope=doc.scope,
            title=title,
            scope=scope,
        )
        if doc_changes:
            for field, value in doc_changes.items():
                setattr(doc, field, value)
            await doc.save()
        if chunk_changes:
            await KnowledgeChunkDocument.find(
                {"source_document_id": document_id}
            ).update({"$set": chunk_changes})
        return doc

    async def reindex_document(self, document_id: str) -> KnowledgeDocument:
        """Reconstruye los chunks de un documento desde el binario en storage."""
        doc = await self.get_document(document_id)
        content = await self._storage.read_bytes(doc.storage_key)
        if content is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.KNOWLEDGE_NOT_FOUND,
                message="El binario del documento no está disponible en el storage.",
            )
        await self._delete_chunks(str(doc.id))
        doc.status = "processing"
        doc.error = None
        await doc.save()
        try:
            await self._index_document(doc, content)
        except Exception as exc:  # noqa: BLE001
            await self._mark_failed(doc, str(exc))
            raise ApiError(
                status_code=502,
                code=ErrorCode.KNOWLEDGE_EMBEDDING_FAILED,
                message="No se pudo reindexar el documento en el RAG.",
            ) from exc
        return doc

    # ── Borrado ────────────────────────────────────────────────────────
    async def delete_document(self, document_id: str) -> None:
        doc = await self.get_document(document_id)
        await self._delete_chunks(document_id)
        if doc.storage_key:
            await self._storage.delete(doc.storage_key)
        await doc.delete()

    # ── Internos ───────────────────────────────────────────────────────
    def _validate_upload(self, *, mime_type: str, content: bytes) -> None:
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ApiError(
                status_code=400,
                code=ErrorCode.KNOWLEDGE_UNSUPPORTED_TYPE,
                message=(
                    "Tipo de archivo no soportado. "
                    "Usa PDF, texto plano o markdown."
                ),
                details={"mime_type": mime_type},
            )
        if not content:
            raise ApiError(
                status_code=400,
                code=ErrorCode.KNOWLEDGE_EMPTY_CONTENT,
                message="El archivo está vacío.",
            )
        if len(content) > settings.rag_max_document_bytes:
            raise ApiError(
                status_code=400,
                code=ErrorCode.KNOWLEDGE_FILE_TOO_LARGE,
                message="El archivo supera el tamaño máximo permitido.",
                details={"max_bytes": settings.rag_max_document_bytes},
            )

    async def _index_document(self, doc: KnowledgeDocument, content: bytes) -> None:
        try:
            text = extract_text(content, doc.mime_type)
        except UnsupportedDocumentError as exc:
            raise ApiError(
                status_code=400,
                code=ErrorCode.KNOWLEDGE_UNSUPPORTED_TYPE,
                message="Tipo de archivo no soportado.",
            ) from exc

        chunks = chunk_text(
            text,
            chunk_size=settings.rag_chunk_size,
            overlap=settings.rag_chunk_overlap,
        )
        if not chunks:
            raise ApiError(
                status_code=400,
                code=ErrorCode.KNOWLEDGE_EMPTY_CONTENT,
                message="No se pudo extraer texto del documento.",
            )

        try:
            embeddings = await get_embedder().embed_documents(chunks)
        except EmbeddingError as exc:
            raise ApiError(
                status_code=502,
                code=ErrorCode.KNOWLEDGE_EMBEDDING_FAILED,
                message="No se pudieron generar los embeddings del documento.",
            ) from exc

        chunk_docs = [
            KnowledgeChunkDocument(
                source_document_id=str(doc.id),
                chunk_index=index,
                text=chunk,
                embedding=embedding,
                scope=doc.scope,
                title=doc.title,
            )
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]
        await KnowledgeChunkDocument.insert_many(chunk_docs)

        doc.chunk_count = len(chunk_docs)
        doc.status = "ready"
        doc.error = None
        await doc.save()
        logger.info(
            "[rag] Indexed document %s | chunks=%d | scope=%s",
            doc.id,
            doc.chunk_count,
            doc.scope,
        )

    async def _delete_chunks(self, document_id: str) -> None:
        await KnowledgeChunkDocument.find(
            {"source_document_id": document_id}
        ).delete()

    async def _mark_failed(self, doc: KnowledgeDocument, error: str) -> None:
        doc.status = "failed"
        doc.error = error[:500]
        await doc.save()
        logger.error("[rag] Document indexing failed | id=%s | error=%s", doc.id, error)
