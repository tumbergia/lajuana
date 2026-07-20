import asyncio

from app.channels.whatsapp.integration_service import WhatsAppIntegrationService
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
        integration_service = WhatsAppIntegrationService()
        self._worker = ConversationTurnWorker(
            lock_service=ConversationLockService(),
            buffer_service=MessageBufferService(),
            outbound_service=WhatsAppOutboundService(integration_service=integration_service),
        )
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
