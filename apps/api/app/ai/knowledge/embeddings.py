"""Embeddings para el KB corporativo (Gemini o hash offline para tests)."""

from __future__ import annotations

import hashlib
import math
import os
from typing import Sequence

from app.core.config import settings
from app.core.logging import logger


def _hash_embed(text: str, dims: int = 64) -> list[float]:
    """Embedding determinista offline (tests / sin API)."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Expandir a dims con hashes sucesivos
    raw = bytearray()
    seed = digest
    while len(raw) < dims * 4:
        seed = hashlib.sha256(seed).digest()
        raw.extend(seed)
    values = []
    for i in range(dims):
        n = int.from_bytes(raw[i * 4 : (i + 1) * 4], "big")
        values.append((n % 10000) / 10000.0)
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def _use_hash_embeddings() -> bool:
    mode = (os.getenv("KNOWLEDGE_EMBEDDING_MODE") or "").strip().lower()
    if mode in {"hash", "offline", "test"}:
        return True
    if mode in {"gemini", "api"}:
        return False
    # Default: hash en tests; Gemini si hay key
    if os.getenv("PYTEST_CURRENT_TEST"):
        return True
    return not bool(settings.gemini_api_key or settings.gemini_api_key_2 or settings.gemini_api_key_3)


def embed_texts(texts: Sequence[str], *, model: str | None = None) -> list[list[float]]:
    """Genera embeddings para una lista de textos."""
    if not texts:
        return []
    if _use_hash_embeddings():
        return [_hash_embed(t) for t in texts]

    from google import genai

    api_key = settings.gemini_api_key or settings.gemini_api_key_2 or settings.gemini_api_key_3
    if not api_key:
        logger.warning("[knowledge] No Gemini key; falling back to hash embeddings")
        return [_hash_embed(t) for t in texts]

    client = genai.Client(api_key=api_key)
    embed_model = model or getattr(settings, "gemini_embedding_model", None) or "gemini-embedding-001"
    if not embed_model.startswith("models/"):
        embed_model = f"models/{embed_model}"
    vectors: list[list[float]] = []
    for text in texts:
        result = client.models.embed_content(model=embed_model, contents=text)
        # google-genai: result.embeddings[0].values or result.embedding.values
        embedding = None
        if getattr(result, "embeddings", None):
            embedding = result.embeddings[0].values
        elif getattr(result, "embedding", None):
            embedding = result.embedding.values
        if embedding is None:
            raise RuntimeError(f"Gemini embed_content returned no vector for model={embed_model}")
        vectors.append([float(x) for x in embedding])
    return vectors


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
