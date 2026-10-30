"""007 — Align notification template uniqueness with (template_key, channel)."""

from __future__ import annotations

import logging

from app.common.collections import Collections
from app.migrations.base import Migration

logger = logging.getLogger(__name__)

COMPOUND_INDEX_NAME = "uq_notification_template_key_channel"


class FixNotificationTemplateNaturalKeyIndexMigration(Migration):
    def __init__(self) -> None:
        super().__init__(
            version="007",
            name="fix_notification_template_natural_key_index",
            description="Replace template_key uniqueness with compound (template_key, channel)",
        )

    async def apply(self) -> None:
        from app.core.db import (
            NOTIFICATION_TEMPLATE_COMPOUND_INDEX_KEYS,
            db,
            preflight_notification_template_natural_key,
        )

        if db.client is None:
            raise RuntimeError("Database not initialized")

        database = db.client.get_default_database()
        collection = database[Collections.NOTIFICATION_TEMPLATES]

        index_names_to_drop, removed_duplicates = await preflight_notification_template_natural_key(
            collection
        )

        await collection.create_index(
            NOTIFICATION_TEMPLATE_COMPOUND_INDEX_KEYS,
            unique=True,
            name=COMPOUND_INDEX_NAME,
        )

        logger.info(
            (
                "[migration 007] Dropped %d legacy notification template indexes; "
                "removed %d duplicates; ensured %s"
            ),
            len(index_names_to_drop),
            removed_duplicates,
            COMPOUND_INDEX_NAME,
        )
