import asyncio

from app.core.logging import logger
from app.services.reservation_draft_service import ReservationDraftService

PRE_RESERVATION_EXPIRE_INTERVAL_SECONDS = 300  # 5 minutes


class ReservationDraftExpireWorker:
    def __init__(self) -> None:
        self._service = ReservationDraftService()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def run(self) -> None:
        self._running = True
        logger.info(
            "[pre-reservation-expire] Starting loop | interval=%ds",
            PRE_RESERVATION_EXPIRE_INTERVAL_SECONDS,
        )

        try:
            while self._running:
                try:
                    expired = await self._service.expire_reservation_drafts()
                    if expired:
                        logger.info(
                            "[pre-reservation-expire] Expired %d pre-reservation(s)",
                            expired,
                        )
                except Exception:
                    logger.exception("[pre-reservation-expire] Error in worker loop")

                await asyncio.sleep(PRE_RESERVATION_EXPIRE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("[pre-reservation-expire] Loop cancelled")
        finally:
            self._running = False
            logger.info("[pre-reservation-expire] Loop stopped")

    def stop(self) -> None:
        self._running = False
