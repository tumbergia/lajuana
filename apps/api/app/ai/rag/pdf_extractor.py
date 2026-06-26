"""Extracción y troceado de texto para indexar en el RAG.

Soporta PDF (vía ``pypdf``), texto plano y markdown. El chunking parte el texto
en ventanas con solapamiento para no perder contexto en los bordes.
"""

from __future__ import annotations

import io

SUPPORTED_MIME_TYPES: set[str] = {
    "application/pdf",
    "text/plain",
    "text/markdown",
}


class UnsupportedDocumentError(ValueError):
    """El tipo de documento no se puede indexar."""


def extract_text(content: bytes, mime_type: str) -> str:
    """Extrae texto plano de los bytes según su MIME type."""
    if mime_type == "application/pdf":
        return _extract_pdf(content)
    if mime_type in ("text/plain", "text/markdown"):
        return content.decode("utf-8", errors="replace").strip()
    raise UnsupportedDocumentError(
        f"Unsupported mime_type for knowledge ingestion: {mime_type}"
    )


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(p.strip() for p in pages if p.strip()).strip()


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    """Trocea el texto en ventanas de ``chunk_size`` con ``overlap`` solapado.

    Normaliza espacios en blanco y respeta los límites de palabra para no cortar
    a mitad de palabra. Devuelve lista vacía si el texto no tiene contenido útil.
    """
    normalized = " ".join(text.split())
    if not normalized:
        return []
    if overlap >= chunk_size:
        overlap = chunk_size // 4

    chunks: list[str] = []
    start = 0
    length = len(normalized)
    while start < length:
        end = min(start + chunk_size, length)
        # Evita cortar a mitad de palabra cuando no es el final del texto.
        if end < length:
            last_space = normalized.rfind(" ", start, end)
            if last_space > start:
                end = last_space
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks
