import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId

from app.common.constants import PARTICIPANT_FORM_LINK_EXPIRY_HOURS, PARTICIPANT_FORM_TOKEN_BYTES
from app.common.enums import ParticipantFormLinkStatus, ParticipantFormStatus, ReservationStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


from app.documents import (
    ExperienceDocument,
    ParticipantDocument,
    ParticipantFormLinkDocument,
    ReservationDocument,
)


class ParticipantFormLinkService:
    def _generate_token(self) -> tuple[str, str]:
        raw = secrets.token_hex(PARTICIPANT_FORM_TOKEN_BYTES)
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        return raw, hashed

    def _hash_token(self, raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()

    async def generate(
        self,
        reservation_id: str,
        expected_participants_count: int,
        created_by: PydanticObjectId | None = None,
        channel: str = "whatsapp",
        sent_to_phone: str | None = None,
    ) -> tuple[ParticipantFormLinkDocument, str]:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if reservation.status != ReservationStatus.CONFIRMED:
            raise ApiError(
                status_code=409,
                code=ErrorCode.FORM_LINK_RESERVATION_NOT_CONFIRMED,
                message="La reserva debe estar confirmada para generar el formulario.",
            )

        reservation.expected_participants_count = expected_participants_count
        reservation.participant_form_status = ParticipantFormStatus.SENT
        await reservation.save()

        raw_token, hashed = self._generate_token()
        expires_at = _utc_now() + timedelta(hours=PARTICIPANT_FORM_LINK_EXPIRY_HOURS)

        doc = ParticipantFormLinkDocument(
            reservation_id=reservation.id,
            token_hash=hashed,
            expires_at=expires_at,
            max_participants=expected_participants_count,
            created_by=created_by,
            channel=channel,
            sent_to_phone=sent_to_phone,
        )
        await doc.insert()
        return doc, raw_token

    async def validate_token(self, raw_token: str) -> ParticipantFormLinkDocument:
        hashed = self._hash_token(raw_token)
        doc = await ParticipantFormLinkDocument.find_one(
            ParticipantFormLinkDocument.token_hash == hashed
        )
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.FORM_LINK_INVALID_TOKEN,
                message="El enlace no es válido.",
            )
        if doc.status == ParticipantFormLinkStatus.REVOKED:
            raise ApiError(
                status_code=410,
                code=ErrorCode.FORM_LINK_REVOKED,
                message="El enlace fue revocado.",
            )
        if doc.status == ParticipantFormLinkStatus.EXPIRED or doc.expires_at < _utc_now():
            doc.status = ParticipantFormLinkStatus.EXPIRED
            await doc.save()
            raise ApiError(
                status_code=410,
                code=ErrorCode.FORM_LINK_EXPIRED,
                message="El enlace ha expirado.",
            )
        if doc.status == ParticipantFormLinkStatus.COMPLETED:
            raise ApiError(
                status_code=409,
                code=ErrorCode.FORM_LINK_ALREADY_COMPLETED,
                message="El formulario ya fue completado para todos los participantes.",
            )
        if doc.used_count >= doc.max_participants:
            raise ApiError(
                status_code=409,
                code=ErrorCode.FORM_LINK_MAX_PARTICIPANTS_REACHED,
                message="Se alcanzó el número máximo de participantes.",
            )
        return doc

    async def get_link_by_reservation(
        self, reservation_id: str
    ) -> ParticipantFormLinkDocument | None:
        return await ParticipantFormLinkDocument.find_one(
            ParticipantFormLinkDocument.reservation_id == PydanticObjectId(reservation_id),
            sort=[("created_at", -1)],
        )

    async def get_public_status(
        self, raw_token: str
    ) -> dict:
        hashed = self._hash_token(raw_token)
        doc = await ParticipantFormLinkDocument.find_one(
            ParticipantFormLinkDocument.token_hash == hashed
        )
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.FORM_LINK_INVALID_TOKEN,
                message="El enlace no es válido.",
            )

        reservation = await ReservationDocument.get(doc.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        experience = await ExperienceDocument.get(reservation.experience_id)
        experience_name = experience.name if experience else ""

        return {
            "reservation_code": reservation.code,
            "experience_name": experience_name,
            "requested_date": (
                reservation.requested_date.isoformat() if reservation.requested_date else None
            ),
            "completed_count": reservation.participants_completed_count,
            "expected_count": doc.max_participants,
            "is_complete": (
                reservation.participants_completed_count >= doc.max_participants
            ),
            "link_status": doc.status,
        }

    async def revoke(self, reservation_id: str) -> ParticipantFormLinkDocument:
        doc = await self.get_link_by_reservation(reservation_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.FORM_LINK_NOT_FOUND,
                message="No hay enlace activo para esta reserva.",
            )
        doc.status = ParticipantFormLinkStatus.REVOKED
        doc.revoked_at = _utc_now()
        await doc.save()

        reservation = await ReservationDocument.get(reservation_id)
        if reservation is not None:
            reservation.participant_form_status = ParticipantFormStatus.REVOKED
            await reservation.save()

        return doc

    async def increment_used_count(self, doc: ParticipantFormLinkDocument) -> None:
        doc.used_count += 1
        if doc.used_count >= doc.max_participants:
            doc.status = ParticipantFormLinkStatus.COMPLETED
            doc.completed_at = _utc_now()
        await doc.save()

    async def update_reservation_completion(
        self, reservation_id: PydanticObjectId
    ) -> None:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            return

        total_completed = await ParticipantDocument.find(
            ParticipantDocument.reservation_id == reservation_id,
            ParticipantDocument.is_completed,
        ).count()

        reservation.participants_completed_count = total_completed

        if (
            reservation.expected_participants_count is not None
            and total_completed >= reservation.expected_participants_count
        ):
            reservation.participant_form_status = ParticipantFormStatus.COMPLETE
        elif total_completed > 0:
            reservation.participant_form_status = ParticipantFormStatus.PARTIAL

        await reservation.save()
