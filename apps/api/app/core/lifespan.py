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

scheduler = ConversationScheduler()
expire_worker = ReservationDraftExpireWorker()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    reconfigure_logger()
    logger.info("Application startup")
    await init_db()

    scheduler_task = asyncio.create_task(scheduler.run())
    logger.info("[lifespan] Scheduler started")

    expire_task = asyncio.create_task(expire_worker.run())
    logger.info("[lifespan] Pre-reservation expire worker started")

    yield

    scheduler.stop()
    expire_worker.stop()

    scheduler_task.cancel()
    expire_task.cancel()

    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

    try:
        await expire_task
    except asyncio.CancelledError:
        pass

    await close_db()
    logger.info("Application shutdown")
