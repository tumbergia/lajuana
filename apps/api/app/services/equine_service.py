from __future__ import annotations

from app.common.enums import EquineOperationalStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import EquineDocument
from app.schemas.equine import EquineCreateSchema, EquineUpdateSchema


class EquineService:
    async def create(self, payload: EquineCreateSchema) -> EquineDocument:
        doc = EquineDocument(**payload.model_dump())
        await doc.insert()
        return doc

    async def list(
        self,
        operational_status: EquineOperationalStatus | None = None,
        is_active: bool | None = None,
        is_available: bool | None = None,
    ) -> list[EquineDocument]:
        query = {}
        if operational_status is not None:
            query["operational_status"] = operational_status
        if is_active is not None:
            query["is_active"] = is_active
        if is_available is not None:
            query["is_available"] = is_available
        return await EquineDocument.find(query).to_list()

    async def list_items(
        self,
        operational_status: EquineOperationalStatus | None = None,
        is_active: bool | None = None,
        is_available: bool | None = None,
    ) -> list[EquineDocument]:
        """Retorna solo los campos del list item (usa el mismo query pero más liviano)."""
        return await self.list(
            operational_status=operational_status,
            is_active=is_active,
            is_available=is_available,
        )

    async def get(self, equine_id: str) -> EquineDocument:
        doc = await EquineDocument.get(equine_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EQUINE_NOT_FOUND,
                message="Equino no encontrado.",
            )
        return doc

    async def update(self, equine_id: str, payload: EquineUpdateSchema) -> EquineDocument:
        doc = await self.get(equine_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(doc, field, value)
        await doc.save()
        return doc

    async def deactivate(self, equine_id: str) -> EquineDocument:
        doc = await self.get(equine_id)
        doc.is_active = False
        doc.is_available = False
        doc.operational_status = EquineOperationalStatus.RETIRED
        await doc.save()
        return doc
