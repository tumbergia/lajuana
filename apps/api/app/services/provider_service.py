from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ProviderDocument
from app.schemas.provider import ProviderCreateSchema, ProviderUpdateSchema


class ProviderService:
    async def create(self, payload: ProviderCreateSchema) -> ProviderDocument:
        doc = ProviderDocument(**payload.model_dump())
        await doc.insert()
        return doc

    async def get(self, provider_id: str) -> ProviderDocument:
        doc = await ProviderDocument.get(provider_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PROVIDER_NOT_FOUND,
                message="Proveedor no encontrado.",
            )
        return doc

    async def update(self, provider_id: str, payload: ProviderUpdateSchema) -> ProviderDocument:
        doc = await self.get(provider_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(doc, field, value)
        await doc.save()
        return doc

    async def delete(self, provider_id: str) -> None:
        doc = await self.get(provider_id)
        await doc.delete()
