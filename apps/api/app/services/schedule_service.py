from datetime import date

from app.common.enums import ScheduleStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument, ScheduleDocument
from app.schemas.schedule import ScheduleCreateSchema, ScheduleUpdateSchema


def compute_available_slots(
    *,
    capacity_total: int,
    reserved_slots: int,
    blocked_slots: int,
    internal_slots: int,
) -> int:
    available = capacity_total - reserved_slots - blocked_slots - internal_slots
    if available < 0:
        raise ApiError(
            status_code=400,
            code=ErrorCode.SCHEDULE_NEGATIVE_AVAILABILITY,
            message="Los cupos resultan en un valor negativo.",
        )
    return available


class ScheduleService:
    async def create(self, payload: ScheduleCreateSchema) -> ScheduleDocument:
        experience = await ExperienceDocument.get(payload.experience_id)
        if experience is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EXPERIENCE_NOT_FOUND,
                message="Experiencia no encontrada.",
            )

        available_slots = compute_available_slots(
            capacity_total=payload.capacity_total,
            reserved_slots=payload.reserved_slots,
            blocked_slots=payload.blocked_slots,
            internal_slots=payload.internal_slots,
        )
        if not payload.is_active:
            status = ScheduleStatus.CLOSED
        else:
            status = ScheduleStatus.FULL if available_slots == 0 else ScheduleStatus.OPEN

        doc = ScheduleDocument(
            **payload.model_dump(),
            available_slots=available_slots,
            status=status,
        )
        await doc.insert()
        return doc

    async def list(
        self,
        *,
        experience_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: ScheduleStatus | None = None,
        is_active: bool | None = None,
    ) -> list[ScheduleDocument]:
        query = []
        if experience_id:
            query.append(ScheduleDocument.experience_id == experience_id)
        if date_from:
            query.append(ScheduleDocument.date >= date_from)
        if date_to:
            query.append(ScheduleDocument.date <= date_to)
        if status:
            query.append(ScheduleDocument.status == status)
        if is_active is not None:
            query.append(ScheduleDocument.is_active == is_active)
        if not query:
            return await ScheduleDocument.find_all().to_list()
        return await ScheduleDocument.find(*query).to_list()

    async def get(self, schedule_id: str) -> ScheduleDocument:
        doc = await ScheduleDocument.get(schedule_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.SCHEDULE_NOT_FOUND,
                message="Agenda no encontrada.",
            )
        return doc

    async def update(self, schedule_id: str, payload: ScheduleUpdateSchema) -> ScheduleDocument:
        doc = await self.get(schedule_id)
        updates = payload.model_dump(exclude_none=True)
        for field, value in updates.items():
            setattr(doc, field, value)

        doc.available_slots = compute_available_slots(
            capacity_total=doc.capacity_total,
            reserved_slots=doc.reserved_slots,
            blocked_slots=doc.blocked_slots,
            internal_slots=doc.internal_slots,
        )
        if doc.is_active is False:
            doc.status = ScheduleStatus.CLOSED
        elif doc.available_slots == 0:
            doc.status = ScheduleStatus.FULL
        elif doc.status == ScheduleStatus.FULL:
            doc.status = ScheduleStatus.OPEN

        await doc.save()
        return doc

    async def deactivate(self, schedule_id: str) -> ScheduleDocument:
        doc = await self.get(schedule_id)
        doc.is_active = False
        doc.status = ScheduleStatus.CLOSED
        await doc.save()
        return doc
