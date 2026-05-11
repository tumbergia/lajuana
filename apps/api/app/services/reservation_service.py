"""Servicio de negocio para el agregado Reservation."""

import secrets
from datetime import UTC, date, datetime

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.common.enums import Channel, PaymentStatus, ReservationStatus, ScheduleStatus, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument, ReservationDocument, ScheduleDocument
from app.services.config_service import ConfigService

ACTIVE_RESERVATION_STATUSES = {
    ReservationStatus.QUOTED,
    ReservationStatus.PENDING_PAYMENT,
    ReservationStatus.PAYMENT_RECEIVED,
    ReservationStatus.CONFIRMED,
}

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

    @staticmethod
    def _is_blocking_status(status: ReservationStatus) -> bool:
        return status in ACTIVE_RESERVATION_STATUSES

    async def _sync_day_lock_fields(self, reservation: ReservationDocument) -> None:
        requested_date = reservation.requested_date
        if requested_date is None and reservation.schedule_id is not None:
            schedule = await ScheduleDocument.get(reservation.schedule_id)
            if schedule is not None:
                requested_date = schedule.date

        reservation.blocks_day = bool(requested_date) and self._is_blocking_status(reservation.status)
        reservation.availability_lock_key = (
            requested_date.isoformat() if reservation.blocks_day and requested_date else None
        )

    async def list_active_reservations_for_date(
        self,
        requested_date: date,
        exclude_reservation_id: str | None = None,
    ) -> list[ReservationDocument]:
        query = [
            ReservationDocument.requested_date == requested_date,
            ReservationDocument.status.in_(list(ACTIVE_RESERVATION_STATUSES)),
        ]
        if exclude_reservation_id is not None:
            query.append(ReservationDocument.id != exclude_reservation_id)
        return await ReservationDocument.find(*query).to_list()

    async def get_blocking_reservation_for_date(
        self,
        requested_date: date,
        exclude_reservation_id: str | None = None,
    ) -> ReservationDocument | None:
        reservations = await self.list_active_reservations_for_date(
            requested_date,
            exclude_reservation_id=exclude_reservation_id,
        )
        return reservations[0] if reservations else None

    async def check_availability(
        self,
        requested_date: date,
        exclude_reservation_id: str | None = None,
    ) -> dict:
        blocking_reservation = await self.get_blocking_reservation_for_date(
            requested_date,
            exclude_reservation_id=exclude_reservation_id,
        )
        if blocking_reservation is None:
            return {
                "available": True,
                "date": requested_date.isoformat(),
                "blocking_reservation_id": None,
                "reason": None,
            }
        return {
            "available": False,
            "date": requested_date.isoformat(),
            "blocking_reservation_id": str(blocking_reservation.id),
            "reason": "Ya existe una reserva activa para esta fecha.",
        }

    async def ensure_date_available(
        self,
        requested_date: date,
        exclude_reservation_id: str | None = None,
    ) -> None:
        availability = await self.check_availability(
            requested_date,
            exclude_reservation_id=exclude_reservation_id,
        )
        if not availability["available"]:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_NO_AVAILABILITY,
                message=availability["reason"] or "La fecha ya tiene una reserva activa.",
                details={
                    "date": availability["date"],
                    "blocking_reservation_id": availability["blocking_reservation_id"],
                },
            )

    async def create(
        self,
        payload: dict,
        actor_id: PydanticObjectId | None = None,
        initial_status: ReservationStatus | None = None,
    ) -> ReservationDocument:
        data = dict(payload)
        raw_status = data.pop("status", None)
        experience_id = data.get("experience_id")
        if experience_id is not None:
            try:
                experience = await ExperienceDocument.get(experience_id)
            except Exception:
                experience = None
            if experience is None or not getattr(experience, "is_active", True):
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.EXPERIENCE_NOT_FOUND,
                    message="Experiencia no encontrada.",
                )
        requested_date = data.get("requested_date")
        schedule_id = data.get("schedule_id")
        if requested_date is None and schedule_id is not None:
            schedule = await ScheduleDocument.get(schedule_id)
            if schedule is not None:
                requested_date = schedule.date
                data["requested_date"] = requested_date

        if initial_status is not None:
            status = initial_status
        else:
            if raw_status is None:
                try:
                    channel = Channel(data.get("channel")) if data.get("channel") is not None else None
                except ValueError:
                    channel = None
                status = ReservationStatus.QUOTED if channel == Channel.WHATSAPP else ReservationStatus.CONTACT
            else:
                status = ReservationStatus(raw_status)

        if requested_date is not None and self._is_blocking_status(status):
            await self.ensure_date_available(requested_date)

        doc = ReservationDocument(
            **data,
            code=self._build_code(),
            status=status,
            created_by=actor_id,
            updated_by=actor_id,
        )
        await self._sync_day_lock_fields(doc)
        try:
            await doc.insert()
        except DuplicateKeyError as exc:
            details = exc.details if isinstance(exc.details, dict) else {}
            key_pattern = details.get("keyPattern", {})
            if "availability_lock_key" in key_pattern or "availability_lock_key" in str(exc):
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.RESERVATION_NO_AVAILABILITY,
                    message="Ya existe una reserva activa para esta fecha.",
                    details={"date": requested_date.isoformat() if requested_date else None},
                ) from exc
            raise ApiError(
                status_code=409,
                code=ErrorCode.CONFLICT,
                message="Existe un conflicto al guardar la reserva.",
                details={"collection": "reservations"},
            ) from exc
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

    async def has_active_reservation_for_schedule(
        self,
        schedule_id: str,
        exclude_reservation_id: str | None = None,
    ) -> bool:
        schedule = await ScheduleDocument.get(schedule_id)
        if schedule is None:
            return False
        return await self.has_active_reservation_for_date(
            schedule.date,
            exclude_reservation_id=exclude_reservation_id,
        )

    async def has_active_reservation_for_date(
        self,
        requested_date: date,
        exclude_reservation_id: str | None = None,
    ) -> bool:
        reservations = await self.list_active_reservations_for_date(
            requested_date,
            exclude_reservation_id=exclude_reservation_id,
        )
        return len(reservations) > 0

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

        if await self.has_active_reservation_for_schedule(
            str(schedule.id),
            exclude_reservation_id=str(reservation.id),
        ):
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_NO_AVAILABILITY,
                message="La fecha ya tiene una reserva activa.",
                details={"schedule_id": str(schedule.id)},
            )

        await self.transition_status(reservation, ReservationStatus.CONFIRMED)
        await self._sync_day_lock_fields(reservation)
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
        await self._sync_day_lock_fields(reservation)
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
        await self._sync_day_lock_fields(reservation)

        if previous_status == ReservationStatus.CONFIRMED and reservation.schedule_id:
            schedule = await ScheduleDocument.get(reservation.schedule_id)
            if schedule is not None:
                if not await self.has_active_reservation_for_schedule(str(schedule.id)):
                    schedule.status = ScheduleStatus.OPEN
                await schedule.save()

        reservation.cancelled_at = datetime.now(UTC)
        reservation.updated_by = actor_id
        await reservation.save()
        return reservation

    def _build_code(self) -> str:
        return f"RES-{datetime.now(UTC).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
