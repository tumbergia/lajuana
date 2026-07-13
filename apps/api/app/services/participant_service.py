from datetime import UTC, datetime

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ParticipantDocument, ReservationDocument
from app.documents.audit_metadata_models import ParticipantMetadata
from app.documents.participant_document import EmergencyContact
from app.schemas.participant import (
    ParticipantCreateSchema,
    ParticipantNestedCreateSchema,
    ParticipantUpdateSchema,
)
from app.services.participant_form_link_service import ParticipantFormLinkService

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
    "emergency_contact",
    "accepted_data_processing",
)

RISK_RELEASE_TEXT = (
    "Declaro que entiendo que la actividad ecuestre con mulas implica riesgos inherentes, "
    "incluyendo caídas, golpes, lesiones graves, incapacidad permanente o muerte. Acepto "
    "participar bajo mi propia responsabilidad, siguiendo instrucciones del personal de La Juana."
)


class ParticipantService:
    def __init__(self, form_link_service: ParticipantFormLinkService) -> None:
        self.form_link_service = form_link_service

    async def _maybe_audit_participant_registered(
        self,
        doc: ParticipantDocument,
        *,
        was_completed: bool,
    ) -> None:
        if was_completed or not doc.is_completed:
            return
        reservation = await ReservationDocument.get(doc.reservation_id)
        if reservation is None:
            return
        from app.services.reservation_audit_helpers import write_reservation_audit_log

        participant_name = f"{doc.first_name} {doc.last_name}".strip()
        await write_reservation_audit_log(
            reservation=reservation,
            action="participant.registered",
            previous_status=reservation.status.value,
            new_status=reservation.status.value,
            metadata=ParticipantMetadata(
                participant_id=str(doc.id),
                participant_name=participant_name,
            ),
        )

        try:
            from app.common.enums import NotificationEventType
            from app.core.di import Container
            from app.core.logging import logger

            code = reservation.code or str(reservation.id)
            await Container.get_instance().notification_service.enqueue_admin_in_app(
                event_type=NotificationEventType.PARTICIPANT_FORM_COMPLETED,
                title="Participante completó formulario",
                body=f"{participant_name or 'Participante'} — reserva {code}",
                reservation_id=str(reservation.id),
                dedup_suffix=str(doc.id),
                contact_phone=reservation.holder_phone,
            )
        except Exception:
            from app.core.logging import logger

            logger.exception(
                "[participant=%s] Failed to enqueue form completed notification",
                doc.id,
            )

    async def get(self, participant_id: str) -> ParticipantDocument:
        doc = await ParticipantDocument.get(participant_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PARTICIPANT_NOT_FOUND,
                message="Participante no encontrado.",
            )
        return doc

    async def create(
        self,
        reservation_id: str,
        payload: ParticipantCreateSchema,
    ) -> ParticipantDocument:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if payload.birth_date >= datetime.now(UTC).date():
            raise ApiError(
                status_code=400,
                code=ErrorCode.PARTICIPANT_INVALID_BIRTH_DATE,
                message="La fecha de nacimiento debe ser anterior a hoy.",
            )

        doc = ParticipantDocument(reservation_id=reservation.id, **payload.model_dump())
        doc.is_completed = self._is_completed(doc)
        await doc.insert()
        reservation.participant_ids.append(doc.id)
        await reservation.save()
        await self._maybe_audit_participant_registered(doc, was_completed=False)
        return doc

    async def create_from_form(
        self,
        raw_token: str,
        payload: ParticipantNestedCreateSchema,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ParticipantDocument:
        form_link = await self.form_link_service.validate_token(raw_token)

        if payload.birth_date >= datetime.now(UTC).date():
            raise ApiError(
                status_code=400,
                code=ErrorCode.PARTICIPANT_INVALID_BIRTH_DATE,
                message="La fecha de nacimiento debe ser anterior a hoy.",
            )

        if not payload.accepted_data_processing:
            raise ApiError(
                status_code=422,
                code=ErrorCode.PARTICIPANT_DATA_PROCESSING_REQUIRED,
                message="Debe aceptar el tratamiento de datos personales.",
            )

        if not payload.accepted_risk_release:
            raise ApiError(
                status_code=422,
                code=ErrorCode.PARTICIPANT_RISK_RELEASE_REQUIRED,
                message="Debe aceptar la liberación de responsabilidad para participar.",
            )

        reservation = await ReservationDocument.get(form_link.reservation_id)

        doc = ParticipantDocument(
            reservation_id=form_link.reservation_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            birth_date=payload.birth_date,
            document_type=payload.document_type,
            document_number=payload.document_number,
            phone=payload.phone,
            country=payload.country,
            city=payload.city,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            experience_level=payload.experience_level,
            dietary_restrictions=payload.dietary_restrictions,
            blood_type=payload.blood_type,
            eps_or_travel_insurance=payload.eps_or_travel_insurance,
            health_conditions=payload.health_conditions,
            sensory_disabilities=payload.sensory_disabilities,
            emergency_contact=EmergencyContact(
                **payload.emergency_contact.model_dump()
            ),
            accepted_data_processing=payload.accepted_data_processing,
            accepted_media_usage=payload.accepted_media_usage,
            accepted_risk_release=payload.accepted_risk_release,
            risk_release_text_version=payload.risk_release_text_version or RISK_RELEASE_TEXT,
            submitted_at=datetime.now(UTC),
            source_form_link_id=form_link.id,
        )
        doc.is_completed = self._is_completed(doc)
        await doc.insert()

        if reservation is not None:
            reservation.participant_ids.append(doc.id)
            await reservation.save()

        await self.form_link_service.increment_used_count(form_link)
        await self.form_link_service.update_reservation_completion(form_link.reservation_id)

        await self._maybe_audit_participant_registered(doc, was_completed=False)
        return doc

    async def update(
        self,
        participant_id: str,
        payload: ParticipantUpdateSchema,
    ) -> ParticipantDocument:
        doc = await self.get(participant_id)
        updates = payload.model_dump(exclude_none=True)
        if "birth_date" in updates and updates["birth_date"] >= datetime.now(UTC).date():
            raise ApiError(
                status_code=400,
                code=ErrorCode.PARTICIPANT_INVALID_BIRTH_DATE,
                message="La fecha de nacimiento debe ser anterior a hoy.",
            )
        was_completed = doc.is_completed
        for field, value in updates.items():
            setattr(doc, field, value)
        doc.is_completed = self._is_completed(doc)
        await doc.save()
        await self._maybe_audit_participant_registered(doc, was_completed=was_completed)
        return doc

    def _is_completed(self, participant: ParticipantDocument) -> bool:
        for field_name in REQUIRED_FIELDS_FOR_OPERATIONAL_COMPLETION:
            if getattr(participant, field_name, None) in (None, ""):
                return False
        if not participant.accepted_data_processing:
            return False
        if participant.accepted_risk_release is not True:
            return False
        return True

    def validate_completed(self, participant: ParticipantDocument) -> None:
        if not participant.is_completed:
            raise ApiError(
                status_code=422,
                code=ErrorCode.PARTICIPANT_OPERATIONALLY_INCOMPLETE,
                message="El participante no tiene completitud operativa.",
            )

    def get_risk_release_text(self) -> str:
        return RISK_RELEASE_TEXT
