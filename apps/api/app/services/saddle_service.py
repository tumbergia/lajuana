from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import SaddleDocument
from app.schemas.saddle import SaddleCreateSchema, SaddleUpdateSchema


class SaddleService:
    async def create(self, payload: SaddleCreateSchema) -> SaddleDocument:
        existing = await SaddleDocument.find_one(SaddleDocument.code == payload.code)
        if existing is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.SADDLE_CODE_ALREADY_EXISTS,
                message="El código de silla ya existe.",
            )
        doc = SaddleDocument(**payload.model_dump())
        await doc.insert()
        return doc

    async def list(self) -> list[SaddleDocument]:
        return await SaddleDocument.find_all().to_list()

    async def get(self, saddle_id: str) -> SaddleDocument:
        doc = await SaddleDocument.get(saddle_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.SADDLE_NOT_FOUND,
                message="Silla no encontrada.",
            )
        return doc

    async def update(self, saddle_id: str, payload: SaddleUpdateSchema) -> SaddleDocument:
        doc = await self.get(saddle_id)
        updates = payload.model_dump(exclude_none=True)
        if "code" in updates:
            existing = await SaddleDocument.find_one(SaddleDocument.code == updates["code"])
            if existing is not None and existing.id != doc.id:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.SADDLE_CODE_ALREADY_EXISTS,
                    message="El código de silla ya existe.",
                )
        for field, value in updates.items():
            setattr(doc, field, value)
        await doc.save()
        return doc
