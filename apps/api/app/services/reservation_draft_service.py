from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from beanie import PydanticObjectId

from app.common.constants import build_code
from app.common.enums import ReservationStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument, ReservationDocument
from app.services.config_service import ConfigService
from app.services.reservation_service import ReservationService


class ReservationDraftService:
    def __init__(
        self,
        reservation_service: ReservationService,
        config_service: ConfigService,
    ) -> None:
        self.reservation_service = reservation_service
        self.config_service = config_service

    async def create_reservation_draft(
        self,
        experience_id: str,
        participant_count: int,
        holder_phone: str,
        holder_name: str | None,
        requested_date: str,
        quote_snapshot: dict,
        conversation_id: str | None = None,
        trace_id: str | None = None,
        holder_email: str | None = None,
        holder_language: str = "es",
    ) -> dict:
        # 1. Validate experience exists and is active
        experience = await ExperienceDocument.get(PydanticObjectId(experience_id))
        if experience is None or not getattr(experience, "is_active", True):
            raise ApiError(
                status_code=404,
                code=ErrorCode.EXPERIENCE_NOT_FOUND,
                message="Experiencia no encontrada.",
            )

        # 2. Validate minimum anticipation and convert date
        rules = await self.config_service.get_reservation_rules()
        requested = datetime.strptime(requested_date, "%Y-%m-%d").date()
        delta_days = (requested - datetime.now(UTC).date()).days
        if delta_days < rules.min_days_in_advance:
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_MIN_NOTICE_VIOLATION,
                message="La fecha no cumple la anticipación mínima.",
            )

        # 3. Validate max participants
        if participant_count > 8:
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_INVALID_PARTICIPANT_COUNT,
                message="Máximo 8 personas por reserva.",
            )

        # 4. Validate no active reservation on the same date
        # If a pre-reservation already exists for this phone+experience+date,
        # return it instead of erroring (idempotent for duplicate submissions).
        existing = await ReservationDocument.find_one({
            "holder_phone": holder_phone,
            "experience_id": experience_id,
            "requested_date": requested,
            "status": ReservationStatus.PRE_RESERVED.value,
        })
        if existing:
            return {
                "created": True,
                "code": existing.code,
                "status": existing.status.value,
                "expire_at": existing.expire_at,
                "message": f"Pre-reserva {existing.code} ya existente, retornando datos actuales.",
            }
        await self.reservation_service.ensure_date_available(requested)

        # 5. Validate quote_snapshot
        if not quote_snapshot or not isinstance(quote_snapshot, dict):
            raise ApiError(
                status_code=400,
                code=ErrorCode.RESERVATION_QUOTE_SNAPSHOT_REQUIRED,
                message="quote_snapshot es obligatorio.",
            )

        # 6. Generate code with PR- prefix
        code = build_code("PR")

        # 7. Compute TTL
        expire_at = datetime.now(UTC) + timedelta(minutes=rules.reservation_draft_ttl_minutes)

        # 8. Create reservation
        quoted_total = None
        if quote_snapshot and isinstance(quote_snapshot, dict):
            raw_subtotal = quote_snapshot.get("subtotal")
            if raw_subtotal is not None:
                try:
                    quoted_total = Decimal(str(raw_subtotal))
                except Exception:
                    quoted_total = None

        payload = {
            "experience_id": experience_id,
            "participant_count": participant_count,
            "holder_phone": holder_phone,
            "holder_name": holder_name,
            "holder_email": holder_email,
            "holder_language": holder_language,
            "requested_date": requested,
            "channel": "whatsapp",
            "code": code,
            "quote_snapshot": quote_snapshot,
            "quote_trace_id": trace_id,
            "quoted_total_amount": quoted_total,
            "pre_reserved_at": datetime.now(UTC),
            "expire_at": expire_at,
        }

        await self.reservation_service.create(
            payload=payload,
            initial_status=ReservationStatus.PRE_RESERVED,
        )

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
            count += 1

        return count


