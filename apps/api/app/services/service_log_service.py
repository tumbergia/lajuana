from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ReservationDocument, ServiceLogDocument, ServiceLogEventType
from app.schemas.service_log import ServiceLogCreateSchema, ServiceLogUpdateSchema


class ServiceLogService:
    async def create(self, payload: ServiceLogCreateSchema) -> ServiceLogDocument:
        reservation = await ReservationDocument.get(payload.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if payload.event_type == ServiceLogEventType.CHECKPOINT and not payload.checkpoint_name:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_CHECKPOINT_NAME_REQUIRED,
                message="checkpoint_name es obligatorio para event_type checkpoint.",
            )
        doc = ServiceLogDocument(
            reservation_id=reservation.id,
            event_type=payload.event_type,
            happened_at=payload.happened_at,
            checkpoint_name=payload.checkpoint_name,
            notes=payload.notes,
            related_participant_id=payload.related_participant_id,
            related_equine_id=payload.related_equine_id,
        )
        await doc.insert()
        return doc

    async def get(self, log_id: str) -> ServiceLogDocument:
        doc = await ServiceLogDocument.get(log_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.LOG_NOT_FOUND,
                message="Log no encontrado.",
            )
        return doc

    async def update(self, log_id: str, payload: ServiceLogUpdateSchema) -> ServiceLogDocument:
        doc = await self.get(log_id)
        updates = payload.model_dump(exclude_none=True)
        event_type = updates.get("event_type", doc.event_type)
        checkpoint_name = updates.get("checkpoint_name", doc.checkpoint_name)
        if event_type == ServiceLogEventType.CHECKPOINT and not checkpoint_name:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_CHECKPOINT_NAME_REQUIRED,
                message="checkpoint_name es obligatorio para event_type checkpoint.",
            )
        for field, value in updates.items():
            setattr(doc, field, value)
        await doc.save()
        return doc
