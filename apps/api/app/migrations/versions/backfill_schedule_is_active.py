"""002 — Backfill is_active field on ScheduleDocument.

Idempotent: only updates documents missing is_active.
"""

from __future__ import annotations

import logging

from app.common.collections import Collections
from app.migrations.base import Migration

logger = logging.getLogger(__name__)


class BackfillScheduleIsActiveMigration(Migration):
    def __init__(self) -> None:
        super().__init__(
            version="002",
            name="backfill_schedule_is_active",
            description="Set is_active=True on Schedule documents missing the field",
        )

    async def apply(self) -> None:
        from app.core.db import db

        if db.client is None:
            raise RuntimeError("Database not initialized")

        database = db.client.get_default_database()
        collection = database[Collections.SCHEDULES]

        result = await collection.update_many(
            {"is_active": {"$exists": False}},
            {"$set": {"is_active": True}},
        )
        logger.info(
            "[migration 002] Backfilled is_active on %d schedules",
            result.modified_count,
        )
