"""One-time: cancel all pre-service reminder outbox entries so fresh ones are created."""

import asyncio

from app.common.enums import NotificationEventType, NotificationStatus
from app.core.db import init_db
from app.documents.notification_outbox_document import NotificationOutboxDocument


async def reset_pre_service_reminders() -> int:
    await init_db()
    entries = await NotificationOutboxDocument.find(
        {
            "event_type": NotificationEventType.PRE_SERVICE_REMINDER.value,
            "status": {"$ne": NotificationStatus.CANCELLED.value},
        }
    ).to_list()

    for entry in entries:
        entry.status = NotificationStatus.CANCELLED
        await entry.save()

    print(f"Cancelled {len(entries)} pre-service reminder(s).")
    return len(entries)


if __name__ == "__main__":
    asyncio.run(reset_pre_service_reminders())
