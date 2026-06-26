"""Tests unitarios del RAG (Fase A): chunking, similitud coseno y ranking.

Lógica pura sin red ni DB: no invoca Gemini ni MongoDB.
"""

from __future__ import annotations

from types import SimpleNamespace

from app.ai.rag.pdf_extractor import (
    SUPPORTED_MIME_TYPES,
    UnsupportedDocumentError,
    chunk_text,
    extract_text,
)
from app.ai.rag.retriever import cosine_similarity, rank_chunks


# ── Chunking ────────────────────────────────────────────────────────
def test_chunk_text_splits_with_overlap() -> None:
    text = "palabra " * 500  # ~4000 chars
    chunks = chunk_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)
    # No corta a mitad de palabra.
    assert all(not c.endswith("palabr") for c in chunks)


def test_chunk_text_empty_returns_empty() -> None:
    assert chunk_text("   \n  ") == []
    assert chunk_text("") == []


def test_chunk_text_short_single_chunk() -> None:
    chunks = chunk_text("hola mundo", chunk_size=1000, overlap=100)
    assert chunks == ["hola mundo"]


# ── Extracción ──────────────────────────────────────────────────────
def test_extract_text_plain() -> None:
    assert extract_text(b"hola mundo", "text/plain") == "hola mundo"


def test_extract_text_unsupported_raises() -> None:
    try:
        extract_text(b"x", "image/png")
        raise AssertionError("expected UnsupportedDocumentError")
    except UnsupportedDocumentError:
        pass


def test_supported_mime_types() -> None:
    assert "application/pdf" in SUPPORTED_MIME_TYPES
    assert "text/markdown" in SUPPORTED_MIME_TYPES


# ── Similitud coseno ────────────────────────────────────────────────
def test_cosine_similarity_identical() -> None:
    assert abs(cosine_similarity([1.0, 0.0, 1.0], [1.0, 0.0, 1.0]) - 1.0) < 1e-9


def test_cosine_similarity_orthogonal() -> None:
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9


def test_cosine_similarity_handles_empty_or_mismatched() -> None:
    assert cosine_similarity([], [1.0]) == 0.0
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


# ── Ranking ─────────────────────────────────────────────────────────
def _chunk(text: str, embedding: list[float]) -> SimpleNamespace:
    return SimpleNamespace(
        text=text, title="t", source_document_id="doc1", embedding=embedding
    )


def test_rank_chunks_orders_by_similarity_and_applies_threshold() -> None:
    query = [1.0, 0.0]
    chunks = [
        _chunk("perpendicular", [0.0, 1.0]),  # score 0 → filtrado
        _chunk("igual", [1.0, 0.0]),          # score 1 → primero
        _chunk("parecido", [0.9, 0.1]),       # score alto → segundo
    ]
    hits = rank_chunks(query, chunks, top_k=5, min_similarity=0.5)
    assert [h.text for h in hits] == ["igual", "parecido"]
    assert hits[0].score >= hits[1].score


def test_rank_chunks_respects_top_k() -> None:
    query = [1.0, 0.0]
    chunks = [_chunk(f"c{i}", [1.0, 0.0]) for i in range(5)]
    hits = rank_chunks(query, chunks, top_k=2, min_similarity=0.1)
    assert len(hits) == 2
