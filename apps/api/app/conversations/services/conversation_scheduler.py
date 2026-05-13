import asyncio

from app.conversations.services.conversation_turn_worker import (
    ConversationTurnWorker,
)
from app.core.config import settings
from app.core.logging import logger


class ConversationScheduler:
    def __init__(self) -> None:
        self._worker = ConversationTurnWorker()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def run(self) -> None:
        self._running = True
        logger.info("[scheduler] Starting loop | interval=%ds", settings.scheduler_loop_seconds)

        try:
            while self._running:
                try:
                    processed = await self._worker.process_due_buffers(limit=25)
                    if processed:
                        logger.info("[scheduler] Processed %d buffer(s)", processed)
                except Exception:
                    logger.exception("[scheduler] Error in worker loop")

                await asyncio.sleep(settings.scheduler_loop_seconds)
        except asyncio.CancelledError:
            logger.info("[scheduler] Loop cancelled")
        finally:
            self._running = False
            logger.info("[scheduler] Loop stopped")

    def stop(self) -> None:
        self._running = False
