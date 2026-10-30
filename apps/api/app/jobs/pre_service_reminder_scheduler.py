import asyncio
from datetime import UTC, date, datetime, timedelta

from app.common.enums import (
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
    ReservationStatus,
)
from app.core.logging import logger
from app.documents import ReservationDocument
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.services.notification_service import NotificationService

PRE_SERVICE_REMINDER_INTERVAL_SECONDS = 60


class PreServiceReminderScheduler:
    def __init__(self, service: NotificationService) -> None:
        self._service = service
        self._running = False
        self._processed_today: set[str] = set()
        self._admin_summary_sent_for: date | None = None
        self._current_date: date = date.today()

    @property
    def is_running(self) -> bool:
        return self._running

    async def run(self) -> None:
        self._running = True
        logger.info(
            "[pre-service-reminder] Starting loop | interval=%ds",
            PRE_SERVICE_REMINDER_INTERVAL_SECONDS,
        )

        try:
            while self._running:
                try:
                    await self._schedule_reminders()
                    await self._schedule_admin_tomorrow_summary()
                except Exception:
                    logger.exception("[pre-service-reminder] Error in worker loop")

                await asyncio.sleep(PRE_SERVICE_REMINDER_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("[pre-service-reminder] Loop cancelled")
        finally:
            self._running = False
            logger.info("[pre-service-reminder] Loop stopped")

    async def _schedule_reminders(self) -> None:
        today = date.today()

        # Reset processed set when day changes
        if today != self._current_date:
            self._processed_today.clear()
            self._current_date = today
            self._admin_summary_sent_for = None

        tomorrow = today + timedelta(days=1)

        reservations = await ReservationDocument.find(
            {
                "status": {
                    "$in": [
                        ReservationStatus.CONFIRMED.value,
                        ReservationStatus.PAYMENT_RECEIVED.value,
                    ]
                },
                "requested_date": {"$gte": today, "$lte": tomorrow},
            }
        ).to_list()

        for reservation in reservations:
            if not reservation.holder_email:
                continue

            if str(reservation.id) in self._processed_today:
                continue

            days_until = (reservation.requested_date - today).days  # type: ignore[operator]

            if days_until == 1:
                await self._enqueue_reminder(reservation)

    async def _schedule_admin_tomorrow_summary(self) -> None:
        today = date.today()
        if self._admin_summary_sent_for == today:
            return

        # Send admin summary once after 08:00 UTC (best-effort daily digest).
        now = datetime.now(UTC)
        if now.hour < 8:
            return

        tomorrow = today + timedelta(days=1)
        reservations = await ReservationDocument.find(
            {
                "status": {
                    "$in": [
                        ReservationStatus.CONFIRMED.value,
                        ReservationStatus.PAYMENT_RECEIVED.value,
                    ]
                },
                "requested_date": tomorrow,
            }
        ).to_list()

        if not reservations:
            self._admin_summary_sent_for = today
            return

        lines = []
        for reservation in reservations[:20]:
            holder = reservation.holder_name or "Cliente"
            code = reservation.code or str(reservation.id)
            lines.append(f"• {code}|{reservation.id}: {holder} ({reservation.participant_count})")
        extra = len(reservations) - len(lines)
        if extra > 0:
            lines.append(f"… y {extra} más")

        await self._service.enqueue_admin_in_app(
            event_type=NotificationEventType.TOMORROW_SERVICES_SUMMARY,
            title=f"Reservas de mañana ({len(reservations)})",
            body="\n".join(lines),
            dedup_suffix=today.isoformat(),
        )
        self._admin_summary_sent_for = today
        logger.info(
            "[pre-service-reminder] Admin tomorrow summary sent | count=%d",
            len(reservations),
        )

    async def _enqueue_reminder(self, reservation: ReservationDocument) -> None:
        # Only cancel entries that are pending/scheduled/failed, never SENT.
        # This prevents email spam every 60s while still allowing regeneration
        # after the user runs POST /notifications/reset/{id} or resets the server.
        existing = await NotificationOutboxDocument.find(
            {
                "reservation_id": reservation.id,
                "event_type": NotificationEventType.PRE_SERVICE_REMINDER.value,
                "status": {
                    "$in": [
                        NotificationStatus.PENDING.value,
                        NotificationStatus.SCHEDULED.value,
                        NotificationStatus.FAILED.value,
                    ]
                },
            }
        ).to_list()
        for entry in existing:
            entry.status = NotificationStatus.CANCELLED
            await entry.save()
            logger.debug(
                "[pre-service-reminder] Cancelled stale outbox | reservation=%s | outbox=%s",
                reservation.code,
                str(entry.id),
            )

        today = date.today()
        scheduled_hour = 18
        scheduled_for = datetime.combine(
            today,
            datetime.min.time(),
        ).replace(hour=scheduled_hour, tzinfo=UTC)

        # If scheduled time has already passed, send immediately
        now = datetime.now(UTC)
        if now > scheduled_for:
            scheduled_for = now

        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "participants_count": str(reservation.participant_count),
            **await self._service.business_location_vars(),
        }

        entry = await self._service.enqueue(
            event_type=NotificationEventType.PRE_SERVICE_REMINDER,
            reservation_id=str(reservation.id),
            channel=NotificationChannel.EMAIL,
            recipient_type="customer",
            recipient_identifier=reservation.holder_email,
            variables=vars,
            scheduled_for=scheduled_for,
        )

        self._processed_today.add(str(reservation.id))

        logger.info(
            "[pre-service-reminder] Scheduled | reservation=%s | outbox=%s",
            reservation.code,
            str(entry.id),
        )

    def stop(self) -> None:
        self._running = False
