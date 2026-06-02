import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.conversations.services.conversation_scheduler import (
    ConversationScheduler,
)
from app.core.db import close_db, init_db
from app.migrations import run_migrations
from app.core.di import Container
from app.core.logging import logger, reconfigure_logger
from app.jobs.expire_reservation_drafts import ReservationDraftExpireWorker
from app.jobs.notification_outbox_worker import NotificationOutboxWorker
from app.jobs.pre_service_reminder_scheduler import PreServiceReminderScheduler
from app.jobs.whatsapp_media_worker import WhatsAppMediaWorker
from app.migrations.seed_notification_templates import seed_notification_templates

# Module-level references; actual init happens inside lifespan() after DI is ready
scheduler: ConversationScheduler | None = None
expire_worker: ReservationDraftExpireWorker | None = None
notif_outbox_worker: NotificationOutboxWorker | None = None
pre_service_scheduler: PreServiceReminderScheduler | None = None
media_worker = WhatsAppMediaWorker()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    reconfigure_logger()
    logger.info("Application startup")
    Container.init()
    logger.info("[lifespan] DI container initialized")
    await init_db()
    await run_migrations()

    try:
        seeded = await seed_notification_templates()
        logger.info("[lifespan] Seeded %s notification templates", seeded)
    except Exception:
        logger.warning("[lifespan] Failed to seed notification templates", exc_info=True)

    # ── Initialize workers with DI dependencies ──
    container = Container.get_instance()
    global scheduler, expire_worker, notif_outbox_worker, pre_service_scheduler

    scheduler = ConversationScheduler()
    expire_worker = ReservationDraftExpireWorker(
        service=container.reservation_draft_service,
    )
    notif_outbox_worker = NotificationOutboxWorker(
        service=container.notification_service,
    )
    pre_service_scheduler = PreServiceReminderScheduler(
        service=container.notification_service,
    )

    scheduler_task = asyncio.create_task(scheduler.run())
    logger.info("[lifespan] Scheduler started")

    expire_task = asyncio.create_task(expire_worker.run())
    logger.info("[lifespan] Pre-reservation expire worker started")

    # Process initial batch immediately on startup
    initial_batch_task = asyncio.create_task(notif_outbox_worker.process_initial_batch())
    logger.info("[lifespan] Notification outbox initial batch started")

    notif_outbox_task = asyncio.create_task(notif_outbox_worker.run())
    logger.info("[lifespan] Notification outbox worker started")

    pre_service_task = asyncio.create_task(pre_service_scheduler.run())
    logger.info("[lifespan] Pre-service reminder scheduler started")

    # Wait for initial batch to complete before accepting requests
    try:
        await asyncio.wait_for(initial_batch_task, timeout=60)
    except TimeoutError:
        logger.warning("[lifespan] Initial notification batch timed out")

    media_task = asyncio.create_task(media_worker.run())
    logger.info("[lifespan] WhatsApp media download worker started")

    yield

    scheduler.stop()
    expire_worker.stop()
    notif_outbox_worker.stop()
    pre_service_scheduler.stop()
    media_worker.stop()

    scheduler_task.cancel()
    expire_task.cancel()
    notif_outbox_task.cancel()
    pre_service_task.cancel()
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
        await notif_outbox_task
    except asyncio.CancelledError:
        pass

    try:
        await pre_service_task
    except asyncio.CancelledError:
        pass

    try:
        await media_task
    except asyncio.CancelledError:
        pass

    await close_db()
    logger.info("Application shutdown")
