import asyncio

from app.core.config import settings
from app.core.logging import logger
from app.services.notification_service import NotificationService


class NotificationOutboxWorker:
    def __init__(self) -> None:
        self._service = NotificationService()
        self._running = False
        self._poll_interval = settings.notification_outbox_poll_interval

    @property
    def is_running(self) -> bool:
        return self._running

    async def process_initial_batch(self, batch_size: int = 50) -> int:
        """Process a large batch immediately on startup."""
        logger.info("[notif-outbox] Processing initial startup batch")
        sent = await self._service.process_pending_batch(batch_size=batch_size)
        if sent:
            logger.info("[notif-outbox] Initial batch sent %d notification(s)", sent)
        return sent

    async def run(self) -> None:
        self._running = True
        logger.info(
            "[notif-outbox] Starting loop | interval=%ds",
            self._poll_interval,
        )

        try:
            while self._running:
                try:
                    sent = await self._service.process_pending_batch()
                    if sent:
                        logger.info("[notif-outbox] Sent %d notification(s)", sent)
                except Exception:
                    logger.exception("[notif-outbox] Error in worker loop")

                await asyncio.sleep(self._poll_interval)
        except asyncio.CancelledError:
            logger.info("[notif-outbox] Loop cancelled")
        finally:
            self._running = False
            logger.info("[notif-outbox] Loop stopped")

    def stop(self) -> None:
        self._running = False
