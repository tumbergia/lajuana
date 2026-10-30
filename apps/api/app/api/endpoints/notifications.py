from datetime import UTC, datetime
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.api.deps import get_notification_service, require_permissions
from app.common.enums import NOTIFICATION_PREFERENCE_KEYS, NotificationStatus, Permission
from app.documents import UserDocument
from app.documents.in_app_notification_document import InAppNotificationDocument
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.documents.notification_template_document import NotificationTemplateDocument
from app.schemas.notification import (
    InAppClearResultSchema,
    InAppNotificationResponseSchema,
    InAppUnreadCountSchema,
    NotificationOutboxResponseSchema,
    NotificationPreferencesSchema,
    NotificationPreferencesUpdateSchema,
    NotificationTemplateResponseSchema,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notificaciones"])


def _to_in_app_schema(d: InAppNotificationDocument) -> InAppNotificationResponseSchema:
    return InAppNotificationResponseSchema(
        id=str(d.id),
        user_id=str(d.user_id),
        reservation_id=str(d.reservation_id) if d.reservation_id else None,
        title=d.title,
        body=d.body,
        read=d.read,
        event_type=d.event_type,
        contact_phone=d.contact_phone,
        version=d.version,
        created_at=d.created_at,
        updated_at=d.updated_at,
        deleted_at=d.deleted_at,
    )


def _to_outbox_schema(entry: NotificationOutboxDocument) -> NotificationOutboxResponseSchema:
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
    "/templates",
    response_model=list[NotificationTemplateResponseSchema],
    operation_id="listNotificationTemplates",
)
async def list_templates(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_TEMPLATE_READ))],
    response: Response,
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
) -> list[NotificationTemplateResponseSchema]:
    total = await NotificationTemplateDocument.find_all().count()
    response.headers["X-Total-Count"] = str(total)
    docs = await NotificationTemplateDocument.find_all().skip(skip).limit(limit).to_list()
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
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_UPDATE))],
) -> dict:
    """Cancel all pending outbox entries for a reservation so the scheduler creates fresh ones."""
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
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_UPDATE))],
    notification_service: NotificationService = Depends(get_notification_service),
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

    await notification_service.send_from_outbox(entry)
    return _to_outbox_schema(entry)


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
    if d is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return _to_outbox_schema(d)


@router.post(
    "/outbox/{notification_id}/retry",
    response_model=NotificationOutboxResponseSchema,
    operation_id="retryNotification",
)
async def retry_notification(
    notification_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_UPDATE))],
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationOutboxResponseSchema:
    d = await notification_service.retry(notification_id)
    return _to_outbox_schema(d)


@router.post(
    "/outbox/{notification_id}/cancel",
    response_model=NotificationOutboxResponseSchema,
    operation_id="cancelNotification",
)
async def cancel_notification(
    notification_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.NOTIFICATION_UPDATE))],
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationOutboxResponseSchema:
    d = await notification_service.cancel(notification_id)
    return _to_outbox_schema(d)


@router.get(
    "/in-app/unread-count",
    response_model=InAppUnreadCountSchema,
    operation_id="getInAppUnreadCount",
)
async def get_in_app_unread_count(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
) -> InAppUnreadCountSchema:
    count = await InAppNotificationDocument.find(
        {"user_id": current_user.id, "read": False, "deleted_at": None}
    ).count()
    return InAppUnreadCountSchema(unread_count=count)


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
    limit: int = Query(default=50, ge=1, le=100),
    before_id: str | None = Query(default=None),
    unread_only: bool = Query(default=False),
) -> list[InAppNotificationResponseSchema]:
    query: dict = {"user_id": current_user.id, "deleted_at": None}
    if unread_only:
        query["read"] = False
    if before_id:
        try:
            query["_id"] = {"$lt": PydanticObjectId(before_id)}
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid before_id") from exc

    docs = await InAppNotificationDocument.find(query).sort("-created_at").limit(limit).to_list()
    return [_to_in_app_schema(d) for d in docs]


@router.post(
    "/in-app/{notification_id}/read",
    response_model=InAppNotificationResponseSchema,
    operation_id="markInAppNotificationRead",
)
async def mark_in_app_read(
    notification_id: str,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
) -> InAppNotificationResponseSchema:
    doc = await InAppNotificationDocument.get(notification_id)
    if doc is None or doc.user_id != current_user.id or doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not doc.read:
        doc.read = True
        doc.read_at = datetime.now(UTC).isoformat()
        await doc.save()
    return _to_in_app_schema(doc)


@router.post(
    "/in-app/read-all",
    response_model=InAppUnreadCountSchema,
    operation_id="markAllInAppNotificationsRead",
)
async def mark_all_in_app_read(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
) -> InAppUnreadCountSchema:
    now = datetime.now(UTC).isoformat()
    result = await InAppNotificationDocument.find(
        {"user_id": current_user.id, "read": False, "deleted_at": None}
    ).update_many({"$set": {"read": True, "read_at": now}})
    # Beanie UpdateResult may expose modified_count
    modified = getattr(result, "modified_count", 0) or 0
    return InAppUnreadCountSchema(unread_count=0 if modified >= 0 else 0)


@router.delete(
    "/in-app/{notification_id}",
    response_model=InAppClearResultSchema,
    operation_id="deleteInAppNotification",
)
async def delete_in_app_notification(
    notification_id: str,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
) -> InAppClearResultSchema:
    doc = await InAppNotificationDocument.get(notification_id)
    if doc is None or doc.user_id != current_user.id or doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Notification not found")
    doc.deleted_at = datetime.now(UTC)
    await doc.save()
    return InAppClearResultSchema(cleared_count=1)


@router.delete(
    "/in-app",
    response_model=InAppClearResultSchema,
    operation_id="clearInAppNotifications",
)
async def clear_in_app_notifications(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
    read_only: bool = Query(
        default=False,
        description="If true, only soft-delete notifications that are already read.",
    ),
) -> InAppClearResultSchema:
    query: dict = {"user_id": current_user.id, "deleted_at": None}
    if read_only:
        query["read"] = True
    now = datetime.now(UTC)
    result = await InAppNotificationDocument.find(query).update_many({"$set": {"deleted_at": now}})
    cleared = getattr(result, "modified_count", 0) or 0
    return InAppClearResultSchema(cleared_count=cleared)


@router.get(
    "/preferences",
    response_model=NotificationPreferencesSchema,
    operation_id="getNotificationPreferences",
)
async def get_notification_preferences(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
) -> NotificationPreferencesSchema:
    return NotificationPreferencesSchema.from_user_prefs(current_user.notification_preferences)


@router.put(
    "/preferences",
    response_model=NotificationPreferencesSchema,
    operation_id="updateNotificationPreferences",
)
async def update_notification_preferences(
    body: NotificationPreferencesUpdateSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.NOTIFICATION_READ)),
    ],
) -> NotificationPreferencesSchema:
    allowed = set(NOTIFICATION_PREFERENCE_KEYS)
    merged = dict(current_user.notification_preferences or {})
    for key, enabled in body.preferences.items():
        if key in allowed:
            merged[key] = bool(enabled)
    current_user.notification_preferences = merged
    await current_user.save()
    return NotificationPreferencesSchema.from_user_prefs(merged)
