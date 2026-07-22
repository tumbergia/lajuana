"""Construcción y carga del índice vectorial local del KB (por idioma)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.ai.knowledge.chunking import (
    KB_LANGUAGES,
    knowledge_md_path,
    list_available_kb_languages,
    load_source_chunks,
    normalize_kb_language,
)
from app.ai.knowledge.embeddings import embed_texts
from app.core.logging import logger

INDEX_DIR = Path(__file__).resolve().parent / ".index"


def index_path(language: str | None = "es") -> Path:
    lang = normalize_kb_language(language)
    return INDEX_DIR / f"la_juana_empresa.{lang}.index.json"


def build_index(*, language: str | None = "es", force: bool = False) -> Path:
    """Indexa el MD de un idioma con embeddings y escribe JSON en `.index/`."""
    lang = normalize_kb_language(language)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    source = knowledge_md_path(lang)
    out = index_path(lang)
    if not source.exists():
        logger.warning("[knowledge] Missing MD for lang=%s → %s", lang, source)
        return out

    source_mtime = source.stat().st_mtime
    if out.exists() and not force:
        try:
            existing = json.loads(out.read_text(encoding="utf-8"))
            if (
                existing.get("source_mtime") == source_mtime
                and existing.get("language") == lang
                and existing.get("chunks")
            ):
                logger.info("[knowledge] Index up to date (%s): %s", lang, out)
                return out
        except Exception:
            pass

    chunks = load_source_chunks(lang)
    texts = [c.text for c in chunks]
    vectors = embed_texts(texts) if texts else []
    payload = {
        "source": str(source.name),
        "language": lang,
        "source_mtime": source_mtime,
        "chunks": [
            {
                **asdict(chunk),
                "embedding": vectors[i] if i < len(vectors) else None,
            }
            for i, chunk in enumerate(chunks)
        ],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    logger.info("[knowledge] Built index lang=%s chunks=%d → %s", lang, len(chunks), out)
    return out


def build_all_indexes(*, force: bool = False) -> list[Path]:
    paths: list[Path] = []
    for lang in list_available_kb_languages() or list(KB_LANGUAGES):
        paths.append(build_index(language=lang, force=force))
    return paths


def load_index(language: str | None = "es") -> list[dict]:
    """Carga el índice del idioma; si no existe, lo construye."""
    lang = normalize_kb_language(language)
    out = index_path(lang)
    if not out.exists():
        build_index(language=lang, force=True)
    data = json.loads(out.read_text(encoding="utf-8"))
    return list(data.get("chunks") or [])


def ensure_index(language: str | None = "es") -> list[dict]:
    lang = normalize_kb_language(language)
    try:
        return load_index(lang)
    except Exception as exc:
        logger.warning(
            "[knowledge] Index load/build failed lang=%s (%s); using raw chunks",
            lang,
            exc,
        )
        chunks = load_source_chunks(lang)
        return [
            {
                "chunk_id": c.chunk_id,
                "title": c.title,
                "text": c.text,
                "language": c.language,
                "embedding": None,
            }
            for c in chunks
        ]
