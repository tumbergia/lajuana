import asyncio

from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.conversations.services.conversation_lock_service import (
    ConversationLockService,
)
from app.conversations.services.conversation_turn_worker import (
    ConversationTurnWorker,
)
from app.conversations.services.message_buffer_service import MessageBufferService
from app.core.config import settings
from app.core.logging import logger


class ConversationScheduler:
    def __init__(self) -> None:
        self._worker = ConversationTurnWorker(
            lock_service=ConversationLockService(),
            buffer_service=MessageBufferService(),
            outbound_service=WhatsAppOutboundService(),
        )
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def run(self) -> None:
        self._running = True
        logger.info("[scheduler] Starting loop | interval=%ds", settings.scheduler_loop_seconds)

        tick = 0
        try:
            while self._running:
                tick += 1
                try:
                    buffers = await self._worker._buffer_service.find_due_buffers(limit=25)
                    if buffers:
                        logger.info(
                            "[scheduler] Found %d due buffer(s) | iteration=%d",
                            len(buffers),
                            tick,
                        )
                        processed = await self._worker.process_due_buffers(limit=25)
                        if processed:
                            logger.info(
                                "[scheduler] Processed %d buffer(s) | iteration=%d", processed, tick
                            )
                    elif tick % 15 == 0:
                        logger.info(
                            "[scheduler] Heartbeat | iteration=%d | no due buffers",
                            tick,
                        )
                except Exception:
                    logger.exception("[scheduler] Error in worker loop | iteration=%d", tick)

                await asyncio.sleep(settings.scheduler_loop_seconds)
        except asyncio.CancelledError:
            logger.info("[scheduler] Loop cancelled | iteration=%d", tick)
        finally:
            self._running = False
            logger.info("[scheduler] Loop stopped | iteration=%d", tick)

    def stop(self) -> None:
        self._running = False
