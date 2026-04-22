from pymongo.errors import DuplicateKeyError

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument
from app.schemas.experience import ExperienceCreateSchema, ExperienceUpdateSchema


class ExperienceService:
    @staticmethod
    def _raise_conflict_from_duplicate(exc: DuplicateKeyError) -> None:
        details = exc.details if isinstance(exc.details, dict) else {}
        key_pattern = details.get("keyPattern", {})
        if "slug" in key_pattern or "slug_1" in str(exc):
            raise ApiError(
                status_code=409,
                code=ErrorCode.EXPERIENCE_SLUG_ALREADY_EXISTS,
                message="Ya existe una experiencia con ese slug.",
                details={"field": "slug"},
            ) from exc
        raise ApiError(
            status_code=409,
            code=ErrorCode.CONFLICT,
            message="Existe un conflicto al guardar la experiencia.",
            details={"collection": "experiences"},
        ) from exc

    async def create(self, payload: ExperienceCreateSchema) -> ExperienceDocument:
        if payload.duration_hours is None and payload.duration_days is None:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_INVALID_DURATION,
                message="Debes informar duracion en horas o dias.",
            )
        doc = ExperienceDocument(**payload.model_dump())
        try:
            await doc.insert()
        except DuplicateKeyError as exc:
            self._raise_conflict_from_duplicate(exc)
        return doc

    async def list(self, is_active: bool | None = None) -> list[ExperienceDocument]:
        if is_active is None:
            return await ExperienceDocument.find_all().to_list()
        return await ExperienceDocument.find(ExperienceDocument.is_active == is_active).to_list()

    async def get(self, experience_id: str) -> ExperienceDocument:
        doc = await ExperienceDocument.get(experience_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EXPERIENCE_NOT_FOUND,
                message="Experiencia no encontrada.",
            )
        return doc

    async def update(
        self,
        experience_id: str,
        payload: ExperienceUpdateSchema,
    ) -> ExperienceDocument:
        doc = await self.get(experience_id)
        updates = payload.model_dump(exclude_none=True)
        for field, value in updates.items():
            setattr(doc, field, value)
        if doc.duration_hours is None and doc.duration_days is None:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_INVALID_DURATION,
                message="Debes informar duracion en horas o dias.",
            )
        try:
            await doc.save()
        except DuplicateKeyError as exc:
            self._raise_conflict_from_duplicate(exc)
        return doc

    async def deactivate(self, experience_id: str) -> ExperienceDocument:
        doc = await self.get(experience_id)
        doc.is_active = False
        await doc.save()
        return doc

