from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import EquineDocument
from app.schemas.equine import EquineCreateSchema, EquineUpdateSchema


class EquineService:
    async def create(self, payload: EquineCreateSchema) -> EquineDocument:
        doc = EquineDocument(**payload.model_dump())
        await doc.insert()
        return doc

    async def list(self) -> list[EquineDocument]:
        return await EquineDocument.find_all().to_list()

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
        doc.is_available = False
        await doc.save()
        return doc
