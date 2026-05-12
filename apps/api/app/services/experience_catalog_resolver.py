from __future__ import annotations

from enum import StrEnum

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.documents.experience_document import ExperienceDocument


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
    async def resolve(self, query: str) -> ExperienceResolutionResult:
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

        experiences = await ExperienceDocument.find(ExperienceDocument.is_active == True).to_list()  # noqa: E712

        # 2. Exact match by slug
        for doc in experiences:
            if doc.slug and doc.slug.lower() == text.lower():
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 3. Exact match by name
        for doc in experiences:
            if doc.name and doc.name.lower() == text.lower():
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 4. Exact match by alias
        for doc in experiences:
            aliases = getattr(doc, "aliases", []) or []
            if any(alias.lower() == text.lower() for alias in aliases):
                return ExperienceResolutionResult(
                    status=ExperienceResolutionStatus.FOUND,
                    experience_id=str(doc.id),
                    experience_name=doc.name,
                    slug=doc.slug,
                    confidence=1.0,
                )

        # 5. Token overlap
        query_tokens = {t for t in text.lower().split() if len(t) >= 4}
        if not query_tokens:
            return ExperienceResolutionResult(
                status=ExperienceResolutionStatus.NOT_FOUND,
            )

        scored: list[tuple[int, ExperienceDocument]] = []
        for doc in experiences:
            haystack = " ".join(
                [
                    doc.name or "",
                    doc.slug or "",
                    doc.description or "",
                    " ".join(getattr(doc, "aliases", []) or []),
                ]
            ).lower()
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
