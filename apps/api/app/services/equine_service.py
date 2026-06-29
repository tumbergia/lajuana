from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.common.enums import EquineOperationalStatus, ReservationStatus
from app.common.labels import ErrorCode
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    EquineEventDocument,
    ReservationDocument,
    ServiceLogDocument,
    ServiceLogEventType,
)
from app.schemas.equine import EquineCreateSchema, EquineTimelineEntrySchema, EquineUpdateSchema
from app.services.base_service import BaseService


class EquineService(BaseService[EquineDocument, EquineCreateSchema, EquineUpdateSchema]):
    document_class = EquineDocument
    not_found_code = ErrorCode.EQUINE_NOT_FOUND
    not_found_message = "Equino no encontrado."
    sync_entity_type = "equine"

    # ── List/Count con filtros de dominio ──

    async def list(
        self,
        operational_status: EquineOperationalStatus | None = None,
        is_active: bool | None = None,
        is_available: bool | None = None,
        include_deleted: bool = False,
        limit: int = 200,
        skip: int = 0,
    ) -> list[EquineDocument]:
        query: dict[str, object] = {}
        if not include_deleted:
            query["deleted_at"] = None
        if operational_status is not None:
            query["operational_status"] = operational_status
        if is_active is not None:
            query["is_active"] = is_active
        if is_available is not None:
            query["is_available"] = is_available
        return await EquineDocument.find(query).skip(skip).limit(limit).to_list()

    async def count(
        self,
        operational_status: EquineOperationalStatus | None = None,
        is_active: bool | None = None,
        is_available: bool | None = None,
        include_deleted: bool = False,
    ) -> int:
        query: dict[str, object] = {}
        if not include_deleted:
            query["deleted_at"] = None
        if operational_status is not None:
            query["operational_status"] = operational_status
        if is_active is not None:
            query["is_active"] = is_active
        if is_available is not None:
            query["is_available"] = is_available
        return await EquineDocument.find(query).count()

    # ── Acciones de dominio ──

    async def deactivate(self, equine_id: str) -> EquineDocument:
        doc = await self.get(equine_id)
        doc.is_active = False
        doc.is_available = False
        doc.operational_status = EquineOperationalStatus.RETIRED
        await doc.save()
        return doc

    async def soft_delete(self, equine_id: str) -> EquineDocument:
        """Borra lógicamente un equino: deleted_at + desactivación."""
        doc = await self.get(equine_id)
        doc.deleted_at = datetime.now(UTC)
        doc.is_active = False
        await doc.save()
        return doc

    async def restore(self, equine_id: str) -> EquineDocument:
        """Restaura un equino: reactiva + limpia deleted_at."""
        doc = await self.get(equine_id)
        doc.deleted_at = None
        doc.is_active = True
        await doc.save()
        return doc

    async def get_timeline(
        self,
        equine_id: str,
        limit: int = 50,
    ) -> list[EquineTimelineEntrySchema]:
        """Retorna timeline unificado: ServiceLogs + EquineEvents."""
        await self.get(equine_id)
        equine_oid = PydanticObjectId(equine_id)

        logs, events = await asyncio.gather(
            ServiceLogDocument.find(
                {"related_equine_id": equine_oid, "deleted_at": None},
            )
            .sort([("happened_at", -1)])
            .limit(limit)
            .to_list(),
            EquineEventDocument.find(
                {"equine_id": equine_oid, "deleted_at": None},
            )
            .sort([("happened_at", -1)])
            .limit(limit)
            .to_list(),
        )

        entries: list[EquineTimelineEntrySchema] = []

        for log in logs:
            entries.append(
                EquineTimelineEntrySchema(
                    id=str(log.id),
                    source="service_log",
                    event_type=log.event_type.value,
                    happened_at=log.happened_at,
                    title=_timeline_title(log.event_type, log.checkpoint_name),
                    reservation_id=str(log.reservation_id),
                    participant_id=(
                        str(log.related_participant_id)
                        if log.related_participant_id
                        else None
                    ),
                    notes=log.notes,
                )
            )

        for event in events:
            entries.append(
                EquineTimelineEntrySchema(
                    id=str(event.id),
                    source="equine_event",
                    event_type=event.event_type.value,
                    happened_at=event.happened_at,
                    title=event.title,
                    reservation_id=(
                        str(event.reservation_id) if event.reservation_id else None
                    ),
                    assignment_id=(
                        str(event.assignment_id) if event.assignment_id else None
                    ),
                    participant_id=(
                        str(event.participant_id) if event.participant_id else None
                    ),
                    notes=event.description,
                    severity=event.severity,
                    affects_availability=event.affects_availability,
                )
            )

        entries.sort(key=lambda e: e.happened_at, reverse=True)
        return entries[:limit]

    async def list_available_for_reservation(
        self,
        reservation_id: str,
        limit: int = 200,
        skip: int = 0,
    ) -> list[tuple[EquineDocument, str | None]]:
        """Retorna TODOS los equinos con block_reason.

        block_reason is None → equino asignable a la reserva.
        block_reason is set → explica por qué NO puede asignarse.
        """
        reservation = await ReservationDocument.get(reservation_id)

        my_assignments = await AssignmentDocument.find(
            {"reservation_id": PydanticObjectId(reservation_id)},
        ).to_list()
        my_assigned_equine_ids = {str(a.equine_id) for a in my_assignments}

        same_date_equine_ids: set[str] = set()
        if reservation and reservation.requested_date:
            same_date_reservations = await ReservationDocument.find(
                {
                    "_id": {"$ne": reservation.id},
                    "requested_date": reservation.requested_date,
                    "status": {"$in": [s.value for s in ReservationStatus if s not in (
                        ReservationStatus.CANCELLED,
                        ReservationStatus.EXPIRED,
                    )]},
                },
            ).to_list()
            same_date_ids = [r.id for r in same_date_reservations]
            if same_date_ids:
                same_date_assignments = await AssignmentDocument.find(
                    {"reservation_id": {"$in": same_date_ids}},
                ).to_list()
                same_date_equine_ids = {str(a.equine_id) for a in same_date_assignments}

        all_equines = await EquineDocument.find({}).skip(skip).limit(limit).to_list()

        result: list[tuple[EquineDocument, str | None]] = []
        for equine in all_equines:
            reason: str | None = None
            eid_str = str(equine.id)

            if not equine.is_active:
                reason = "Equino inactivo"
            elif not equine.is_available:
                reason = "Equino no disponible"
            elif eid_str in my_assigned_equine_ids:
                reason = "Ya asignado a esta reserva"
            elif eid_str in same_date_equine_ids:
                reason = "Ya asignado a otra reserva en la misma fecha"
            elif equine.operational_status in (
                EquineOperationalStatus.RETIRED,
                EquineOperationalStatus.INJURED,
                EquineOperationalStatus.UNAVAILABLE,
            ):
                reason = f"Estado operativo: {equine.operational_status.value}"

            result.append((equine, reason))

        return result


def _timeline_title(event_type: ServiceLogEventType, checkpoint_name: str | None) -> str:
    """Deriva un título legible desde el tipo de evento ServiceLog."""
    if event_type == ServiceLogEventType.CHECKPOINT and checkpoint_name:
        return checkpoint_name
    titles = {
        ServiceLogEventType.ARRIVAL: "Llegada a la finca",
        ServiceLogEventType.DEPARTURE: "Salida de la finca",
        ServiceLogEventType.CHECKPOINT: "Punto de control",
        ServiceLogEventType.CLOSURE: "Cierre de servicio",
        ServiceLogEventType.INCIDENT: "Incidencia",
        ServiceLogEventType.NOTE: "Nota operativa",
    }
    return titles.get(event_type, event_type.value)
