"""Timeline unificado de bitácora para reservas."""

from __future__ import annotations

import asyncio
from datetime import datetime

from beanie import PydanticObjectId

from app.common.enums import UserRole
from app.documents import (
    ParticipantDocument,
    PaymentProofDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
    ServiceLogDocument,
    ServiceLogEventType,
    UserDocument,
)
from app.schemas.reservation_timeline import ReservationTimelineEntrySchema
from app.schemas.service_log import ServiceLogPhotoSchema

AUDIT_ACTIONS_IN_TIMELINE = frozenset(
    {
        "reservation.created",
        "reservation.confirmed",
        "payment_proof.registered",
        "payment_proof.approved",
        "payment_proof.rejected",
        "payment_proof.unverified",
        "payment_proof.unrejected",
        "participant.registered",
        "notification.payment_approved_form_sent",
        "notification.reservation_confirmed_logistics_sent",
        "notification.participant_form_resent",
    }
)

AUDIT_ACTION_TITLES: dict[str, str] = {
    "reservation.created": "Reserva creada",
    "reservation.confirmed": "Reserva confirmada",
    "payment_proof.registered": "Comprobante registrado",
    "payment_proof.approved": "Pago aprobado",
    "payment_proof.rejected": "Pago rechazado",
    "payment_proof.unverified": "Verificación revertida",
    "payment_proof.unrejected": "Rechazo revertido",
    "participant.registered": "Participante registrado",
    "notification.payment_approved_form_sent": "Formulario enviado tras pago",
    "notification.reservation_confirmed_logistics_sent": "Logística confirmada enviada",
    "notification.participant_form_resent": "Formulario reenviado",
}

SERVICE_LOG_TITLES: dict[ServiceLogEventType, str] = {
    ServiceLogEventType.ARRIVAL: "Inicio del servicio",
    ServiceLogEventType.DEPARTURE: "Salida de la finca",
    ServiceLogEventType.CHECKPOINT: "Punto de control",
    ServiceLogEventType.CLOSURE: "Cierre de servicio",
    ServiceLogEventType.INCIDENT: "Incidencia",
    ServiceLogEventType.NOTE: "Nota manual",
}


def _service_log_title(log: ServiceLogDocument) -> str:
    if log.event_type == ServiceLogEventType.CHECKPOINT and log.checkpoint_name:
        return log.checkpoint_name
    return SERVICE_LOG_TITLES.get(log.event_type, log.event_type.value)


def _dedupe_key(kind: str, happened_at: datetime) -> tuple[str, datetime]:
    bucket = happened_at.replace(second=0, microsecond=0)
    base_kind = kind.split(":", 1)[0]
    return base_kind, bucket


def _photo_schemas(log: ServiceLogDocument) -> tuple[list[ServiceLogPhotoSchema], int]:
    photos = getattr(log, "photos", None) or []
    total = len(photos)
    mapped = [
        ServiceLogPhotoSchema(
            index=index,
            storage_key=photo.storage_key,
            filename=photo.filename,
            content_type=photo.content_type,
            size_bytes=photo.size_bytes,
        )
        for index, photo in enumerate(photos)
    ]
    return mapped, total


