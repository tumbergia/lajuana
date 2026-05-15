from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from beanie import PydanticObjectId

from app.common.enums import ReservationStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument, ReservationDocument
from app.services.config_service import ConfigService
from app.services.reservation_service import ReservationService
from app.services.schedule_service import ScheduleService


class ReservationDraftService:
    def __init__(self) -> None:
        self.reservation_service = ReservationService()
        self.schedule_service = ScheduleService()
        self.config_service = ConfigService()

    async def create_reservation_draft(
        self,
        experience_id: str,
        schedule_id: str,
        participant_count: int,
        holder_phone: str,
        holder_name: str | None,
        requested_date: str,
        quote_snapshot: dict,
        conversation_id: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        # 1. Validate experience exists and is active
        experience = await ExperienceDocument.get(PydanticObjectId(experience_id))
        if experience is None or not getattr(experience, "is_active", True):
            raise ApiError(
                status_code=404,
                code=ErrorCode.EXPERIENCE_NOT_FOUND,
                message="Experiencia no encontrada.",
            )

        # 2. Validate schedule is open
        schedule = await self.schedule_service.get(schedule_id)
        if not schedule.is_active or schedule.status.value != "open":
            raise ApiError(
                status_code=409,
                code=ErrorCode.SCHEDULE_NOT_OPEN,
                message="La agenda no está disponible para pre-reservar.",
            )

        # 3. Validate minimum anticipation and convert date
        rules = await self.config_service.get_reservation_rules()
        requested = datetime.strptime(requested_date, "%Y-%m-%d").date()
        delta_days = (requested - datetime.now(UTC).date()).days
        if delta_days < rules.min_days_in_advance:
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_MIN_NOTICE_VIOLATION,
                message="La fecha no cumple la anticipación mínima.",
            )

        # 4. Validate available slots (must use live read since atomic hold covers race)
        if schedule.available_slots < participant_count:
            raise ApiError(
                status_code=409,
                code=ErrorCode.SCHEDULE_ALREADY_FULL,
                message="No hay suficientes cupos disponibles.",
            )

        # 5. Validate quote_snapshot
        if not quote_snapshot or not isinstance(quote_snapshot, dict):
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_QUOTE_SNAPSHOT_REQUIRED,
                message="quote_snapshot es obligatorio.",
            )

        # 6. Atomic hold
        hold_result = await self.schedule_service.hold_slots(schedule_id, participant_count)
        if hold_result is None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.SCHEDULE_HOLD_FAILED,
                message="No se pudieron reservar los cupos temporalmente. Intenta de nuevo.",
            )

        # 7. Generate code with PR- prefix
        code = self._build_reservation_draft_code()

        # 8. Compute TTL
        expire_at = datetime.now(UTC) + timedelta(minutes=rules.reservation_draft_ttl_minutes)

        # 9. Create reservation (requested_date as date object, not string)
        try:
            await self.reservation_service.create(
                payload={
                    "experience_id": experience_id,
                    "schedule_id": schedule_id,
                    "participant_count": participant_count,
                    "holder_phone": holder_phone,
                    "holder_name": holder_name,
                    "requested_date": requested,
                    "channel": "whatsapp",
                    "code": code,
                    "quote_snapshot": quote_snapshot,
                    "quote_trace_id": trace_id,
                    "pre_reserved_at": datetime.now(UTC),
                    "expire_at": expire_at,
                },
                initial_status=ReservationStatus.PRE_RESERVED,
            )
        except Exception:
            await self.schedule_service.release_held_slots(schedule_id, participant_count)
            raise

        return {
            "created": True,
            "code": code,
            "status": ReservationStatus.PRE_RESERVED.value,
            "expire_at": expire_at,
            "message": f"Pre-reserva {code} creada exitosamente.",
        }

    async def expire_reservation_drafts(self) -> int:
        expired = await ReservationDocument.find(
            {
                "status": ReservationStatus.PRE_RESERVED.value,
                "expire_at": {"$lt": datetime.now(UTC)},
            }
        ).to_list()

        count = 0
        for reservation in expired:
            await self.reservation_service.transition_status(reservation, ReservationStatus.EXPIRED)
            reservation.updated_at = datetime.now(UTC)
            await reservation.save()

            if reservation.schedule_id is not None:
                await self.schedule_service.release_held_slots(
                    str(reservation.schedule_id),
                    reservation.participant_count,
                )
            count += 1

        return count

    def _build_reservation_draft_code(self) -> str:
        return f"PR-{datetime.now(UTC).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
