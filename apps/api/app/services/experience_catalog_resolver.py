from __future__ import annotations

import re
import time
from difflib import SequenceMatcher
from enum import StrEnum

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.documents.experience_document import ExperienceDocument

_ACCENT_MAP = {
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "ü": "u",
    "ñ": "n",
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "Ü": "U",
    "Ñ": "N",
}
_ACCENT_TABLE = str.maketrans(_ACCENT_MAP)

MIN_TOKEN_LENGTH = 3
MAX_RESULTS = 100
CACHE_TTL_SECONDS = 300  # 5 minutos
FUZZY_TOKEN_RATIO = 0.78

_STOPWORDS = {
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "unos",
    "unas",
    "de",
    "del",
    "en",
    "para",
    "por",
    "a",
    "y",
    "e",
    "o",
    "que",
    "con",
    "su",
    "al",
    "lo",
    "mi",
    "me",
    "te",
    "se",
    "no",
    "si",
    "ya",
    "dime",
    "dima",
    "dame",
    "acerca",
    "sobre",
    "tambien",
    "también",
    "mas",
    "más",
    "quiero",
    "saber",
    "info",
    "informacion",
    "información",
    "detalle",
    "detalles",
    "cuentame",
    "cuéntame",
    "hablame",
    "háblame",
    "explicame",
    "explícame",
    "the",
    "a",
    "an",
    "of",
    "and",
    "or",
    "about",
    "tell",
    "me",
    "please",
}


def _strip_accents(text: str) -> str:
    return text.translate(_ACCENT_TABLE)


def _normalize(text: str) -> str:
    return _strip_accents((text or "").lower()).strip()


def _significant_tokens(text: str) -> set[str]:
    norm = _normalize(text)
    return {
        t
        for t in re.split(r"[^a-z0-9]+", norm)
        if len(t) >= MIN_TOKEN_LENGTH and t not in _STOPWORDS
    }


