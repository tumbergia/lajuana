"""006 — Backfill participant country_code / country_name (ISO 3166-1 alpha-2).

Idempotent: only updates documents missing country_code when the free-text
country can be resolved. Never invents codes. Logs unresolved values.
"""

from __future__ import annotations

import logging

from app.common.collections import Collections
from app.migrations.base import Migration
from app.services.analytics_country_normalizer import AnalyticsCountryNormalizer

logger = logging.getLogger(__name__)


class BackfillParticipantCountryCodesMigration(Migration):
    def __init__(self) -> None:
        super().__init__(
            version="006",
            name="backfill_participant_country_codes",
            description=(
                "Normalize ParticipantDocument.country into country_code / "
                "country_name without inventing ISO codes"
            ),
        )

    async def apply(self) -> None:
        from app.core.db import db

        if db.client is None:
            raise RuntimeError("Database not initialized")

        database = db.client.get_default_database()
        collection = database[Collections.PARTICIPANTS]
        normalizer = AnalyticsCountryNormalizer()

        cursor = collection.find(
            {
                "$or": [
                    {"country_code": {"$exists": False}},
                    {"country_code": None},
                    {"country_code": ""},
                ]
            },
            {"_id": 1, "country": 1},
        )

        updated = 0
        unresolved: list[str] = []
        async for doc in cursor:
            original = doc.get("country")
            result = normalizer.normalize(original)
            if not result.resolved:
                if original and original not in unresolved:
                    unresolved.append(str(original))
                continue
            await collection.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "country_code": result.country_code,
                        "country_name": result.country_name,
                    }
                },
            )
            updated += 1

        logger.info(
            "[migration 006] Updated %d participants; unresolved unique values: %d",
            updated,
            len(unresolved),
        )
        if unresolved:
            sample = unresolved[:25]
            logger.warning(
                "[migration 006] Unresolved country samples (%d): %s",
                len(unresolved),
                sample,
            )
