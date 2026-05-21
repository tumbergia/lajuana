from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_permissions
from app.common.enums import NotificationStatus, Permission
from app.documents import UserDocument
from app.documents.in_app_notification_document import InAppNotificationDocument
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.documents.notification_template_document import NotificationTemplateDocument
from app.schemas.notification import (
    InAppNotificationResponseSchema,
    NotificationOutboxResponseSchema,
    NotificationTemplateResponseSchema,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notificaciones"])
notification_service = NotificationService()


@router.get(
    "/templates",
    response_model=list[NotificationTemplateResponseSchema],
    operation_id="listNotificationTemplates",
)
async def list_templates(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_TEMPLATE_READ))],
) -> list[NotificationTemplateResponseSchema]:
    docs = await NotificationTemplateDocument.find_all().to_list()
    return [
        NotificationTemplateResponseSchema(
            id=str(d.id),
            template_key=d.template_key,
            channel=d.channel,
            language=d.language,
            subject=d.subject,
            body=d.body,
            variables_allowed=d.variables_allowed,
            is_active=d.is_active,
            version=d.version,
            created_at=d.created_at,
            updated_at=d.updated_at,
            deleted_at=d.deleted_at,
        )
        for d in docs
    ]


@router.post(
    "/reset/{reservation_id}",
    operation_id="resetReservationNotifications",
)
async def reset_reservation_notifications(
    reservation_id: str,
) -> dict:
    """Cancel all pending outbox entries for a reservation so the scheduler creates fresh ones."""
    from beanie import PydanticObjectId

    oid = PydanticObjectId(reservation_id)
    entries = await NotificationOutboxDocument.find(
        {
            "reservation_id": oid,
            "status": {"$ne": NotificationStatus.CANCELLED.value},
        }
    ).to_list()

    for entry in entries:
        entry.status = NotificationStatus.CANCELLED
        await entry.save()

    return {
        "cancelled": len(entries),
        "reservation_id": reservation_id,
        "message": f"Cancelled {len(entries)} notification(s). Scheduler will regenerate.",
    }


@router.post(
    "/test/{reservation_id}",
    response_model=NotificationOutboxResponseSchema,
    operation_id="testSendNotification",
)
async def test_send_notification(
    reservation_id: str,
) -> NotificationOutboxResponseSchema:
    """Manual test endpoint to trigger notification for a specific reservation."""
    from app.common.enums import NotificationChannel, NotificationEventType
    from app.documents import ReservationDocument

    reservation = await ReservationDocument.get(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    entry = await notification_service.enqueue(
        event_type=NotificationEventType.PRE_SERVICE_REMINDER,
        reservation_id=reservation_id,
        channel=NotificationChannel.EMAIL,
        recipient_type="customer",
        recipient_identifier=reservation.holder_email or "test@example.com",
        variables={
            "customer_name": reservation.holder_name or "Cliente",
            "reservation_code": reservation.code,
            "participants_count": str(reservation.participant_count),
        },
    )

    # Try to send immediately
    await notification_service.send_from_outbox(entry)

    return NotificationOutboxResponseSchema(
        id=str(entry.id),
        reservation_id=str(entry.reservation_id) if entry.reservation_id else None,
        event_type=entry.event_type,
        recipient_type=entry.recipient_type,
        recipient_identifier=entry.recipient_identifier,
        channel=entry.channel,
        template_key=entry.template_key,
        subject=entry.subject,
        status=entry.status,
        scheduled_for=entry.scheduled_for,
        sent_at=entry.sent_at,
        attempt_count=entry.attempt_count,
        last_error=entry.last_error,
        provider_message_id=entry.provider_message_id,
        version=entry.version,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        deleted_at=entry.deleted_at,
    )



@router.get(
    "/outbox/{notification_id}",
    response_model=NotificationOutboxResponseSchema,
    operation_id="getNotificationOutbox",
)
async def get_outbox(
    notification_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_READ))],
) -> NotificationOutboxResponseSchema:
    d = await NotificationOutboxDocument.get(notification_id)
    return NotificationOutboxResponseSchema(
        id=str(d.id),
        reservation_id=str(d.reservation_id) if d.reservation_id else None,
        event_type=d.event_type,
        recipient_type=d.recipient_type,
        recipient_identifier=d.recipient_identifier,
        channel=d.channel,
        template_key=d.template_key,
        subject=d.subject,
        status=d.status,
        scheduled_for=d.scheduled_for,
        sent_at=d.sent_at,
        attempt_count=d.attempt_count,
        last_error=d.last_error,
        provider_message_id=d.provider_message_id,
        version=d.version,
        created_at=d.created_at,
        updated_at=d.updated_at,
        deleted_at=d.deleted_at,
    )


@router.post(
    "/outbox/{notification_id}/retry",
    response_model=NotificationOutboxResponseSchema,
    operation_id="retryNotification",
)
async def retry_notification(
    notification_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_UPDATE))],
) -> NotificationOutboxResponseSchema:
    d = await notification_service.retry(notification_id)
    return NotificationOutboxResponseSchema(
        id=str(d.id),
        reservation_id=str(d.reservation_id) if d.reservation_id else None,
        event_type=d.event_type,
        recipient_type=d.recipient_type,
        recipient_identifier=d.recipient_identifier,
        channel=d.channel,
        template_key=d.template_key,
        subject=d.subject,
        status=d.status,
        scheduled_for=d.scheduled_for,
        sent_at=d.sent_at,
        attempt_count=d.attempt_count,
        last_error=d.last_error,
        provider_message_id=d.provider_message_id,
        version=d.version,
        created_at=d.created_at,
        updated_at=d.updated_at,
        deleted_at=d.deleted_at,
    )


@router.post(
    "/outbox/{notification_id}/cancel",
    response_model=NotificationOutboxResponseSchema,
    operation_id="cancelNotification",
)
async def cancel_notification(
    notification_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_UPDATE))],
) -> NotificationOutboxResponseSchema:
    d = await notification_service.cancel(notification_id)
    return NotificationOutboxResponseSchema(
        id=str(d.id),
        reservation_id=str(d.reservation_id) if d.reservation_id else None,
        event_type=d.event_type,
        recipient_type=d.recipient_type,
        recipient_identifier=d.recipient_identifier,
        channel=d.channel,
        template_key=d.template_key,
        subject=d.subject,
        status=d.status,
        scheduled_for=d.scheduled_for,
        sent_at=d.sent_at,
        attempt_count=d.attempt_count,
        last_error=d.last_error,
        provider_message_id=d.provider_message_id,
        version=d.version,
        created_at=d.created_at,
        updated_at=d.updated_at,
        deleted_at=d.deleted_at,
    )


@router.get(
    "/in-app",
    response_model=list[InAppNotificationResponseSchema],
    operation_id="listInAppNotifications",
)
async def list_in_app(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
) -> list[InAppNotificationResponseSchema]:
    docs = (
        await InAppNotificationDocument.find(
            InAppNotificationDocument.user_id == current_user.id
        )
        .sort("-created_at")
        .limit(50)
        .to_list()
    )
    return [
        InAppNotificationResponseSchema(
            id=str(d.id),
            user_id=str(d.user_id),
            reservation_id=str(d.reservation_id) if d.reservation_id else None,
            title=d.title,
            body=d.body,
            read=d.read,
            event_type=d.event_type,
            version=d.version,
            created_at=d.created_at,
            updated_at=d.updated_at,
            deleted_at=d.deleted_at,
        )
        for d in docs
    ]
