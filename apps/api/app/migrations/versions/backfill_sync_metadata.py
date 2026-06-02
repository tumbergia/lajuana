"""003 — Backfill sync_metadata on mutable collections.

Idempotent: only updates documents missing sync_metadata.created_at.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.common.collections import Collections
from app.migrations.base import Migration

logger = logging.getLogger(__name__)

MUTABLE_COLLECTIONS = (
    Collections.USERS,
    Collections.EXPERIENCES,
    Collections.SCHEDULES,
    Collections.RESERVATIONS,
    Collections.PARTICIPANTS,
    Collections.PAYMENT_PROOFS,
    Collections.EQUINES,
    Collections.SADDLES,
    Collections.ASSIGNMENTS,
    Collections.SERVICE_LOGS,
    Collections.PROVIDERS,
    Collections.POLICIES,
)


class BackfillSyncMetadataMigration(Migration):
    def __init__(self) -> None:
        super().__init__(
            version="003",
            name="backfill_sync_metadata",
            description="Backfill sync_metadata on documents missing it",
        )

    async def apply(self) -> None:
        from app.core.db import db

        if db.client is None:
            raise RuntimeError("Database not initialized")

        database = db.client.get_default_database()
        now = datetime.now(UTC)
        total = 0

        for coll_name in MUTABLE_COLLECTIONS:
            collection = database[coll_name]
            result = await collection.update_many(
                {"sync_metadata.created_at": {"$exists": False}},
                {
                    "$set": {
                        "sync_metadata.created_at": now,
                        "sync_metadata.updated_at": now,
                        "sync_metadata.sync_version": 1,
                    }
                },
            )
            if result.modified_count:
                logger.info(
                    "[migration 003] Backfilled sync_metadata on %d docs in %s",
                    result.modified_count,
                    coll_name,
                )
                total += result.modified_count

        logger.info(
            "[migration 003] Backfilled sync_metadata on %d total documents",
            total,
        )
