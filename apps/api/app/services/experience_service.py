from app.core.errors import ApiError
from app.documents import ExperienceDocument
from app.schemas.experience import ExperienceCreateSchema, ExperienceUpdateSchema


class ExperienceService:
    async def create(self, payload: ExperienceCreateSchema) -> ExperienceDocument:
        if payload.duration_hours is None and payload.duration_days is None:
            raise ApiError(
                status_code=422,
                code="experience.duration_required",
                message="Debes informar duración en horas o días.",
            )
        doc = ExperienceDocument(**payload.model_dump())
        await doc.insert()
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
                code="experience.not_found",
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
                status_code=422,
                code="experience.duration_required",
                message="Debes informar duración en horas o días.",
            )
        await doc.save()
        return doc
