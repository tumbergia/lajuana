"""001 — Migrate staff role to guide.

Extracted from db.py init_db() where it was previously inline.
Idempotent: only affects documents with role == "staff".
"""

from __future__ import annotations

import logging

from app.common.collections import Collections
from app.migrations.base import Migration

logger = logging.getLogger(__name__)


class StaffToGuideMigration(Migration):
    def __init__(self) -> None:
        super().__init__(
            version="001",
            name="staff_to_guide",
            description="Migrate users with role 'staff' to 'guide'",
        )

    async def apply(self) -> None:
        from app.core.db import db

        if db.client is None:
            raise RuntimeError("Database not initialized")

        database = db.client.get_default_database()
        collection = database[Collections.USERS]

        result = await collection.update_many(
            {"role": "staff"},
            {"$set": {"role": "guide"}},
        )
        if result.modified_count:
            logger.info(
                "[migration 001] Migrated %d users from staff→guide",
                result.modified_count,
            )
        else:
            logger.info("[migration 001] No users with role 'staff' found")
