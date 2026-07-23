#!/usr/bin/env python
"""Migration: add contract fields to existing AssignmentDocument records.

Run against QA before production:

    python -m app.scripts.migrations.add_assignment_contract_fields

Legacy documents lack: status, source, safety_flags, validation_warnings,
is_active, assigned_by_user_id, finalized_by_user_id, assigned_at, finalized_at,
replaced_by_assignment_id.

We keep existing priority and assigned_manually fields as deprecated.
"""

import asyncio
import os

os.environ.setdefault("APP_ENV", "production")

from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


async def main() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client.get_default_database()
    collection = db["assignments"]

    total = await collection.count_documents({})
    print(f"[migration] Found {total} assignment documents")

    # Phase 1: set defaults for all docs
    result = await collection.update_many(
        {},
        {
            "$set": {
                "status": "draft",
                "source": "manual_admin",
                "safety_flags": [],
                "validation_warnings": [],
                "is_active": True,
            },
        },
    )
    print(f"[migration] Phase 1: set defaults on {result.modified_count} documents")

    # Phase 2: copy created_at into assigned_at for docs where assigned_at is missing
    # but created_at exists (legacy docs were created at assignment time)
    result2 = await collection.update_many(
        {"assigned_at": None, "created_at": {"$ne": None}},
        [
            {"$set": {"assigned_at": "$created_at"}},
        ],
    )
    print(
        f"[migration] Phase 2: backfilled assigned_at from created_at for {result2.modified_count} documents"
    )

    print("[migration] Done — priority and assigned_manually kept as deprecated fields")


if __name__ == "__main__":
    asyncio.run(main())
