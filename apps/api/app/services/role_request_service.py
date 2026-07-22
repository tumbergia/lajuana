"""Servicio de solicitudes de rol para usuarios sin rol asignado."""

from __future__ import annotations

from datetime import UTC, datetime

from app.common.enums import (
    NotificationChannel,
    NotificationEventType,
    NotificationStatus,
    RoleRequestStatus,
    UserRole,
)
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents import RoleRequestDocument, UserDocument
from app.schemas.auth import UserUpdateSchema
from app.schemas.role_request import (
    RoleRequestCreateSchema,
    RoleRequestDecisionSchema,
    RoleRequestResponseSchema,
)
from app.services.notification_service import NotificationService
from app.services.user_service import UserService

_ASSIGNABLE_ROLES = frozenset({UserRole.ADMIN, UserRole.GUIDE})

_ROLE_LABELS = {
    UserRole.ADMIN: "Administrador",
    UserRole.GUIDE: "Guía",
    UserRole.UNASSIGNED: "Sin rol",
}


class RoleRequestService:
    def __init__(
        self,
        user_service: UserService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self._user_service = user_service or UserService()
        self._notification_service = notification_service or NotificationService()

    async def create_self_request(
        self,
        actor: UserDocument,
        payload: RoleRequestCreateSchema,
    ) -> RoleRequestDocument:
        if actor.role != UserRole.UNASSIGNED:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ROLE_REQUEST_NOT_ALLOWED,
                message="Solo los usuarios sin rol pueden solicitar un rol.",
            )
        if payload.requested_role not in _ASSIGNABLE_ROLES:
            raise ApiError(
                status_code=400,
                code=ErrorCode.ROLE_REQUEST_INVALID_ROLE,
                message="Solo se puede solicitar rol de Guía o Administrador.",
            )

        existing = await RoleRequestDocument.find_one(
            {
                "user_id": actor.id,
                "status": RoleRequestStatus.PENDING,
                "deleted_at": None,
            }
        )
        if existing is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ROLE_REQUEST_ALREADY_PENDING,
                message="Ya tienes una solicitud de rol pendiente.",
            )

        doc = RoleRequestDocument(
            user_id=actor.id,
            requested_role=payload.requested_role,
            status=RoleRequestStatus.PENDING,
        )
        await doc.insert()

        role_label = _ROLE_LABELS.get(payload.requested_role, payload.requested_role.value)
        try:
            await self._notification_service.enqueue_admin_in_app(
                event_type=NotificationEventType.ROLE_REQUEST_CREATED,
                title="Solicitud de rol",
                body=f"{actor.full_name} solicita el rol de {role_label}.",
                actor_user_id=str(actor.id),
                dedup_suffix=str(doc.id),
            )
        except Exception:
            logger.exception(
                "[role_request] Failed to notify admins | request=%s",
                doc.id,
            )
        return doc

    async def get_my_request(self, actor: UserDocument) -> RoleRequestDocument | None:
        return (
            await RoleRequestDocument.find(
                {
                    "user_id": actor.id,
                    "deleted_at": None,
                }
            )
            .sort([("created_at", -1)])
            .first_or_none()
        )

    async def list_requests(
        self,
        status: RoleRequestStatus | None = RoleRequestStatus.PENDING,
        limit: int = 200,
        skip: int = 0,
    ) -> list[RoleRequestDocument]:
        query: dict = {"deleted_at": None}
        if status is not None:
            query["status"] = status
        return (
            await RoleRequestDocument.find(query)
            .sort([("created_at", -1)])
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def count_requests(
        self,
        status: RoleRequestStatus | None = RoleRequestStatus.PENDING,
    ) -> int:
        query: dict = {"deleted_at": None}
        if status is not None:
            query["status"] = status
        return await RoleRequestDocument.find(query).count()

    async def decide(
        self,
        request_id: str,
        actor: UserDocument,
        payload: RoleRequestDecisionSchema,
    ) -> RoleRequestDocument:
        doc = await RoleRequestDocument.get(request_id)
        if doc is None or doc.deleted_at is not None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.ROLE_REQUEST_NOT_FOUND,
                message="Solicitud de rol no encontrada.",
            )
        if doc.status != RoleRequestStatus.PENDING:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ROLE_REQUEST_NOT_PENDING,
                message="La solicitud ya fue resuelta.",
            )

        requester = await UserDocument.get(doc.user_id)
        if requester is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.USER_NOT_FOUND,
                message="Usuario solicitante no encontrado.",
            )

        if payload.action == "approve":
            assigned = payload.assigned_role or doc.requested_role
            if assigned not in _ASSIGNABLE_ROLES:
                raise ApiError(
                    status_code=400,
                    code=ErrorCode.ROLE_REQUEST_INVALID_ROLE,
                    message="Solo se puede asignar rol de Guía o Administrador.",
                )
            await self._user_service.update_user(
                str(doc.user_id),
                UserUpdateSchema(role=assigned),
            )
            doc.status = RoleRequestStatus.APPROVED
            doc.decided_role = assigned
            decision_body = (
                f"Tu solicitud fue aprobada. Ahora tienes el rol de "
                f"{_ROLE_LABELS.get(assigned, assigned.value)}."
            )
        elif payload.action == "reject":
            doc.status = RoleRequestStatus.REJECTED
            doc.decided_role = None
            decision_body = "Tu solicitud de rol fue rechazada."
        else:
            raise ApiError(
                status_code=400,
                code=ErrorCode.ROLE_REQUEST_INVALID_ACTION,
                message="Acción inválida. Usa approve o reject.",
            )

        doc.decided_by = actor.id
        doc.decided_at = datetime.now(UTC)
        if payload.note is not None:
            doc.note = payload.note
        await doc.save()

        try:
            entry = await self._notification_service.enqueue(
                event_type=NotificationEventType.ROLE_REQUEST_DECIDED,
                reservation_id=None,
                channel=NotificationChannel.IN_APP,
                recipient_type="internal",
                recipient_identifier=str(doc.user_id),
                subject="Solicitud de rol resuelta",
                body=decision_body,
                skip_template=True,
                dedup_suffix=str(doc.id),
            )
            if getattr(entry, "status", None) == NotificationStatus.PENDING:
                await self._notification_service.send_from_outbox(entry)
        except Exception:
            logger.exception(
                "[role_request] Failed to notify requester | request=%s user=%s",
                doc.id,
                doc.user_id,
            )
        return doc

    async def to_response(self, doc: RoleRequestDocument) -> RoleRequestResponseSchema:
        user = await UserDocument.get(doc.user_id)
        return RoleRequestResponseSchema(
            id=str(doc.id),
            version=doc.version,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            deleted_at=doc.deleted_at,
            user_id=str(doc.user_id),
            user_email=user.email if user else "unknown@example.com",
            user_full_name=user.full_name if user else "Usuario eliminado",
            user_role=user.role if user else UserRole.UNASSIGNED,
            requested_role=doc.requested_role,
            status=doc.status,
            decided_role=doc.decided_role,
            decided_by=str(doc.decided_by) if doc.decided_by else None,
            decided_at=doc.decided_at,
            note=doc.note,
        )
