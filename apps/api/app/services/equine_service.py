from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from beanie import PydanticObjectId

from datetime import date

from app.common.enums import EquineOperationalStatus, ReservationStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ReservationDocument,
    ServiceLogDocument,
    ServiceLogEventType,
)
from app.schemas.equine import EquineCreateSchema, EquineTimelineEntrySchema, EquineUpdateSchema


class EquineService:
    async def create(self, payload: EquineCreateSchema) -> EquineDocument:
        doc = EquineDocument(**payload.model_dump())
        await doc.insert()
        return doc

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
        # Por defecto excluir borrados lógicos.
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

    async def list_items(
        self,
        operational_status: EquineOperationalStatus | None = None,
        is_active: bool | None = None,
        is_available: bool | None = None,
        include_deleted: bool = False,
        limit: int = 200,
        skip: int = 0,
    ) -> list[EquineDocument]:
        """Retorna solo los campos del list item (usa el mismo query pero más liviano)."""
        return await self.list(
            operational_status=operational_status,
            is_active=is_active,
            is_available=is_available,
            include_deleted=include_deleted,
            limit=limit,
            skip=skip,
        )

    async def get(self, equine_id: str) -> EquineDocument:
        doc = await EquineDocument.get(equine_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EQUINE_NOT_FOUND,
                message="Equino no encontrado.",
            )
        return doc

    async def update(self, equine_id: str, payload: EquineUpdateSchema) -> EquineDocument:
        doc = await self.get(equine_id)
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(doc, field, value)
        await doc.save()
        return doc

    async def deactivate(self, equine_id: str) -> EquineDocument:
        doc = await self.get(equine_id)
        doc.is_active = False
        doc.is_available = False
        doc.operational_status = EquineOperationalStatus.RETIRED
        await doc.save()
        return doc

    async def soft_delete(self, equine_id: str) -> EquineDocument:
        """Borra lógicamente un equino estableciendo deleted_at y desactivándolo."""
        doc = await self.get(equine_id)
        doc.deleted_at = datetime.now(UTC)
        doc.is_active = False
        await doc.save()
        return doc

    async def restore(self, equine_id: str) -> EquineDocument:
        """Restaura un equino borrado lógicamente."""
        doc = await self.get(equine_id)
        doc.deleted_at = None
        await doc.save()
        return doc

    async def get_timeline(
        self,
        equine_id: str,
        limit: int = 50,
    ) -> list[EquineTimelineEntrySchema]:
        """Retorna el timeline del equino desde ServiceLogs."""
        # Validar que el equino existe primero.
        await self.get(equine_id)
        logs = await ServiceLogDocument.find(
            {"related_equine_id": PydanticObjectId(equine_id)},
        ).sort(-ServiceLogDocument.happened_at).limit(limit).to_list()

        entries: list[EquineTimelineEntrySchema] = []
        for log in logs:
            title = _timeline_title(log.event_type, log.checkpoint_name)
            entries.append(
                EquineTimelineEntrySchema(
                    id=str(log.id),
                    event_type=log.event_type.value,
                    happened_at=log.happened_at,
                    title=title,
                    reservation_id=str(log.reservation_id),
                    notes=log.notes,
                )
            )
        return entries

    async def list_available_for_reservation(
        self,
        reservation_id: str,
        limit: int = 200,
        skip: int = 0,
    ) -> list[tuple[EquineDocument, str | None]]:
        """Retorna TODOS los equinos con block_reason.

        block_reason is None → equino asignable a la reserva.
        block_reason is set → explica por qué NO puede asignarse.

        Reglas de exclusión:
        1. Inactivo (is_active=False)
        2. No disponible (is_available=False)
        3. Ya asignado a esta reserva
        4. Ya asignado a otra reserva en la misma fecha
        """
        # 1. Obtener la reserva objetivo para conocer su fecha
        reservation = await ReservationDocument.get(reservation_id)

        # 2. Encontrar equinos ya asignados a esta reserva
        my_assignments = await AssignmentDocument.find(
            {"reservation_id": PydanticObjectId(reservation_id)},
        ).to_list()
        my_assigned_equine_ids = {str(a.equine_id) for a in my_assignments}

        # 3. Encontrar equinos asignados a otras reservas en la misma fecha
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

        # 4. Cargar todos los equinos (con paginación)
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
