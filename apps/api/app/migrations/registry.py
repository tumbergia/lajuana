"""Migration tracker — records applied migrations in MongoDB.

Uses raw motor collection (not Beanie) to avoid circular imports with
init_beanie, which is called before run_migrations() in the lifespan.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.core.db import db
from app.common.collections import Collections

logger = logging.getLogger(__name__)

COLLECTION = Collections.MIGRATION_TRACKER


async def _collection():
    """Lazy-access the motor collection via the global db client."""
    if db.client is None:
        raise RuntimeError("Database not initialized")
    database = db.client.get_default_database()
    return database[COLLECTION]


async def ensure_index() -> None:
    """Create unique index on version to prevent duplicates."""
    coll = await _collection()
    await coll.create_index("version", unique=True, name="uq_migration_version")


async def is_applied(version: str) -> bool:
    """Check if a migration version has been applied."""
    coll = await _collection()
    doc = await coll.find_one({"version": version})
    return doc is not None


async def mark_applied(
    version: str,
    name: str,
    checksum: str,
    execution_seconds: float,
) -> None:
    """Record a migration as applied."""
    coll = await _collection()
    try:
        await coll.insert_one({
            "version": version,
            "name": name,
            "checksum": checksum,
            "applied_at": datetime.now(UTC),
            "execution_seconds": round(execution_seconds, 3),
        })
    except Exception:
        logger.exception(
            "Failed to record migration %s_%s", version, name
        )


async def get_all_applied() -> list[dict]:
    """Return all applied migration records, ordered by version."""
    coll = await _collection()
    cursor = coll.find().sort("version", 1)
    return await cursor.to_list(length=None)
