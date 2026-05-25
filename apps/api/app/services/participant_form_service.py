import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId

from app.common.enums import ParticipantFormStatus, ReservationStatus
from app.common.labels import ErrorCode
from app.core.config import settings
from app.core.errors import ApiError
from app.documents import (
    ExperienceDocument,
    LiabilityReleaseDocument,
    ParticipantDocument,
    ReservationDocument,
    ScheduleDocument,
)
from app.schemas.participant import (
    ParticipantFormCreateResponse,
    ParticipantFormInfoSchema,
    ParticipantPublicCreateSchema,
)
from app.services.mappers import form_info_to_response
from app.utils.pdf_generator import generate_liability_release_pdf


def _generate_raw_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_token(token: str) -> str:
    raw = token + settings.participant_form_token_secret
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


RISK_RELEASE_TEXT = (
    "Declaro que entiendo que la actividad ecuestre con mulas implica riesgos inherentes, "
    "incluyendo caídas, golpes, lesiones graves, incapacidad permanente o muerte. Acepto "
    "participar bajo mi propia responsabilidad, siguiendo instrucciones del personal de La Juana."
)


class ParticipantFormService:
    async def generate_form_link(
        self,
        reservation_id: str,
        force: bool = False,
        expires_in_days: int | None = None,
    ) -> ParticipantFormCreateResponse:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if reservation.status != ReservationStatus.CONFIRMED:
            raise ApiError(
                status_code=400,
                code=ErrorCode.PARTICIPANT_FORM_NOT_CONFIRMED,
                message="La reserva debe estar confirmada para generar el enlace.",
                details={"status": reservation.status.value},
            )

        if (
            not force
            and reservation.participant_form_status == ParticipantFormStatus.ACTIVE
            and reservation.participant_form_expires_at
            and reservation.participant_form_expires_at > _utc_now_naive()
        ):
            return self._build_response(reservation)

        if force and reservation.participant_form_status == ParticipantFormStatus.ACTIVE:
            reservation.participant_form_status = ParticipantFormStatus.REVOKED

        token = _generate_raw_token()
        token_hash = _hash_token(token)
        expiry_days = expires_in_days or settings.participant_form_token_expiry_days

        reservation.participant_form_token_hash = token_hash
        reservation.participant_form_created_at = _utc_now_naive()
        reservation.participant_form_expires_at = _utc_now_naive() + timedelta(days=expiry_days)
        reservation.participant_form_status = ParticipantFormStatus.ACTIVE
        reservation.participant_registration_limit = reservation.participant_count
        if not force:
            reservation.participant_registration_count = 0
        await reservation.save()

        response = self._build_response(reservation)
        response.form_url = f"{settings.participant_form_base_url}?token={token}"
        return response

    async def get_form_info(self, token: str) -> ParticipantFormInfoSchema:
        reservation = await self._find_by_token(token)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PARTICIPANT_FORM_INVALID_TOKEN,
                message="El enlace del formulario no es válido.",
            )

        if reservation.participant_form_status in (
            ParticipantFormStatus.EXPIRED,
            ParticipantFormStatus.REVOKED,
        ) or (
            reservation.participant_form_expires_at
            and reservation.participant_form_expires_at < _utc_now_naive()
        ):
            if reservation.participant_form_status != ParticipantFormStatus.REVOKED:
                reservation.participant_form_status = ParticipantFormStatus.EXPIRED
                await reservation.save()
            raise ApiError(
                status_code=410,
                code=ErrorCode.PARTICIPANT_FORM_EXPIRED,
                message="El enlace del formulario ha expirado.",
            )

        if reservation.participant_form_status == ParticipantFormStatus.FULL:
            raise ApiError(
                status_code=409,
                code=ErrorCode.PARTICIPANT_FORM_FULL,
                message="El formulario ya completó todos los cupos.",
                details={
                    "registered": reservation.participant_registration_count,
                    "limit": reservation.participant_registration_limit,
                },
            )

        experience_name = await self._get_experience_name(reservation.experience_id)
        start_time = await self._get_start_time(reservation.schedule_id)
        return form_info_to_response(reservation, experience_name, start_time)

    async def register_participant(
        self,
        token: str,
        payload: ParticipantPublicCreateSchema,
    ) -> ParticipantFormCreateResponse:
        token_hash = _hash_token(token)
        reservation = await ReservationDocument.find_one(
            {"participant_form_token_hash": token_hash}
        )
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PARTICIPANT_FORM_INVALID_TOKEN,
                message="El enlace del formulario no es válido.",
            )

        if reservation.participant_form_status != ParticipantFormStatus.ACTIVE:
            if reservation.participant_form_status == ParticipantFormStatus.FULL:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.PARTICIPANT_FORM_FULL,
                    message="El formulario ya completó todos los cupos.",
                )
            raise ApiError(
                status_code=410,
                code=ErrorCode.PARTICIPANT_FORM_EXPIRED,
                message="El enlace del formulario ha expirado.",
            )

        if (
            reservation.participant_form_expires_at
            and reservation.participant_form_expires_at < _utc_now_naive()
        ):
            reservation.participant_form_status = ParticipantFormStatus.EXPIRED
            await reservation.save()
            raise ApiError(
                status_code=410,
                code=ErrorCode.PARTICIPANT_FORM_EXPIRED,
                message="El enlace del formulario ha expirado.",
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

        limit = reservation.participant_registration_limit or 0
        if reservation.participant_registration_count >= limit:
            raise ApiError(
                status_code=409,
                code=ErrorCode.PARTICIPANT_FORM_FULL,
                message="El formulario ya completó todos los cupos.",
            )

        collection = ReservationDocument.get_motor_collection()
        result = await collection.find_one_and_update(
            {
                "_id": reservation.id,
                "participant_form_status": ParticipantFormStatus.ACTIVE,
                "participant_registration_count": {"$lt": limit},
                "participant_form_expires_at": {"$gt": _utc_now_naive()},
            },
            {"$inc": {"participant_registration_count": 1}},
        )
        if result is None:
            existing = await ReservationDocument.get(reservation.id)
            if existing and existing.participant_registration_count >= limit:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.PARTICIPANT_FORM_FULL,
                    message="El formulario ya completó todos los cupos.",
                )
            raise ApiError(
                status_code=409,
                code=ErrorCode.PARTICIPANT_FORM_EXPIRED,
                message="El enlace del formulario ha expirado o ya no está disponible.",
            )

        doc = ParticipantDocument(
            reservation_id=reservation.id,
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
            blood_type=payload.blood_type,
            eps_or_travel_insurance=payload.eps or payload.travel_insurance,
            health_conditions=payload.medical_conditions,
            sensory_disabilities=payload.functional_conditions,
            dietary_restrictions=payload.dietary_restrictions,
            emergency_contact={
                "name": payload.emergency_contact_name,
                "phone": payload.emergency_contact_phone,
                "relationship": payload.emergency_contact_relationship,
                "country": payload.emergency_contact_country,
            },
            accepted_data_processing=payload.accepted_data_processing,
            accepted_media_usage=payload.accepted_media_usage,
            accepted_risk_release=payload.accepted_risk_release,
            risk_release_text_version=payload.risk_release_text_version or RISK_RELEASE_TEXT,
            is_completed=True,
        )

        try:
            await doc.insert()

            release_text = payload.risk_release_text_version or RISK_RELEASE_TEXT
            pdf_bytes = generate_liability_release_pdf(release_text, f"{payload.first_name} {payload.last_name}")
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

            liability = LiabilityReleaseDocument(
                participant_id=doc.id,
                reservation_id=reservation.id,
                participant_name=f"{payload.first_name} {payload.last_name}",
                pdf_base64=pdf_base64,
                accepted_at=datetime.now(UTC),
            )
            await liability.insert()

            await collection.update_one(
                {"_id": reservation.id},
                {"$push": {"participant_ids": doc.id}},
            )

            updated = await ReservationDocument.get(reservation.id)
            if updated and updated.participant_registration_count >= (limit):
                await collection.update_one(
                    {"_id": reservation.id},
                    {
                        "$set": {
                            "participant_form_status": ParticipantFormStatus.FULL,
                        }
                    },
                )
        except Exception:
            await collection.update_one(
                {"_id": reservation.id},
                {"$inc": {"participant_registration_count": -1}},
            )
            raise

        response = self._build_response(updated or reservation)
        if updated:
            remaining = max(0, limit - updated.participant_registration_count)
            response.participants_registered = updated.participant_registration_count
            response.participants_remaining = remaining
            response.form_status = (
                ParticipantFormStatus.FULL if remaining == 0 else ParticipantFormStatus.ACTIVE
            )
        return response

    async def _find_by_token(self, token: str) -> ReservationDocument | None:
        token_hash = _hash_token(token)
        return await ReservationDocument.find_one({"participant_form_token_hash": token_hash})

    async def _get_experience_name(self, experience_id: PydanticObjectId) -> str:
        exp = await ExperienceDocument.get(experience_id)
        return exp.name if exp else "Experiencia"

    async def _get_start_time(self, schedule_id: PydanticObjectId | None) -> str | None:
        if schedule_id is None:
            return None
        schedule = await ScheduleDocument.get(schedule_id)
        return str(schedule.start_time) if schedule and schedule.start_time else None

    def _build_response(self, reservation: ReservationDocument) -> ParticipantFormCreateResponse:
        limit = reservation.participant_registration_limit or 0
        registered = reservation.participant_registration_count
        return ParticipantFormCreateResponse(
            reservation_id=str(reservation.id),
            public_reservation_code=reservation.code,
            form_url="",
            expires_at=reservation.participant_form_expires_at,
            participant_limit=limit,
            participants_registered=registered,
            participants_remaining=max(0, limit - registered),
            form_status=reservation.participant_form_status or ParticipantFormStatus.ACTIVE,
        )
