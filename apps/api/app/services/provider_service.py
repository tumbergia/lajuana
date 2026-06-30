from __future__ import annotations

import re
from typing import Any

from app.common.labels import ErrorCode
from app.documents import ProviderDocument, ProviderStatus
from app.documents.provider_document import ProviderType
from app.schemas.provider import ProviderCreateSchema, ProviderUpdateSchema
from app.services.base_service import BaseService


class ProviderService(BaseService[ProviderDocument, ProviderCreateSchema, ProviderUpdateSchema]):
    document_class = ProviderDocument
    not_found_code = ErrorCode.PROVIDER_NOT_FOUND
    not_found_message = "Proveedor no encontrado."

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
