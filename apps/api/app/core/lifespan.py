import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.conversations.services.conversation_scheduler import (
    ConversationScheduler,
)
from app.core.db import close_db, init_db
from app.core.logging import logger, reconfigure_logger
from app.jobs.expire_reservation_drafts import ReservationDraftExpireWorker
from app.jobs.whatsapp_media_worker import WhatsAppMediaWorker

scheduler = ConversationScheduler()
expire_worker = ReservationDraftExpireWorker()
media_worker = WhatsAppMediaWorker()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    reconfigure_logger()
    logger.info("Application startup")
    await init_db()

    scheduler_task = asyncio.create_task(scheduler.run())
    logger.info("[lifespan] Scheduler started")

    expire_task = asyncio.create_task(expire_worker.run())
    logger.info("[lifespan] Pre-reservation expire worker started")

    media_task = asyncio.create_task(media_worker.run())
    logger.info("[lifespan] WhatsApp media download worker started")

    yield

    scheduler.stop()
    expire_worker.stop()
    media_worker.stop()

    scheduler_task.cancel()
    expire_task.cancel()
    media_task.cancel()

    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

    try:
        await expire_task
    except asyncio.CancelledError:
        pass

    try:
        await media_task
    except asyncio.CancelledError:
        pass

    await close_db()
    logger.info("Application shutdown")
