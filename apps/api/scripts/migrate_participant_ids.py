#!/usr/bin/env python3
"""One-shot migration: backfill participant_ids on ReservationDocuments.

Legacy ReservationDocuments may have empty/null participant_ids. This script
finds them, queries ParticipantDocuments by reservation_id, and sets
participant_ids = [p.id for p in participants].

Idempotent: skips documents that already have participant_ids populated.
Use --dry-run to preview without writing.

Usage:
    python scripts/migrate_participant_ids.py          # actual run
    python scripts/migrate_participant_ids.py --dry-run  # preview only
"""

import asyncio
import logging
import sys

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("migrate_participant_ids")

DRY_RUN = "--dry-run" in sys.argv


async def migrate() -> None:
    client: AsyncIOMotorClient | None = None
    try:
        mongo_uri = settings.mongo_uri
        db_name = settings.mongo_db_name
        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]

        reservations_collection = db["reservations"]
        participants_collection = db["participants"]

        total = 0
        fixed = 0
        skipped = 0

        cursor = reservations_collection.find(
            {
                "$or": [
                    {"participant_ids": {"$exists": False}},
                    {"participant_ids": None},
                    {"participant_ids": []},
                ]
            },
        )

        async for res in cursor:
            total += 1
            rid = res["_id"]
            participants = await participants_collection.find(
                {"reservation_id": rid},
            ).to_list(length=None)

            if not participants:
                logger.warning(
                    "Reservation %s has no participants at all — skipping",
                    rid,
                )
                skipped += 1
                continue

            p_ids = [p["_id"] for p in participants]

            if DRY_RUN:
                logger.info(
                    "[DRY-RUN] Reservation %s: would set participant_ids=%s "
                    "(found %d participants)",
                    rid,
                    p_ids,
                    len(p_ids),
                )
                fixed += 1
                continue

            await reservations_collection.update_one(
                {"_id": rid},
                {"$set": {"participant_ids": p_ids}},
            )
            fixed += 1
            logger.info(
                "Migrated reservation %s: set %d participant_ids",
                rid,
                len(p_ids),
            )

        mode = "DRY-RUN" if DRY_RUN else "RUN"
        logger.info(
            "[%s] Done. Processed %d reservations: %d fixed, %d skipped (no participants)",
            mode,
            total,
            fixed,
            skipped,
        )

    except Exception:
        logger.exception("Migration failed")
        sys.exit(1)
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
