"""Push-operation handler for offline in-app notification mutations.

Mobile enqueues ``notification_mutation`` ops (mark_read / mark_all_read /
delete / clear_inbox) into the shared sync outbox. This handler applies them
idempotently so retries after a successful direct API call still succeed.
"""

from datetime import UTC, datetime
from types import SimpleNamespace

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents.in_app_notification_document import InAppNotificationDocument
from app.schemas.sync import SyncPushOperationSchema


def _bulk_result(*, local_id: str, payload: dict) -> SimpleNamespace:
    """Stub document for bulk ops that SyncOperationExecutor can serialize."""
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=local_id,
        version=1,
        updated_at=now,
        model_dump=lambda mode="json": payload,
    )


class NotificationSyncHandler:
    """Handles push operations for ``notification_mutation``."""

    async def handle(
        self,
        *,
        entity: str,
        op_type: str,
        operation: SyncPushOperationSchema,
        current_user,
    ):
        if entity != "notification_mutation":
            return None

        if op_type == "mark_read":
            return await self._mark_read(operation, current_user)
        if op_type == "mark_all_read":
            return await self._mark_all_read(current_user, operation)
        if op_type == "delete":
            return await self._delete_one(operation, current_user)
        if op_type == "clear_inbox":
            return await self._clear_inbox(operation, current_user)

        raise ApiError(
            status_code=400,
            code=ErrorCode.SYNC_UNSUPPORTED_OPERATION,
            message="Operacion de sincronizacion no soportada.",
            details={"entity_type": entity, "operation_type": op_type},
        )

    async def _mark_read(self, operation: SyncPushOperationSchema, current_user):
        doc = await InAppNotificationDocument.get(operation.entity_local_id)
        if doc is None or doc.user_id != current_user.id:
            # Idempotent: desired state is "read" / gone from unread.
            return _bulk_result(
                local_id=operation.entity_local_id,
                payload={"id": operation.entity_local_id, "read": True},
            )
        if doc.deleted_at is not None:
            return doc
        if not doc.read:
            doc.read = True
            doc.read_at = datetime.now(UTC).isoformat()
            await doc.save()
        return doc

    async def _mark_all_read(self, current_user, operation: SyncPushOperationSchema):
        now = datetime.now(UTC).isoformat()
        result = await InAppNotificationDocument.find(
            {"user_id": current_user.id, "read": False, "deleted_at": None}
        ).update_many({"$set": {"read": True, "read_at": now}})
        modified = getattr(result, "modified_count", 0) or 0
        return _bulk_result(
            local_id=operation.entity_local_id,
            payload={"unread_count": 0, "modified_count": modified},
        )

    async def _delete_one(self, operation: SyncPushOperationSchema, current_user):
        doc = await InAppNotificationDocument.get(operation.entity_local_id)
        if doc is None or doc.user_id != current_user.id:
            return _bulk_result(
                local_id=operation.entity_local_id,
                payload={"id": operation.entity_local_id, "cleared_count": 0},
            )
        if doc.deleted_at is None:
            doc.deleted_at = datetime.now(UTC)
            await doc.save()
        return doc

    async def _clear_inbox(self, operation: SyncPushOperationSchema, current_user):
        read_only = bool(operation.payload.get("read_only", False))
        query: dict = {"user_id": current_user.id, "deleted_at": None}
        if read_only:
            query["read"] = True
        now = datetime.now(UTC)
        result = await InAppNotificationDocument.find(query).update_many(
            {"$set": {"deleted_at": now}}
        )
        cleared = getattr(result, "modified_count", 0) or 0
        return _bulk_result(
            local_id=operation.entity_local_id,
            payload={"cleared_count": cleared, "read_only": read_only},
        )