class ReservationTimelineService:
    async def get_timeline(
        self,
        reservation_id: str,
        *,
        actor_role: UserRole,
        limit: int = 100,
    ) -> list[ReservationTimelineEntrySchema]:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            from app.common.labels import ErrorCode
            from app.core.errors import ApiError

            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        reservation_oid = reservation.id
        logs, audits, participants, payment_proofs = await asyncio.gather(
            ServiceLogDocument.find(
                {"reservation_id": reservation_oid, "deleted_at": None},
            )
            .sort([("happened_at", -1)])
            .limit(limit)
            .to_list(),
            ReservationAuditLogDocument.find(
                {"reservation_id": reservation_oid, "deleted_at": None},
            )
            .sort([("created_at", -1)])
            .limit(limit)
            .to_list(),
            ParticipantDocument.find(
                {"reservation_id": reservation_oid, "deleted_at": None},
            ).to_list(),
            PaymentProofDocument.find(
                {"reservation_id": reservation_oid, "deleted_at": None},
            )
            .sort([("created_at", 1)])
            .to_list(),
        )

        actor_ids = {
            log.actor_user_id
            for log in audits
            if log.actor_user_id is not None
        }
        user_names: dict[str, str] = {}
        if actor_ids:
            users = await UserDocument.find(
                {"_id": {"$in": list(actor_ids)}},
            ).to_list()
            user_names = {str(u.id): u.full_name for u in users}

        is_admin = actor_role == UserRole.ADMIN
        entries: list[ReservationTimelineEntrySchema] = []
        seen_keys: set[tuple[str, datetime]] = set()

        def _add(entry: ReservationTimelineEntrySchema) -> None:
            key = _dedupe_key(entry.kind, entry.happened_at)
            if key in seen_keys:
                return
            seen_keys.add(key)
            entries.append(entry)

        for log in logs:
            kind = log.event_type.value
            is_note = log.event_type == ServiceLogEventType.NOTE
            photo_preview, photos_total = _photo_schemas(log)
            _add(
                ReservationTimelineEntrySchema(
                    id=f"service_log:{log.id}",
                    source="service_log",
                    kind=kind,
                    happened_at=log.happened_at,
                    title=_service_log_title(log),
                    description=log.notes,
                    editable=is_note,
                    deletable=is_note or is_admin,
                    related_participant_id=(
                        str(log.related_participant_id)
                        if log.related_participant_id
                        else None
                    ),
                    service_log_id=str(log.id),
                    photos=photo_preview,
                    photos_total=photos_total,
                )
            )

        for audit in audits:
            if audit.action not in AUDIT_ACTIONS_IN_TIMELINE:
                continue
            actor_id = str(audit.actor_user_id) if audit.actor_user_id else None
            description = audit.reason
            related_participant_id = None
            if audit.action == "participant.registered" and audit.metadata is not None:
                meta = audit.metadata
                if hasattr(meta, "participant_id"):
                    related_participant_id = meta.participant_id
                    description = meta.participant_name
            _add(
                ReservationTimelineEntrySchema(
                    id=f"audit_log:{audit.id}",
                    source="audit_log",
                    kind=audit.action,
                    happened_at=audit.created_at,
                    title=AUDIT_ACTION_TITLES.get(audit.action, audit.action),
                    description=description,
                    actor_name=user_names.get(actor_id) if actor_id else None,
                    actor_role=audit.actor_role.value if audit.actor_role else None,
                    editable=False,
                    deletable=False,
                    related_participant_id=related_participant_id,
                )
            )

        if not any(e.kind == "reservation.created" for e in entries):
            _add(
                ReservationTimelineEntrySchema(
                    id=f"derived:reservation.created:{reservation.id}",
                    source="derived",
                    kind="reservation.created",
                    happened_at=reservation.created_at,
                    title="Reserva creada",
                    description=f"Código {reservation.code}",
                    editable=False,
                    deletable=False,
                )
            )

        if payment_proofs and not any(
            e.kind == "payment_proof.registered" for e in entries
        ):
            first_proof = payment_proofs[0]
            _add(
                ReservationTimelineEntrySchema(
                    id=f"derived:payment_proof.registered:{first_proof.id}",
                    source="derived",
                    kind="payment_proof.registered",
                    happened_at=first_proof.created_at,
                    title="Comprobante registrado",
                    description=first_proof.filename,
                    editable=False,
                    deletable=False,
                )
            )

        registered_participant_ids = {
            e.related_participant_id
            for e in entries
            if e.kind == "participant.registered" and e.related_participant_id
        }
        for participant in participants:
            if not participant.is_completed:
                continue
            pid = str(participant.id)
            if pid in registered_participant_ids:
                continue
            happened_at = participant.submitted_at or participant.updated_at
            kind = f"participant.registered:{pid}"
            if any(
                e.kind.startswith("participant.registered")
                and e.related_participant_id == pid
                for e in entries
            ):
                continue
            _add(
                ReservationTimelineEntrySchema(
                    id=f"derived:{kind}",
                    source="derived",
                    kind="participant.registered",
                    happened_at=happened_at,
                    title="Participante registrado",
                    description=f"{participant.first_name} {participant.last_name}".strip(),
                    related_participant_id=pid,
                    editable=False,
                    deletable=False,
                )
            )

        entries.sort(key=lambda e: e.happened_at, reverse=True)
        return entries[:limit]
