"""One-time: notify admins about existing PAYMENT_RECEIVED reservations."""

import asyncio

from app.common.enums import NotificationChannel, NotificationEventType, ReservationStatus, UserRole
from app.core.db import init_db
from app.documents import ReservationDocument, UserDocument
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.services.notification_service import NotificationService

ADMIN_EMAIL_TEMPLATE = (
    "Nuevo pago recibido y verificado para reserva {{reservation_code}}. "
    "Participantes: {{participants_count}}. "
    "Requiere confirmación."
)


async def notify_existing_payments() -> int:
    await init_db()
    service = NotificationService()
    count = 0

    reservations = await ReservationDocument.find(
        {"status": ReservationStatus.PAYMENT_RECEIVED, "payment_status": "verified"},
    ).to_list()

    for reservation in reservations:
        dedup_key = f"reservation_confirmed:{reservation.id}:internal:email"

        existing = await NotificationOutboxDocument.find_one(
            {"deduplication_key": dedup_key, "status": {"$ne": "cancelled"}}
        )
        if existing is not None:
            continue

        internal_users = await UserDocument.find(
            {"is_active": True, "role": UserRole.ADMIN},
        ).to_list()

        vars = {
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "participants_count": str(reservation.participant_count),
        }

        for user in internal_users:
            if user.email:
                await service.enqueue(
                    event_type=NotificationEventType.RESERVATION_CONFIRMED,
                    reservation_id=str(reservation.id),
                    channel=NotificationChannel.EMAIL,
                    recipient_type="internal",
                    recipient_identifier=user.email,
                    variables=vars,
                )

            await service.enqueue(
                event_type=NotificationEventType.RESERVATION_CONFIRMED,
                reservation_id=str(reservation.id),
                channel=NotificationChannel.IN_APP,
                recipient_type="internal",
                recipient_identifier=str(user.id),
                variables=vars,
            )

        count += 1
        print(f"  [{reservation.code}] Enqueued admin notifications")

    print(f"\nDone. Processed {count} reservations.")
    return count


if __name__ == "__main__":
    asyncio.run(notify_existing_payments())
