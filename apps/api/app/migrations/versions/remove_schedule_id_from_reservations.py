"""Remove schedule_id from reservation documents."""

import asyncio

from app.core.db import init_db
from app.documents.reservation_document import ReservationDocument


async def remove_schedule_id_from_reservations() -> int:
    await init_db()
    collection = ReservationDocument.get_motor_collection()
    result = await collection.update_many(
        {"schedule_id": {"$exists": True}},
        {"$unset": {"schedule_id": ""}},
    )
    return result.modified_count


if __name__ == "__main__":
    count = asyncio.run(remove_schedule_id_from_reservations())
    print(f"Removed schedule_id from {count} reservations.")
