"""Servicio de negocio para el agregado Reservation."""

import secrets
from datetime import UTC, date, datetime

from beanie import PydanticObjectId
from beanie.exceptions import CollectionWasNotInitialized
from pymongo.errors import DuplicateKeyError

from app.common.enums import (
    Channel,
    ParticipantFormStatus,
    PaymentStatus,
    ReservationStatus,
    ScheduleStatus,
    UserRole,
)
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents import (
    ExperienceDocument,
    ParticipantDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
    ScheduleDocument,
)
from app.services.config_service import ConfigService
from app.services.notification_service import NotificationService
from app.services.participant_form_link_service import ParticipantFormLinkService

ACTIVE_RESERVATION_STATUSES = {
    ReservationStatus.QUOTED,
    ReservationStatus.PRE_RESERVED,
    ReservationStatus.PENDING_PAYMENT,
    ReservationStatus.PAYMENT_RECEIVED,
    ReservationStatus.CONFIRMED,
}

ALLOWED_RESERVATION_TRANSITIONS = {
    ReservationStatus.CONTACT: {ReservationStatus.QUOTED, ReservationStatus.CANCELLED},
    ReservationStatus.QUOTED: {
        ReservationStatus.PRE_RESERVED,
        ReservationStatus.PENDING_PAYMENT,
        ReservationStatus.CANCELLED,
    },
    ReservationStatus.PRE_RESERVED: {
        ReservationStatus.PENDING_PAYMENT,
        ReservationStatus.EXPIRED,
        ReservationStatus.CANCELLED,
    },
    ReservationStatus.PENDING_PAYMENT: {
        ReservationStatus.PAYMENT_RECEIVED,
        ReservationStatus.CANCELLED,
    },
    ReservationStatus.PAYMENT_RECEIVED: {ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED},
    ReservationStatus.CONFIRMED: {ReservationStatus.COMPLETED, ReservationStatus.CANCELLED},
    ReservationStatus.CANCELLED: set(),
    ReservationStatus.COMPLETED: set(),
    ReservationStatus.EXPIRED: set(),
}


def _today() -> date:
    return datetime.now(UTC).date()


