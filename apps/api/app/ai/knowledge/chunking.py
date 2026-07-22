"""Chunking del MD corporativo por secciones de encabezado."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KB_LANGUAGES: tuple[str, ...] = ("es", "en", "fr", "de", "it", "ru", "zh", "ja")


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    title: str
    text: str
    language: str = "es"


_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
_ASSISTANT_LIMITS_RE = re.compile(
    r"(l[ií]mites?\s+para\s+el\s+asistente|assistant\s+limits|"
    r"limites?\s+pour\s+l|grenzen\s+für\s+den|"
    r"limiti\s+per\s+l|ограничения\s+для|"
    r"助手限制|アシスタントの制限)",
    re.IGNORECASE,
)


def knowledge_dir() -> Path:
    return Path(__file__).resolve().parent


def normalize_kb_language(language: str | None) -> str:
    lang = (language or "es").strip().lower()[:2]
    return lang if lang in KB_LANGUAGES else "es"


def knowledge_md_path(language: str | None = "es") -> Path:
    """Resuelve el MD por idioma; ES es `la_juana_empresa.md`, resto `*.{lang}.md`."""
    lang = normalize_kb_language(language)
    base = knowledge_dir()
    if lang == "es":
        return base / "la_juana_empresa.md"
    specific = base / f"la_juana_empresa.{lang}.md"
    if specific.exists():
        return specific
    return base / "la_juana_empresa.md"


def split_markdown_sections(
    markdown: str,
    *,
    language: str = "es",
) -> list[KnowledgeChunk]:
    """Parte el MD en chunks por headings ## / ### (y # raíz)."""
    matches = list(_HEADING_RE.finditer(markdown))
    if not matches:
        body = markdown.strip()
        return (
            [KnowledgeChunk(chunk_id="chunk-0", title="documento", text=body, language=language)]
            if body
            else []
        )

    chunks: list[KnowledgeChunk] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        block = markdown[start:end].strip()
        title = match.group(2).strip()
        if _ASSISTANT_LIMITS_RE.search(title):
            continue
        if len(block) < 40:
            continue
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{language}-chunk-{i}",
                title=title,
                text=block,
                language=language,
            )
        )
    return chunks


def load_source_chunks(language: str | None = "es") -> list[KnowledgeChunk]:
    lang = normalize_kb_language(language)
    path = knowledge_md_path(lang)
    text = path.read_text(encoding="utf-8")
    return split_markdown_sections(text, language=lang)


def list_available_kb_languages() -> list[str]:
    available: list[str] = []
    for lang in KB_LANGUAGES:
        if knowledge_md_path(lang).exists():
            available.append(lang)
    return available
