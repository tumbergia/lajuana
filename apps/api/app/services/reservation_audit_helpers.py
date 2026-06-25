"""Best-effort writers for reservation audit log entries."""

from __future__ import annotations

from beanie import PydanticObjectId

from app.common.enums import UserRole
from app.core.logging import logger
from app.documents import ReservationAuditLogDocument, ReservationDocument
from app.documents.audit_metadata_models import ParticipantMetadata


async def write_reservation_audit_log(
    *,
    reservation: ReservationDocument,
    action: str,
    actor_user_id: PydanticObjectId | None = None,
    actor_role: UserRole | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
    reason: str | None = None,
    payment_proof_id: PydanticObjectId | None = None,
    metadata: ParticipantMetadata | None = None,
    source: str = "mobile_app",
) -> None:
    try:
        log = ReservationAuditLogDocument(
            reservation_id=reservation.id,
            payment_proof_id=payment_proof_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action=action,
            previous_status=previous_status or reservation.status.value,
            new_status=new_status or reservation.status.value,
            reason=reason,
            source=source,
            metadata=metadata,
        )
        await log.insert()
    except Exception as exc:
        logger.warning(
            "[audit] Failed to create audit log: %s | action=%s reservation=%s",
            exc,
            action,
            reservation.id,
        )