class ReservationService:
    """Orquesta reglas críticas de confirmación/cancelación de reservas."""

    def __init__(self) -> None:
        self.config_service = ConfigService()
        self.notification_service = NotificationService()
        self.form_link_service = ParticipantFormLinkService()

    @staticmethod
    def _is_blocking_status(status: ReservationStatus) -> bool:
        return status in ACTIVE_RESERVATION_STATUSES

    @staticmethod
    def _compute_schedule_status(*, is_active: bool, available_slots: int) -> ScheduleStatus:
        if not is_active:
            return ScheduleStatus.CLOSED
        if available_slots == 0:
            return ScheduleStatus.FULL
        return ScheduleStatus.OPEN

    @staticmethod
    async def _save_schedule_status(schedule: ScheduleDocument) -> None:
        """Save schedule status, avoiding Beanie datetime.time encoding issue.

        Uses motor collection update_one when available (production), falls back
        to Beanie .save() for unit tests where Beanie is not initialized.
        """
        try:
            collection = ScheduleDocument.get_motor_collection()
            await collection.update_one(
                {"_id": schedule.id},
                {"$set": {"status": schedule.status.value}},
            )
        except CollectionWasNotInitialized:
            await schedule.save()

    async def _sync_day_lock_fields(self, reservation: ReservationDocument) -> None:
        requested_date = reservation.requested_date

        reservation.blocks_day = bool(requested_date) and self._is_blocking_status(
            reservation.status
        )
        reservation.availability_lock_key = (
            requested_date.isoformat() if reservation.blocks_day and requested_date else None
        )

    async def list_active_reservations_for_date(
        self,
        requested_date: date,
        exclude_reservation_id: str | None = None,
    ) -> list[ReservationDocument]:
        status_values = [s.value for s in ACTIVE_RESERVATION_STATUSES]
        query = {
            "requested_date": requested_date,
            "status": {"$in": status_values},
        }
        if exclude_reservation_id is not None:
            query["_id"] = {"$ne": PydanticObjectId(exclude_reservation_id)}
        return await ReservationDocument.find(query).to_list()

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
        code = data.pop("code", None)
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
                    channel = (
                        Channel(data.get("channel")) if data.get("channel") is not None else None
                    )
                except ValueError:
                    channel = None
                status = (
                    ReservationStatus.QUOTED
                    if channel == Channel.WHATSAPP
                    else ReservationStatus.CONTACT
                )
            else:
                status = ReservationStatus(raw_status)

        if requested_date is not None and self._is_blocking_status(status):
            await self.ensure_date_available(requested_date)

        doc = ReservationDocument(
            **data,
            code=code or self._build_code(),
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

        if status in (ReservationStatus.CONTACT, ReservationStatus.QUOTED):
            try:
                await self.notification_service.enqueue_reservation_created(doc)
            except Exception:
                pass

        return doc

    async def list(self, actor_role: UserRole) -> list[ReservationDocument]:
        if actor_role == UserRole.GUIDE:
            return await ReservationDocument.find(
                {"status": ReservationStatus.CONFIRMED}
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
        """Busca una reserva por su ObjectId (24 caracteres)
        o usando coincidencia parcial del código."""
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
            reservation.payment_status != PaymentStatus.VERIFIED
            or not reservation.payment_proof_ids
        ):
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_PAYMENT_NOT_VERIFIED,
                message="No se puede confirmar sin pago verificado.",
            )

        await self.ensure_date_available(service_date, exclude_reservation_id=str(reservation.id))

        allowed = ALLOWED_RESERVATION_TRANSITIONS.get(reservation.status, set())
        if ReservationStatus.CONFIRMED not in allowed:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_INVALID_STATUS_TRANSITION,
                message="La transición de estado no es válida.",
                details={"from": reservation.status, "to": ReservationStatus.CONFIRMED},
            )

        capacity_source = await self._commit_schedule_capacity(
            schedule_id=str(schedule.id),
            participant_count=reservation.participant_count,
        )
        if capacity_source is None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_NO_AVAILABILITY,
                message="No fue posible comprometer cupos para confirmar la reserva.",
                details={"schedule_id": str(schedule.id)},
            )

        try:
            previous_status = reservation.status.value
            await self.transition_status(reservation, ReservationStatus.CONFIRMED)
            await self._sync_day_lock_fields(reservation)
            schedule = await ScheduleDocument.get(schedule.id)
            if schedule is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.SCHEDULE_NOT_FOUND,
                    message="Agenda no encontrada.",
                )
            schedule.status = self._compute_schedule_status(
                is_active=schedule.is_active,
                available_slots=schedule.available_slots,
            )

            reservation.confirmed_at = datetime.now(UTC)
            reservation.updated_by = actor_id
            await self._save_schedule_status(schedule)
            await reservation.save()

            try:
                await self.notification_service.enqueue_reservation_confirmed(reservation)
            except Exception:
                pass

            _, raw_token = await self.form_link_service.generate(
                reservation_id=reservation_id,
                expected_participants_count=reservation.participant_count,
                created_by=actor_id,
            )
            from app.core.config import settings

            reservation.form_url = (
                f"{settings.participant_form_base_url}/?token={raw_token}"
            )
            await reservation.save()

            # Send WhatsApp logistics message (deterministic, not chatbot)
            try:
                from app.notifications.reservation_whatsapp_notification_service import (
                    ReservationWhatsAppNotificationService,
                )

                whatsapp_notif = ReservationWhatsAppNotificationService()
                await whatsapp_notif.send_reservation_confirmed_logistics(
                    reservation=reservation,
                    actor_id=actor_id,
                )
            except Exception:
                logger.exception(
                    "[reservation=%s] Failed to send logistics WhatsApp",
                    reservation.id,
                )

            # Audit log — best-effort, non-critical
            try:
                log = ReservationAuditLogDocument(
                    reservation_id=reservation.id,
                    actor_user_id=actor_id,
                    actor_role=UserRole.ADMIN,
                    action="reservation.confirmed",
                    previous_status=previous_status,
                    new_status=ReservationStatus.CONFIRMED.value,
                    source="mobile_app",
                )
                await log.insert()
            except Exception:
                pass

            return reservation
        except Exception:
            await self._rollback_schedule_capacity(
                schedule_id=str(schedule.id),
                participant_count=reservation.participant_count,
                capacity_source=capacity_source,
            )
            schedule_after_rollback = await ScheduleDocument.get(schedule.id)
            if schedule_after_rollback is not None:
                schedule_after_rollback.status = self._compute_schedule_status(
                    is_active=schedule_after_rollback.is_active,
                    available_slots=schedule_after_rollback.available_slots,
                )
                await self._save_schedule_status(schedule_after_rollback)
            raise

    async def _commit_schedule_capacity(
        self,
        schedule_id: str,
        participant_count: int,
    ) -> str | None:
        collection = ScheduleDocument.get_motor_collection()
        schedule_object_id = PydanticObjectId(schedule_id)

        convert_result = await collection.update_one(
            {
                "_id": schedule_object_id,
                "held_slots": {"$gte": participant_count},
            },
            {
                "$inc": {
                    "held_slots": -participant_count,
                    "reserved_slots": participant_count,
                }
            },
        )
        if convert_result.modified_count > 0:
            return "held"

        reserve_result = await collection.update_one(
            {
                "_id": schedule_object_id,
                "available_slots": {"$gte": participant_count},
            },
            {
                "$inc": {
                    "available_slots": -participant_count,
                    "reserved_slots": participant_count,
                }
            },
        )
        if reserve_result.modified_count > 0:
            return "available"
        return None

    async def _rollback_schedule_capacity(
        self,
        *,
        schedule_id: str,
        participant_count: int,
        capacity_source: str,
    ) -> None:
        collection = ScheduleDocument.get_motor_collection()
        schedule_object_id = PydanticObjectId(schedule_id)
        if capacity_source == "held":
            rollback_result = await collection.update_one(
                {
                    "_id": schedule_object_id,
                    "reserved_slots": {"$gte": participant_count},
                },
                {
                    "$inc": {
                        "held_slots": participant_count,
                        "reserved_slots": -participant_count,
                    }
                },
            )
        else:
            rollback_result = await collection.update_one(
                {
                    "_id": schedule_object_id,
                    "reserved_slots": {"$gte": participant_count},
                },
                {
                    "$inc": {
                        "available_slots": participant_count,
                        "reserved_slots": -participant_count,
                    }
                },
            )

        if rollback_result.modified_count == 0:
            raise ApiError(
                status_code=500,
                code=ErrorCode.INTERNAL_ERROR,
                message="No fue posible revertir cupos tras fallo de confirmación.",
                details={
                    "schedule_id": schedule_id,
                    "participant_count": participant_count,
                    "capacity_source": capacity_source,
                },
            )

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

        if target_status == ReservationStatus.PAYMENT_RECEIVED:
            try:
                await self.notification_service.enqueue_payment_received(reservation)
            except Exception:
                pass

        if target_status == ReservationStatus.COMPLETED:
            try:
                await self.notification_service.enqueue_post_service(reservation)
            except Exception:
                pass

        return reservation

    async def cancel_reservation(
        self,
        reservation_id: str,
        actor_id: PydanticObjectId | None = None,
        notify_client: bool = True,
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

        # Send WhatsApp cancellation notification (deterministic, not chatbot)
        if notify_client:
            try:
                from app.notifications.reservation_whatsapp_notification_service import (
                    ReservationWhatsAppNotificationService,
                )

                whatsapp_notif = ReservationWhatsAppNotificationService()
                await whatsapp_notif.send_reservation_cancelled(
                    reservation=reservation,
                    actor_id=actor_id,
                )
            except Exception:
                logger.exception(
                    "[reservation=%s] Failed to send cancellation WhatsApp",
                    reservation.id,
                )

        return reservation

    async def validate_participant_forms_completed(
        self, reservation: ReservationDocument
    ) -> None:
        if reservation.participant_form_status != ParticipantFormStatus.COMPLETE:
            raise ApiError(
                status_code=409,
                code=ErrorCode.PARTICIPANT_FORM_NOT_COMPLETE,
                message="Todos los participantes deben completar el formulario antes de continuar.",
                details={
                    "expected": reservation.expected_participants_count,
                    "completed": reservation.participants_completed_count,
                },
            )

        participants = await ParticipantDocument.find(
            {"reservation_id": reservation.id},
        ).to_list()
        for p in participants:
            if not p.accepted_data_processing:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.PARTICIPANT_DATA_PROCESSING_REQUIRED,
                    message=(
                        f"El participante {p.first_name} {p.last_name} "
                        "no aceptó el tratamiento de datos."
                    ),
                )
            if p.accepted_risk_release is not True:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.PARTICIPANT_RISK_RELEASE_REQUIRED,
                    message=(
                        f"El participante {p.first_name} {p.last_name} "
                        "no aceptó la liberación de responsabilidad."
                    ),
                )

    def _build_code(self, prefix: str = "RES") -> str:
        return f"{prefix}-{datetime.now(UTC).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
