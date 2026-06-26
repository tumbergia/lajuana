from __future__ import annotations

from typing import Any

from app.ai.mcp.tool_contracts import (
    KnowledgeSnippet,
    SearchKnowledgeOutput,
)
from app.ai.rag.retriever import search_knowledge_chunks
from app.core.config import settings
from app.core.logging import logger


async def search_knowledge(
    query: str = "",
    trace_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Busca información en la base de conocimiento (RAG) para responder preguntas.

    Recupera los fragmentos públicos más relevantes para ``query``. Pensada para
    preguntas abiertas sobre La Juana, el campo, los equinos o las experiencias
    cuyo detalle vive en documentos cargados (PDF, etc.), no en la base de datos
    transaccional. Solo lectura; no expone contenido interno (scope ``ops``).
    """
    if not settings.rag_enabled or not query.strip():
        return SearchKnowledgeOutput(
            trace_id=trace_id or "",
            query=query,
            found=False,
        ).model_dump()

    try:
        hits = await search_knowledge_chunks(query, scopes=["public"])
    except Exception as exc:  # noqa: BLE001 — la conversación no debe romperse
        logger.warning("[rag] search_knowledge failed: %s", exc)
        return SearchKnowledgeOutput(
            trace_id=trace_id or "",
            query=query,
            found=False,
        ).model_dump()

    snippets = [
        KnowledgeSnippet(text=hit.text, title=hit.title, score=round(hit.score, 4))
        for hit in hits
    ]
    return SearchKnowledgeOutput(
        trace_id=trace_id or "",
        query=query,
        found=bool(snippets),
        snippets=snippets,
        total=len(snippets),
    ).model_dump()
