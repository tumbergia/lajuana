import asyncio

from app.core.logging import logger
from app.services.whatsapp_media_downloader import download_pending_media

MEDIA_DOWNLOAD_INTERVAL_SECONDS = 60


class WhatsAppMediaWorker:
    def __init__(self) -> None:
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    async def run(self) -> None:
        self._running = True
        logger.info(
            "[whatsapp-media] Starting loop | interval=%ds",
            MEDIA_DOWNLOAD_INTERVAL_SECONDS,
        )

        try:
            while self._running:
                try:
                    downloaded = await download_pending_media(limit=5)
                    if downloaded:
                        logger.info(
                            "[whatsapp-media] Downloaded %d pending file(s)",
                            len(downloaded),
                        )
                except Exception:
                    logger.exception("[whatsapp-media] Error in worker loop")

                await asyncio.sleep(MEDIA_DOWNLOAD_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("[whatsapp-media] Loop cancelled")
        finally:
            self._running = False
            logger.info("[whatsapp-media] Loop stopped")

    def stop(self) -> None:
        self._running = False
