from datetime import date

from beanie import PydanticObjectId

from app.common.enums import Channel, ReservationStatus
from app.core.config import settings
from app.documents import ReservationDocument
from app.schemas.reservation import ReservationCreateSchema
from app.services.reservation_service import ReservationService


class BookingService:
    def __init__(
        self,
        reservation_service: ReservationService,
    ) -> None:
        self.reservation_service = reservation_service

    def _channel(self) -> Channel:
        try:
            return Channel(settings.chat_default_channel)
        except ValueError:
            return Channel.WHATSAPP

    async def date_is_available(
        self,
        *,
        requested_date: date,
    ) -> bool:
        return not await self.reservation_service.has_active_reservation_for_date(requested_date)

    async def create_pending_reservation(
        self,
        *,
        experience_id: str,
        participant_count: int,
        requested_date: date | None,
        holder_name: str | None = None,
        holder_email: str | None = None,
        holder_phone: str | None = None,
        actor_id: PydanticObjectId | None = None,
    ) -> ReservationDocument:
        payload = ReservationCreateSchema(
            experience_id=experience_id,
            requested_date=requested_date,
            participant_count=participant_count,
            channel=self._channel(),
            holder_name=holder_name,
            holder_email=holder_email,
            holder_phone=holder_phone,
        )
        reservation = await self.reservation_service.create(
            payload.model_dump(),
            actor_id=actor_id,
            initial_status=ReservationStatus.QUOTED,
        )
        reservation = await self.reservation_service.set_status(
            str(reservation.id),
            ReservationStatus.PENDING_PAYMENT,
            actor_id=actor_id,
        )
        return reservation
