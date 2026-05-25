from __future__ import annotations

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
    "ñ": "ñ",
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "Ü": "U",
    "Ñ": "Ñ",
}
_ACCENT_TABLE = str.maketrans(_ACCENT_MAP)

MIN_TOKEN_LENGTH = 3


def _strip_accents(text: str) -> str:
    return text.translate(_ACCENT_TABLE)


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

        docs = (
            experiences
            if experiences is not None
            else await ExperienceDocument.find({"is_active": True}).to_list()
        )

        # 2. Exact match by slug (normalized)
        norm_text = _strip_accents(text.lower())
        for doc in docs:
            if doc.slug and _strip_accents(doc.slug.lower()) == norm_text:
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 3. Exact match by name (normalized)
        for doc in docs:
            if doc.name and _strip_accents(doc.name.lower()) == norm_text:
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
            if any(_strip_accents(alias.lower()) == norm_text for alias in aliases):
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 5. Token overlap (normalized)
        query_tokens = {t for t in norm_text.split() if len(t) >= MIN_TOKEN_LENGTH}
        if not query_tokens:
            return ExperienceResolutionResult(
                status=ExperienceResolutionStatus.NOT_FOUND,
            )

        scored: list[tuple[int, ExperienceDocument]] = []
        for doc in docs:
            raw_haystack = " ".join(
                [
                    doc.name or "",
                    doc.slug or "",
                    doc.description or "",
                    " ".join(getattr(doc, "aliases", []) or []),
                    " ".join(getattr(doc, "tags", []) or []),
                ]
            )
            haystack = _strip_accents(raw_haystack.lower())
            match_count = sum(1 for token in query_tokens if token in haystack)
            if match_count > 0:
                scored.append((match_count, doc))

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
                confidence=round(top_score / len(query_tokens), 2),
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
