"""RAG (Retrieval-Augmented Generation) para la base de conocimiento.

Embeddings con Gemini + similitud coseno en Python sobre MongoDB. No requiere
MongoDB Atlas ni ``$vectorSearch``: es portable a cualquier despliegue de Mongo.
"""

from app.ai.rag.embeddings import GeminiEmbedder, get_embedder
from app.ai.rag.pdf_extractor import (
    SUPPORTED_MIME_TYPES,
    UnsupportedDocumentError,
    chunk_text,
    extract_text,
)
from app.ai.rag.retriever import KnowledgeSearchHit, search_knowledge_chunks

__all__ = [
    "GeminiEmbedder",
    "get_embedder",
    "SUPPORTED_MIME_TYPES",
    "UnsupportedDocumentError",
    "chunk_text",
    "extract_text",
    "KnowledgeSearchHit",
    "search_knowledge_chunks",
]
