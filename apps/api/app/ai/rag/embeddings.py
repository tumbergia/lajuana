"""Generación de embeddings con Gemini.

Reutiliza el SDK ``google-genai`` (ya usado por el planner) y las mismas API
keys configuradas, con rotación simple ante errores de cuota. Las llamadas
bloqueantes del SDK se ejecutan en un hilo para no bloquear el event loop.
"""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging import logger


class EmbeddingError(RuntimeError):
    """Error al generar embeddings con Gemini."""


# task_type optimiza el embedding según su uso (documento indexado vs. consulta).
_DOCUMENT_TASK = "RETRIEVAL_DOCUMENT"
_QUERY_TASK = "RETRIEVAL_QUERY"


class GeminiEmbedder:
    def __init__(self) -> None:
        keys = [
            settings.gemini_api_key,
            settings.gemini_api_key_2,
            settings.gemini_api_key_3,
        ]
        keys = [k for k in keys if k]
        if not keys:
            raise EmbeddingError(
                "No Gemini API keys configured. "
                "Set GEMINI_API_KEY, GEMINI_API_KEY_2, or GEMINI_API_KEY_3."
            )
        self._clients = [genai.Client(api_key=k) for k in keys]
        self._model = settings.rag_embedding_model

    def _embed_sync(self, texts: list[str], task_type: str) -> list[list[float]]:
        last_exc: Exception | None = None
        for index, client in enumerate(self._clients):
            try:
                response = client.models.embed_content(
                    model=self._model,
                    contents=texts,
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                return [list(item.values) for item in response.embeddings]
            except Exception as exc:  # noqa: BLE001 — se reintenta con otra key
                last_exc = exc
                logger.warning(
                    "[rag] Embedding failed on key %d/%d: %s",
                    index + 1,
                    len(self._clients),
                    exc,
                )
        raise EmbeddingError(f"All Gemini keys failed to embed: {last_exc}") from last_exc

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_sync, texts, _DOCUMENT_TASK)

    async def embed_query(self, text: str) -> list[float]:
        result = await asyncio.to_thread(self._embed_sync, [text], _QUERY_TASK)
        return result[0]


_embedder: GeminiEmbedder | None = None


def get_embedder() -> GeminiEmbedder:
    """Devuelve un embedder singleton (lazy)."""
    global _embedder
    if _embedder is None:
        _embedder = GeminiEmbedder()
    return _embedder
