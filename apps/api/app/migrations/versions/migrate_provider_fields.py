"""Migrate legacy provider documents to the expanded provider schema."""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from typing import Any

from pymongo.asynchronous.collection import AsyncCollection

from app.common.collections import Collections
from app.documents.provider_document import ProviderStatus, ProviderType
from app.migrations.base import Migration

logger = logging.getLogger(__name__)

_TYPE_MAP = {
    "lodging": ProviderType.LODGING.value,
    "food": ProviderType.FOOD.value,
    "mule_transport": ProviderType.EQUINE_TRANSPORT.value,
    "other": ProviderType.OTHER.value,
}


def _slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or "provider"


async def _unique_slug(collection: AsyncCollection, base_slug: str, doc_id: Any) -> str:
    slug = base_slug
    suffix = 2
    while await collection.find_one({"slug": slug, "_id": {"$ne": doc_id}}):
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


async def backfill_provider_slugs(collection: AsyncCollection) -> int:
    """Ensure every provider has a unique slug (required before unique index creation)."""
    modified = 0
    cursor = collection.find({"$or": [{"slug": {"$exists": False}}, {"slug": None}, {"slug": ""}]})
    async for doc in cursor:
        base_slug = _slugify(str(doc.get("name", "provider")))
        slug = await _unique_slug(collection, base_slug, doc["_id"])
        await collection.update_one({"_id": doc["_id"]}, {"$set": {"slug": slug}})
        modified += 1
    return modified


async def migrate_provider_fields_collection(collection: AsyncCollection) -> int:
    """Full provider schema migration using a raw Motor collection."""
    modified = 0
    cursor = collection.find({})

    async for doc in cursor:
        updates: dict[str, object] = {}
        unset: dict[str, str] = {}

        if "provider_type" in doc:
            raw_type = doc["provider_type"]
            updates["type"] = _TYPE_MAP.get(str(raw_type), ProviderType.OTHER.value)
            unset["provider_type"] = ""

        if "type" not in doc and "type" not in updates:
            updates["type"] = ProviderType.OTHER.value

        if "phone" in doc:
            updates["whatsapp_phone"] = doc["phone"]
            unset["phone"] = ""

        if "location" in doc:
            updates["location_label"] = doc["location"]
            unset["location"] = ""

        if "rate_notes" in doc:
            updates["tariff_notes"] = doc["rate_notes"]
            unset["rate_notes"] = ""

        if "status" not in doc:
            updates["status"] = (
                ProviderStatus.INACTIVE.value
                if doc.get("is_active") is False
                else ProviderStatus.ACTIVE.value
            )

        if "service_categories" not in doc:
            updates["service_categories"] = []

        if not doc.get("slug"):
            base_slug = _slugify(str(doc.get("name", "provider")))
            updates["slug"] = await _unique_slug(collection, base_slug, doc["_id"])

        if updates or unset:
            operation: dict[str, object] = {}
            if updates:
                operation["$set"] = updates
            if unset:
                operation["$unset"] = unset
            await collection.update_one({"_id": doc["_id"]}, operation)
            modified += 1

    return modified


async def migrate_provider_fields() -> int:
    from app.core.db import db

    if db.client is None:
        raise RuntimeError("Database not initialized")

    database = db.client.get_default_database()
    return await migrate_provider_fields_collection(database[Collections.PROVIDERS])


async def remove_provider_ids_from_reservations() -> int:
    from app.common.collections import Collections
    from app.core.db import db

    if db.client is None:
        raise RuntimeError("Database not initialized")

    collection = db.client.get_default_database()[Collections.RESERVATIONS]
    result = await collection.update_many(
        {"provider_ids": {"$exists": True}},
        {"$unset": {"provider_ids": ""}},
    )
    return result.modified_count


class MigrateProviderFieldsMigration(Migration):
    def __init__(self) -> None:
        super().__init__(
            version="004",
            name="migrate_provider_fields",
            description="Rename provider fields and backfill slug/status defaults",
        )

    async def apply(self) -> None:
        from app.core.db import db

        if db.client is None:
            raise RuntimeError("Database not initialized")

        database = db.client.get_default_database()
        provider_count = await migrate_provider_fields_collection(database[Collections.PROVIDERS])
        reservation_count = await remove_provider_ids_from_reservations()
        logger.info(
            "[migration 004] Migrated %d providers; cleaned provider_ids on %d reservations",
            provider_count,
            reservation_count,
        )


async def run_migration() -> None:
    from app.core.db import init_db

    await init_db()
    provider_count = await migrate_provider_fields()
    reservation_count = await remove_provider_ids_from_reservations()
    print(f"Migrated {provider_count} providers.")
    print(f"Removed provider_ids from {reservation_count} reservations.")


if __name__ == "__main__":
    asyncio.run(run_migration())
