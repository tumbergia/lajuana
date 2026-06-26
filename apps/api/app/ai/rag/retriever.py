"""Recuperación por similitud coseno sobre los chunks del RAG.

Carga los chunks del ``scope`` solicitado desde MongoDB y rankea por similitud
coseno contra el embedding de la consulta. Apto para corpus pequeños/medianos
(decenas a pocos miles de chunks); para escalar a gran volumen, migrar a
MongoDB Atlas ``$vectorSearch`` manteniendo esta misma interfaz.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.ai.rag.embeddings import get_embedder
from app.core.config import settings
from app.documents.knowledge_chunk_document import KnowledgeChunkDocument
from app.documents.knowledge_document import KnowledgeScope


@dataclass(frozen=True)
class KnowledgeSearchHit:
    text: str
    title: str
    source_document_id: str
    score: float


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Similitud coseno entre dos vectores. Devuelve 0.0 si alguno es nulo."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b, strict=False):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def rank_chunks(
    query_embedding: list[float],
    chunks: list[KnowledgeChunkDocument],
    *,
    top_k: int,
    min_similarity: float,
) -> list[KnowledgeSearchHit]:
    """Rankea chunks por similitud coseno (lógica pura, sin I/O)."""
    scored: list[KnowledgeSearchHit] = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk.embedding)
        if score >= min_similarity:
            scored.append(
                KnowledgeSearchHit(
                    text=chunk.text,
                    title=chunk.title,
                    source_document_id=chunk.source_document_id,
                    score=score,
                )
            )
    scored.sort(key=lambda hit: hit.score, reverse=True)
    return scored[:top_k]


async def search_knowledge_chunks(
    query: str,
    *,
    scopes: list[KnowledgeScope] | None = None,
    top_k: int | None = None,
    min_similarity: float | None = None,
) -> list[KnowledgeSearchHit]:
    """Busca los chunks más relevantes para ``query`` en los ``scopes`` dados."""
    allowed_scopes = scopes or ["public"]
    limit = top_k or settings.rag_search_top_k
    threshold = settings.rag_min_similarity if min_similarity is None else min_similarity

    chunks = await KnowledgeChunkDocument.find(
        {"scope": {"$in": list(allowed_scopes)}}
    ).to_list()
    if not chunks:
        return []

    query_embedding = await get_embedder().embed_query(query)
    return rank_chunks(
        query_embedding,
        chunks,
        top_k=limit,
        min_similarity=threshold,
    )
