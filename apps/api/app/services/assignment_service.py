from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ParticipantDocument,
    ReservationDocument,
    SaddleDocument,
)
from app.schemas.assignment import AssignmentCreateSchema, AssignmentUpdateSchema


class AssignmentService:
    async def create(self, payload: AssignmentCreateSchema) -> AssignmentDocument:
        reservation = await ReservationDocument.get(payload.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        participant = await ParticipantDocument.get(payload.participant_id)
        if participant is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PARTICIPANT_NOT_FOUND,
                message="Participante no encontrado.",
            )
        if participant.reservation_id != reservation.id:
            raise ApiError(
                status_code=400,
                code=ErrorCode.ASSIGNMENT_PARTICIPANT_NOT_IN_RESERVATION,
                message="El participante no pertenece a la reserva.",
            )
        equine = await EquineDocument.get(payload.equine_id)
        if equine is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EQUINE_NOT_FOUND,
                message="Equino no encontrado.",
            )
        if not equine.is_available:
            raise ApiError(
                status_code=409,
                code=ErrorCode.EQUINE_UNAVAILABLE,
                message="Equino no disponible.",
            )

        dup_e = await AssignmentDocument.find_one(
            AssignmentDocument.reservation_id == reservation.id,
            AssignmentDocument.equine_id == equine.id,
        )
        if dup_e is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_EQUINE_ALREADY_ASSIGNED,
                message="El equino ya está asignado para esta salida.",
            )

        saddle_obj = None
        if payload.saddle_id:
            saddle_obj = await SaddleDocument.get(payload.saddle_id)
            if saddle_obj is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.SADDLE_NOT_FOUND,
                    message="Silla no encontrada.",
                )
            if not saddle_obj.is_available:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.SADDLE_UNAVAILABLE,
                    message="Silla no disponible.",
                )
            dup_s = await AssignmentDocument.find_one(
                AssignmentDocument.reservation_id == reservation.id,
                AssignmentDocument.saddle_id == saddle_obj.id,
            )
            if dup_s is not None:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.ASSIGNMENT_SADDLE_ALREADY_ASSIGNED,
                    message="La silla ya está asignada para esta salida.",
                )

        doc = AssignmentDocument(
            reservation_id=reservation.id,
            participant_id=participant.id,
            equine_id=equine.id,
            saddle_id=saddle_obj.id if saddle_obj else None,
            priority=payload.priority,
            assigned_manually=payload.assigned_manually,
            notes=payload.notes,
        )
        await doc.insert()
        return doc

    async def get(self, assignment_id: str) -> AssignmentDocument:
        doc = await AssignmentDocument.get(assignment_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.ASSIGNMENT_NOT_FOUND,
                message="Asignación no encontrada.",
            )
        return doc

    async def update(
        self,
        assignment_id: str,
        payload: AssignmentUpdateSchema,
    ) -> AssignmentDocument:
        doc = await self.get(assignment_id)
        updates = payload.model_dump(exclude_none=True)
        if "equine_id" in updates:
            equine = await EquineDocument.get(updates["equine_id"])
            if equine is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.EQUINE_NOT_FOUND,
                    message="Equino no encontrado.",
                )
            if not equine.is_available:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.EQUINE_UNAVAILABLE,
                    message="Equino no disponible.",
                )
            dup_e = await AssignmentDocument.find_one(
                AssignmentDocument.id != doc.id,
                AssignmentDocument.reservation_id == doc.reservation_id,
                AssignmentDocument.equine_id == equine.id,
            )
            if dup_e is not None:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.ASSIGNMENT_EQUINE_ALREADY_ASSIGNED,
                    message="El equino ya está asignado para esta salida.",
                )
            doc.equine_id = equine.id
        if "saddle_id" in updates and updates["saddle_id"] is not None:
            saddle = await SaddleDocument.get(updates["saddle_id"])
            if saddle is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.SADDLE_NOT_FOUND,
                    message="Silla no encontrada.",
                )
            if not saddle.is_available:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.SADDLE_UNAVAILABLE,
                    message="Silla no disponible.",
                )
            dup_s = await AssignmentDocument.find_one(
                AssignmentDocument.id != doc.id,
                AssignmentDocument.reservation_id == doc.reservation_id,
                AssignmentDocument.saddle_id == saddle.id,
            )
            if dup_s is not None:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.ASSIGNMENT_SADDLE_ALREADY_ASSIGNED,
                    message="La silla ya está asignada para esta salida.",
                )
            doc.saddle_id = saddle.id
        for field in ("priority", "assigned_manually", "notes"):
            if field in updates:
                setattr(doc, field, updates[field])
        await doc.save()
        return doc