def _tokens_similar(a: str, b: str, threshold: float = FUZZY_TOKEN_RATIO) -> bool:
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    if abs(len(a) - len(b)) > max(2, len(a) // 3):
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold


def _token_matches_haystack(token: str, haystack: str, haystack_tokens: set[str]) -> bool:
    if token in haystack:
        return True
    return any(_tokens_similar(token, ht) for ht in haystack_tokens)


def _doc_identity_tokens(doc: ExperienceDocument) -> set[str]:
    parts = [getattr(doc, "name", "") or "", getattr(doc, "slug", "") or ""]
    parts.extend(getattr(doc, "aliases", None) or [])
    tokens: set[str] = set()
    for part in parts:
        tokens |= _significant_tokens(part)
    return tokens


def _score_doc_against_query(doc: ExperienceDocument, query: str) -> float:
    """Score how well a catalog doc is mentioned in the user query (0 = no match)."""
    query_norm = _normalize(query)
    if not query_norm:
        return 0.0

    name_norm = _normalize(getattr(doc, "name", "") or "")
    slug_norm = _normalize(getattr(doc, "slug", "") or "")
    if name_norm and name_norm in query_norm:
        return 10.0
    if slug_norm and slug_norm.replace("-", " ") in query_norm:
        return 9.5

    aliases = getattr(doc, "aliases", None) or []
    for alias in aliases:
        alias_norm = _normalize(alias)
        if len(alias_norm) >= MIN_TOKEN_LENGTH and alias_norm in query_norm:
            return 9.0

    query_tokens = _significant_tokens(query)
    if not query_tokens:
        return 0.0

    identity_tokens = _doc_identity_tokens(doc)
    if not identity_tokens:
        return 0.0

    matched = 0
    for it in identity_tokens:
        if any(_tokens_similar(it, qt) for qt in query_tokens):
            matched += 1

    if matched == 0:
        return 0.0

    ratio = matched / len(identity_tokens)
    # Short names (1–2 distinctive tokens): one solid hit is enough.
    # Longer names: need at least half the identity tokens.
    if matched >= 1 and (len(identity_tokens) <= 2 or ratio >= 0.5):
        return float(matched) + ratio
    return 0.0


class ExperienceResolutionStatus(StrEnum):
    FOUND = "found"
    AMBIGUOUS = "ambiguous"
    NOT_FOUND = "not_found"


class ExperienceResolutionResult(BaseModel):
    status: ExperienceResolutionStatus
    experience_id: str | None = None
    experience_name: str | None = None
    slug: str | None = None
    confidence: float = 0.0
    candidates: list[dict] = Field(default_factory=list)


class ExperienceCatalogResolver:
    # Cache class-level: {cache_key: (docs, timestamp)}
    _cache: dict[str, tuple[list[ExperienceDocument], float]] = {}

    async def _load_active(self) -> list[ExperienceDocument]:
        """Carga experiencias activas con caché in-memory TTL."""
        now = time.monotonic()
        cache_key = "active_experiences"

        cached = self._cache.get(cache_key)
        if cached is not None and (now - cached[1]) < CACHE_TTL_SECONDS:
            return cached[0]

        docs = await ExperienceDocument.find({"is_active": True}).to_list()
        self._cache[cache_key] = (docs, now)
        return docs

    async def resolve(
        self,
        query: str,
        experiences: list[ExperienceDocument] | None = None,
    ) -> ExperienceResolutionResult:
        if not query or not query.strip():
            return ExperienceResolutionResult(
                status=ExperienceResolutionStatus.NOT_FOUND,
            )

        text = query.strip()

        # 1. Exact match by ObjectId
        try:
            oid = PydanticObjectId(text)
            doc = await ExperienceDocument.get(oid)
            if doc:
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )
        except Exception:
            pass

        docs = experiences if experiences is not None else await self._load_active()

        # 2. Exact match by slug (normalized)
        norm_text = _normalize(text)
        for doc in docs:
            if doc.slug and _normalize(doc.slug) == norm_text:
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 3. Exact match by name (normalized)
        for doc in docs:
            if doc.name and _normalize(doc.name) == norm_text:
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 4. Exact match by alias (normalized)
        for doc in docs:
            aliases = getattr(doc, "aliases", []) or []
            if any(_normalize(alias) == norm_text for alias in aliases):
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 5. Token overlap + fuzzy — limitado a MAX_RESULTS por seguridad
        query_tokens = _significant_tokens(text)
        if not query_tokens:
            # Keep short tokens (e.g. "rio") for legacy single-token queries
            query_tokens = {
                t for t in norm_text.split() if len(t) >= MIN_TOKEN_LENGTH
            }
        if not query_tokens:
            return ExperienceResolutionResult(
                status=ExperienceResolutionStatus.NOT_FOUND,
            )

        scored: list[tuple[float, ExperienceDocument]] = []
        for doc in docs[:MAX_RESULTS]:
            identity_score = _score_doc_against_query(doc, text)
            if identity_score > 0:
                scored.append((identity_score, doc))
                continue

            raw_haystack = " ".join(
                [
                    doc.name or "",
                    doc.slug or "",
                    doc.description or "",
                    " ".join(getattr(doc, "aliases", []) or []),
                    " ".join(getattr(doc, "tags", []) or []),
                ]
            )
            haystack = _normalize(raw_haystack)
            haystack_tokens = _significant_tokens(raw_haystack)
            match_count = sum(
                1
                for token in query_tokens
                if _token_matches_haystack(token, haystack, haystack_tokens)
            )
            if match_count > 0:
                scored.append((float(match_count), doc))

        if not scored:
            return ExperienceResolutionResult(
                status=ExperienceResolutionStatus.NOT_FOUND,
            )

        scored.sort(key=lambda x: x[0], reverse=True)
        top_score = scored[0][0]
        top_matches = [doc for score, doc in scored if score == top_score]

        if len(top_matches) == 1:
            doc = top_matches[0]
            return ExperienceResolutionResult(
                status=ExperienceResolutionStatus.FOUND,
                experience_id=str(doc.id),
                experience_name=doc.name,
                slug=doc.slug,
                confidence=round(min(top_score / max(len(query_tokens), 1), 1.0), 2),
            )

        return ExperienceResolutionResult(
            status=ExperienceResolutionStatus.AMBIGUOUS,
            candidates=[
                {
                    "experience_id": str(doc.id),
                    "name": doc.name,
                    "slug": doc.slug,
                }
                for doc in top_matches
            ],
        )

    async def resolve_many(
        self,
        query: str,
        experiences: list[ExperienceDocument] | None = None,
    ) -> list[ExperienceDocument]:
        """Load the catalog and return every experience mentioned in ``query``.

        Designed for detail requests that name one or several experiences
        (including typos). Prefer identity/alias hits; fall back to tags only
        when nothing matched by name.
        """
        if not query or not str(query).strip():
            return []

        text = str(query).strip()

        try:
            oid = PydanticObjectId(text)
            doc = await ExperienceDocument.get(oid)
            if doc:
                return [doc]
        except Exception:
            pass

        docs = (
            experiences
            if experiences is not None
            else await self._load_active()
        )
        if not docs:
            return []

        scored: list[tuple[float, ExperienceDocument]] = []
        for doc in docs:
            score = _score_doc_against_query(doc, text)
            if score > 0:
                scored.append((score, doc))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            seen: set[str] = set()
            ordered: list[ExperienceDocument] = []
            for _score, doc in scored:
                doc_id = str(getattr(doc, "id", ""))
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                ordered.append(doc)
            return ordered

        # Tag / description fallback (single best group) when no name hit
        query_tokens = _significant_tokens(text)
        if not query_tokens:
            return []

        tag_scored: list[tuple[int, ExperienceDocument]] = []
        for doc in docs[:MAX_RESULTS]:
            raw_haystack = " ".join(
                [
                    doc.name or "",
                    doc.slug or "",
                    doc.description or "",
                    " ".join(getattr(doc, "aliases", []) or []),
                    " ".join(getattr(doc, "tags", []) or []),
                ]
            )
            haystack = _normalize(raw_haystack)
            haystack_tokens = _significant_tokens(raw_haystack)
            match_count = sum(
                1
                for token in query_tokens
                if _token_matches_haystack(token, haystack, haystack_tokens)
            )
            if match_count > 0:
                tag_scored.append((match_count, doc))

        if not tag_scored:
            return []

        tag_scored.sort(key=lambda x: x[0], reverse=True)
        top = tag_scored[0][0]
        return [doc for score, doc in tag_scored if score == top]
