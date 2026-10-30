from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.common.labels import ErrorCode
from app.documents import ProviderDocument, ProviderStatus
from app.documents.provider_document import ProviderType
from app.schemas.provider import ProviderCreateSchema, ProviderUpdateSchema
from app.services.base_service import BaseService


def _normalize_lookup_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-z0-9._-]+", " ", ascii_text.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _build_provider_label(provider: ProviderDocument) -> str:
    if provider.slug:
        return f"{provider.name} ({provider.slug})"
    return provider.name


class ProviderService(BaseService[ProviderDocument, ProviderCreateSchema, ProviderUpdateSchema]):
    document_class = ProviderDocument
    not_found_code = ErrorCode.PROVIDER_NOT_FOUND
    not_found_message = "Proveedor no encontrado."
    sync_entity_type = "provider"

    async def resolve_provider_reference(self, reference: str) -> dict[str, Any]:
        query = reference.strip()
        if not query:
            return {"status": "missing"}

        normalized_query = _normalize_lookup_text(query)
        query_has_multiple_tokens = " " in normalized_query
        providers = await self.list(limit=200)
        candidates: list[dict[str, Any]] = []

        for provider in providers:
            name = _normalize_lookup_text(provider.name)
            slug = _normalize_lookup_text(provider.slug)
            contact_name = _normalize_lookup_text(provider.contact_name or "")
            location_label = _normalize_lookup_text(provider.location_label or "")
            tokens = [token for token in name.split(" ") if token]
            score = 0

            if normalized_query == slug:
                score = 100
            elif query_has_multiple_tokens and normalized_query == name:
                score = 95
            elif query_has_multiple_tokens and normalized_query == contact_name:
                score = 90
            elif normalized_query in tokens:
                score = 88
            elif any(token.startswith(normalized_query) for token in tokens):
                score = 80
            elif name.startswith(normalized_query) or slug.startswith(normalized_query):
                score = 78
            elif (
                normalized_query in name
                or normalized_query in slug
                or normalized_query in contact_name
            ):
                score = 64
            elif location_label and normalized_query in location_label:
                score = 60

            if score == 0:
                continue

            candidates.append(
                {
                    "score": score,
                    "provider": provider,
                    "summary": {
                        "provider_id": str(provider.id),
                        "name": provider.name,
                        "slug": provider.slug,
                        "is_active": provider.is_active,
                        "label": _build_provider_label(provider),
                    },
                }
            )

        if not candidates:
            return {"status": "not_found", "reference": query, "matches": []}

        candidates.sort(
            key=lambda item: (
                -item["score"],
                not item["provider"].is_active,
                len(item["provider"].name),
            )
        )
        top_score = candidates[0]["score"]
        top_candidates = [item for item in candidates if item["score"] == top_score]

        if len(top_candidates) == 1 and top_score >= 78:
            provider = top_candidates[0]["provider"]
            return {
                "status": "resolved",
                "reference": query,
                "provider_id": str(provider.id),
                "label": _build_provider_label(provider),
                "match_score": top_score,
            }

        return {
            "status": "ambiguous",
            "reference": query,
            "matches": [item["summary"] for item in candidates[:5]],
        }

    def _build_query(
        self,
        *,
        provider_type: ProviderType | None = None,
        status: ProviderStatus | None = None,
        q: str | None = None,
        service_category: str | None = None,
        is_active: bool | None = None,
        include_deleted: bool = False,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        if not include_deleted:
            query["deleted_at"] = None
        if provider_type is not None:
            query["type"] = provider_type
        if status is not None:
            query["status"] = status
        if is_active is not None:
            query["is_active"] = is_active
        if service_category:
            query["service_categories"] = service_category
        if q:
            pattern = re.escape(q.strip())
            query["$or"] = [
                {"name": {"$regex": pattern, "$options": "i"}},
                {"slug": {"$regex": pattern, "$options": "i"}},
                {"location_label": {"$regex": pattern, "$options": "i"}},
                {"contact_name": {"$regex": pattern, "$options": "i"}},
            ]
        return query

    async def list(
        self,
        provider_type: ProviderType | None = None,
        status: ProviderStatus | None = None,
        q: str | None = None,
        service_category: str | None = None,
        is_active: bool | None = None,
        include_deleted: bool = False,
        limit: int = 200,
        skip: int = 0,
    ) -> list[ProviderDocument]:
        query = self._build_query(
            provider_type=provider_type,
            status=status,
            q=q,
            service_category=service_category,
            is_active=is_active,
            include_deleted=include_deleted,
        )
        return await ProviderDocument.find(query).skip(skip).limit(limit).to_list()

    async def count(
        self,
        provider_type: ProviderType | None = None,
        status: ProviderStatus | None = None,
        q: str | None = None,
        service_category: str | None = None,
        is_active: bool | None = None,
        include_deleted: bool = False,
    ) -> int:
        query = self._build_query(
            provider_type=provider_type,
            status=status,
            q=q,
            service_category=service_category,
            is_active=is_active,
            include_deleted=include_deleted,
        )
        return await ProviderDocument.find(query).count()

    async def delete(self, provider_id: str) -> None:
        """Desactiva un proveedor sin borrarlo lógicamente."""
        doc = await self.get(provider_id)
        doc.is_active = False
        doc.status = ProviderStatus.INACTIVE
        await doc.save()
