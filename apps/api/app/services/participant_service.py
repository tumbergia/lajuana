from datetime import UTC, datetime

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ParticipantDocument, ReservationDocument
from app.schemas.participant import ParticipantCreateSchema, ParticipantUpdateSchema

REQUIRED_FIELDS_FOR_OPERATIONAL_COMPLETION = (
    "first_name",
    "last_name",
    "birth_date",
    "document_type",
    "document_number",
    "phone",
    "country",
    "city",
    "height_cm",
    "weight_kg",
    "experience_level",
    "emergency_contact",
    "accepted_data_processing",
)


class ParticipantService:
    async def create(
        self,
        reservation_id: str,
        payload: ParticipantCreateSchema,
    ) -> ParticipantDocument:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code="reservation.not_found",
                message="Reserva no encontrada.",
            )
        if payload.birth_date >= datetime.now(UTC).date():
            raise ApiError(
                status_code=422,
                code="participant.invalid_birth_date",
                message="La fecha de nacimiento debe ser anterior a hoy.",
            )

        doc = ParticipantDocument(reservation_id=reservation.id, **payload.model_dump())
        doc.is_completed = self._is_completed(doc)
        await doc.insert()
        reservation.participant_ids.append(doc.id)
        await reservation.save()
        return doc

    async def update(
        self,
        participant_id: str,
        payload: ParticipantUpdateSchema,
    ) -> ParticipantDocument:
        doc = await ParticipantDocument.get(participant_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code="participant.not_found",
                message="Participante no encontrado.",
            )
        updates = payload.model_dump(exclude_none=True)
        if "birth_date" in updates and updates["birth_date"] >= datetime.now(UTC).date():
            raise ApiError(
                status_code=422,
                code="participant.invalid_birth_date",
                message="La fecha de nacimiento debe ser anterior a hoy.",
            )
        for field, value in updates.items():
            setattr(doc, field, value)
        doc.is_completed = self._is_completed(doc)
        await doc.save()
        return doc

    def _is_completed(self, participant: ParticipantDocument) -> bool:
        for field_name in REQUIRED_FIELDS_FOR_OPERATIONAL_COMPLETION:
            if getattr(participant, field_name, None) in (None, ""):
                return False
        if not participant.accepted_data_processing:
            return False
        return True

    def validate_completed(self, participant: ParticipantDocument) -> None:
        if not participant.is_completed:
            raise ApiError(
                status_code=422,
                code=ErrorCode.PARTICIPANT_INCOMPLETE,
                message="El participante no tiene completitud operativa.",
            )
