"""Gestión de la base de conocimiento del RAG (admin).

El cliente sube y borra documentos (PDF, texto, markdown) y el RAG se adapta
automáticamente: la ingesta trocea, embebe e indexa; el borrado elimina los
chunks. El endpoint de búsqueda permite verificar la recuperación sin pasar por
WhatsApp.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.ai.rag.retriever import search_knowledge_chunks
from app.api.deps import get_knowledge_service, require_permissions
from app.common.enums import Permission
from app.documents import UserDocument
from app.documents.knowledge_document import KnowledgeDocument
from app.schemas.knowledge import (
    KnowledgeDocumentResponseSchema,
    KnowledgeListResponseSchema,
    KnowledgeSearchRequestSchema,
    KnowledgeSearchResponseSchema,
    KnowledgeSearchResultItem,
    KnowledgeUpdateSchema,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Knowledge / RAG"])


def _to_response(doc: KnowledgeDocument) -> KnowledgeDocumentResponseSchema:
    return KnowledgeDocumentResponseSchema(
        id=str(doc.id),
        title=doc.title,
        filename=doc.filename,
        mime_type=doc.mime_type,
        scope=doc.scope,
        source=doc.source,
        size_bytes=doc.size_bytes,
        chunk_count=doc.chunk_count,
        status=doc.status,
        error=doc.error,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.post(
    "",
    response_model=KnowledgeDocumentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Subir documento a la base de conocimiento",
    description=(
        "Sube un documento (PDF, texto o markdown), lo trocea, genera embeddings "
        "con Gemini y lo indexa en el RAG. El documento queda disponible para "
        "búsqueda inmediatamente."
    ),
    operation_id="createKnowledgeDocument",
)
async def upload_knowledge_document(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.KNOWLEDGE_CREATE))
    ],
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    scope: Literal["public", "ops"] = Form(default="public"),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentResponseSchema:
    content = await file.read()
    doc = await service.ingest_document(
        filename=file.filename or "documento",
        mime_type=file.content_type or "application/octet-stream",
        content=content,
        title=title,
        scope=scope,
        uploaded_by=str(current_user.id),
    )
    return _to_response(doc)


@router.get(
    "",
    response_model=KnowledgeListResponseSchema,
    summary="Listar documentos de la base de conocimiento",
    description="Lista los documentos indexados. Filtra por scope opcionalmente.",
    operation_id="listKnowledgeDocuments",
)
async def list_knowledge_documents(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.KNOWLEDGE_READ))],
    scope: Literal["public", "ops"] | None = None,
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeListResponseSchema:
    docs = await service.list_documents(scope=scope)
    return KnowledgeListResponseSchema(
        total=len(docs),
        documents=[_to_response(d) for d in docs],
    )


@router.get(
    "/{document_id}",
    response_model=KnowledgeDocumentResponseSchema,
    summary="Obtener un documento de la base de conocimiento",
    description="Devuelve los metadatos y estado de indexación de un documento.",
    operation_id="getKnowledgeDocument",
)
async def get_knowledge_document(
    document_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.KNOWLEDGE_READ))],
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentResponseSchema:
    return _to_response(await service.get_document(document_id))


@router.patch(
    "/{document_id}",
    response_model=KnowledgeDocumentResponseSchema,
    summary="Editar metadata de un documento",
    description=(
        "Actualiza el título y/o el scope de un documento. Cambiar el scope "
        "(public ↔ ops) se propaga automáticamente a los chunks indexados, así "
        "que la visibilidad en el chat cambia sin re-subir el archivo."
    ),
    operation_id="updateKnowledgeDocument",
)
async def update_knowledge_document(
    document_id: str,
    payload: KnowledgeUpdateSchema,
    _: Annotated[
        UserDocument, Depends(require_permissions(Permission.KNOWLEDGE_CREATE))
    ],
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentResponseSchema:
    doc = await service.update_document(
        document_id, title=payload.title, scope=payload.scope
    )
    return _to_response(doc)


@router.post(
    "/{document_id}/reindex",
    response_model=KnowledgeDocumentResponseSchema,
    summary="Reindexar un documento",
    description="Reconstruye los chunks y embeddings desde el binario almacenado.",
    operation_id="reindexKnowledgeDocument",
)
async def reindex_knowledge_document(
    document_id: str,
    _: Annotated[
        UserDocument, Depends(require_permissions(Permission.KNOWLEDGE_CREATE))
    ],
    service: KnowledgeService = Depends(get_knowledge_service),
) -> KnowledgeDocumentResponseSchema:
    return _to_response(await service.reindex_document(document_id))


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un documento de la base de conocimiento",
    description="Elimina el documento, sus chunks indexados y el binario del storage.",
    operation_id="deleteKnowledgeDocument",
)
async def delete_knowledge_document(
    document_id: str,
    _: Annotated[
        UserDocument, Depends(require_permissions(Permission.KNOWLEDGE_DELETE))
    ],
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    await service.delete_document(document_id)


@router.post(
    "/search",
    response_model=KnowledgeSearchResponseSchema,
    summary="Buscar en la base de conocimiento (debug)",
    description=(
        "Ejecuta una búsqueda semántica sobre los chunks indexados y devuelve los "
        "fragmentos más relevantes con su score. Útil para validar el RAG."
    ),
    operation_id="searchKnowledge",
)
async def search_knowledge(
    payload: KnowledgeSearchRequestSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.KNOWLEDGE_READ))],
) -> KnowledgeSearchResponseSchema:
    hits = await search_knowledge_chunks(
        payload.query,
        scopes=[payload.scope],
        top_k=payload.top_k,
    )
    return KnowledgeSearchResponseSchema(
        query=payload.query,
        scope=payload.scope,
        total=len(hits),
        results=[
            KnowledgeSearchResultItem(
                text=hit.text,
                title=hit.title,
                source_document_id=hit.source_document_id,
                score=hit.score,
            )
            for hit in hits
        ],
    )
