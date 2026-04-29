"""Servicio de negocio para el agregado Reservation."""

import secrets
from datetime import UTC, date, datetime

from beanie import PydanticObjectId

from app.common.enums import PaymentStatus, ReservationStatus, ScheduleStatus, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ReservationDocument, ScheduleDocument
from app.services.config_service import ConfigService

ALLOWED_RESERVATION_TRANSITIONS = {
    ReservationStatus.CONTACT: {ReservationStatus.QUOTED, ReservationStatus.CANCELLED},
    ReservationStatus.QUOTED: {ReservationStatus.PENDING_PAYMENT, ReservationStatus.CANCELLED},
    ReservationStatus.PENDING_PAYMENT: {
        ReservationStatus.PAYMENT_RECEIVED,
        ReservationStatus.CANCELLED,
    },
    ReservationStatus.PAYMENT_RECEIVED: {ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED},
    ReservationStatus.CONFIRMED: {ReservationStatus.COMPLETED, ReservationStatus.CANCELLED},
    ReservationStatus.CANCELLED: set(),
    ReservationStatus.COMPLETED: set(),
}


def _today() -> date:
    return datetime.now(UTC).date()


class ReservationService:
    """Orquesta reglas críticas de confirmación/cancelación de reservas."""

    def __init__(self) -> None:
        self.config_service = ConfigService()

    async def create(
        self,
        payload: dict,
        actor_id: PydanticObjectId | None = None,
    ) -> ReservationDocument:
        doc = ReservationDocument(
            **payload,
            code=self._build_code(),
            created_by=actor_id,
            updated_by=actor_id,
        )
        await doc.insert()
        return doc

    async def list(self, actor_role: UserRole) -> list[ReservationDocument]:
        if actor_role == UserRole.GUIDE:
            return await ReservationDocument.find(
                ReservationDocument.status == ReservationStatus.CONFIRMED
            ).to_list()
        return await ReservationDocument.find_all().to_list()

    async def get(
        self,
        reservation_id: str,
        actor_role: UserRole | None = None,
    ) -> ReservationDocument:
        doc = await ReservationDocument.get(reservation_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if actor_role == UserRole.GUIDE and doc.status != ReservationStatus.CONFIRMED:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        return doc

    async def find_by_code_or_id(self, identifier: str) -> ReservationDocument | None:
        """Busca una reserva por su ObjectId (24 caracteres) o usando coincidencia parcial del código."""
        if len(identifier) == 24:
            doc = await ReservationDocument.get(identifier)
            if doc:
                return doc
        return await ReservationDocument.find_one({"code": {"$regex": identifier, "$options": "i"}})

    async def update(
        self,
        reservation_id: str,
        payload: dict,
        actor_id: PydanticObjectId | None = None,
    ) -> ReservationDocument:
        doc = await self.get(reservation_id)
        for field, value in payload.items():
            setattr(doc, field, value)
        doc.updated_by = actor_id
        await doc.save()
        return doc

    async def transition_status(
        self,
        reservation: ReservationDocument,
        target_status: ReservationStatus,
    ) -> None:
        allowed = ALLOWED_RESERVATION_TRANSITIONS.get(reservation.status, set())
        if target_status not in allowed:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_INVALID_STATUS_TRANSITION,
                message="La transición de estado no es válida.",
                details={"from": reservation.status, "to": target_status},
            )
        reservation.status = target_status

    async def confirm_reservation(
        self,
        reservation_id: str,
        actor_id: PydanticObjectId | None = None,
    ) -> ReservationDocument:
        """Confirma una reserva validando estado, anticipación, pago y cupos."""
        reservation = await self.get(reservation_id)
        rules = await self.config_service.get_reservation_rules()

        if reservation.schedule_id is None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_CONFIRMATION_NOT_ALLOWED,
                message="La confirmación requiere una agenda operativa.",
            )

        schedule = await ScheduleDocument.get(reservation.schedule_id)
        if schedule is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.SCHEDULE_NOT_FOUND,
                message="Agenda no encontrada.",
            )
        if not schedule.is_active:
            raise ApiError(
                status_code=409,
                code=ErrorCode.SCHEDULE_NOT_OPEN,
                message="La agenda esta desactivada para confirmar.",
                details={"schedule_id": str(schedule.id), "status": "inactive"},
            )
        if schedule.status != ScheduleStatus.OPEN:
            raise ApiError(
                status_code=409,
                code=ErrorCode.SCHEDULE_NOT_OPEN,
                message="La agenda no está abierta para confirmar.",
            )

        service_date = reservation.requested_date or schedule.date
        delta_days = (service_date - _today()).days
        if delta_days < rules.min_days_in_advance:
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_MIN_NOTICE_VIOLATION,
                message="La reserva no cumple la anticipación mínima configurada.",
                details={
                    "required_days": rules.min_days_in_advance,
                    "service_date": service_date.isoformat(),
                },
            )

        if rules.require_payment_proof_for_confirmation and (
            reservation.payment_status not in {PaymentStatus.RECEIVED, PaymentStatus.VERIFIED}
            or not reservation.payment_proof_ids
        ):
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_PAYMENT_REQUIRED,
                message="No se puede confirmar sin pago/comprobante válido.",
            )

        if schedule.available_slots < reservation.participant_count:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_NO_AVAILABILITY,
                message="No hay cupos disponibles para confirmar esta reserva.",
                details={
                    "schedule_id": str(schedule.id),
                    "available_slots": schedule.available_slots,
                    "required_slots": reservation.participant_count,
                },
            )

        await self.transition_status(reservation, ReservationStatus.CONFIRMED)
        schedule.reserved_slots += reservation.participant_count
        schedule.available_slots -= reservation.participant_count
        if schedule.available_slots == 0:
            schedule.status = ScheduleStatus.FULL

        reservation.confirmed_at = datetime.now(UTC)
        reservation.updated_by = actor_id
        await schedule.save()
        await reservation.save()
        return reservation

    async def set_status(
        self,
        reservation_id: str,
        target_status: ReservationStatus,
        actor_id: PydanticObjectId | None = None,
    ) -> ReservationDocument:
        reservation = await self.get(reservation_id)
        await self.transition_status(reservation, target_status)
        reservation.updated_by = actor_id
        if target_status == ReservationStatus.PAYMENT_RECEIVED:
            reservation.payment_status = PaymentStatus.RECEIVED
        await reservation.save()
        return reservation

    async def cancel_reservation(
        self,
        reservation_id: str,
        actor_id: PydanticObjectId | None = None,
    ) -> ReservationDocument:
        reservation = await self.get(reservation_id)
        previous_status = reservation.status
        await self.transition_status(reservation, ReservationStatus.CANCELLED)

        if previous_status == ReservationStatus.CONFIRMED and reservation.schedule_id:
            schedule = await ScheduleDocument.get(reservation.schedule_id)
            if schedule is not None:
                schedule.reserved_slots = max(
                    0,
                    schedule.reserved_slots - reservation.participant_count,
                )
                schedule.available_slots = (
                    schedule.capacity_total
                    - schedule.reserved_slots
                    - schedule.internal_slots
                    - schedule.blocked_slots
                )
                if schedule.available_slots > 0 and schedule.status == ScheduleStatus.FULL:
                    schedule.status = ScheduleStatus.OPEN
                await schedule.save()

        reservation.cancelled_at = datetime.now(UTC)
        reservation.updated_by = actor_id
        await reservation.save()
        return reservation

    def _build_code(self) -> str:
        return f"RES-{datetime.now(UTC).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
