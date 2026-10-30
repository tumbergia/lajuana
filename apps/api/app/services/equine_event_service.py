from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from beanie import PydanticObjectId

from app.common.enums import EquineOperationalStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    EquineEventDocument,
    EquineEventType,
    ReservationDocument,
)
from app.schemas.equine_event import (
    EquineEventCreateSchema,
    EquineEventListFilters,
    EquineEventUpdateSchema,
)
from app.services.base_service import BaseService

_AVAILABILITY_BLOCKING_TYPES = frozenset(
    {
        EquineEventType.INJURY,
        EquineEventType.TREATMENT,
        EquineEventType.REST,
        EquineEventType.AVAILABILITY_CHANGE,
    }
)

_DEFAULT_BLOCKING_STATUS: dict[EquineEventType, EquineOperationalStatus] = {
    EquineEventType.INJURY: EquineOperationalStatus.INJURED,
    EquineEventType.TREATMENT: EquineOperationalStatus.RESTRICTED,
    EquineEventType.REST: EquineOperationalStatus.RESTING,
    EquineEventType.AVAILABILITY_CHANGE: EquineOperationalStatus.UNAVAILABLE,
}


class EquineEventService(
    BaseService[EquineEventDocument, EquineEventCreateSchema, EquineEventUpdateSchema],
):
    document_class = EquineEventDocument
    not_found_code = ErrorCode.EQUINE_EVENT_NOT_FOUND
    not_found_message = "Evento de equino no encontrado."

    _FUTURE_TOLERANCE = timedelta(hours=24)

    async def create_for_equine(
        self,
        equine_id: str,
        payload: EquineEventCreateSchema,
    ) -> EquineEventDocument:
        equine = await EquineDocument.get(equine_id)
        if equine is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EQUINE_NOT_FOUND,
                message="Equino no encontrado.",
            )

        await self._validate_payload(
            equine_oid=equine.id,
            event_type=payload.event_type,
            happened_at=payload.happened_at,
            measured_weight_kg=payload.measured_weight_kg,
            measured_height_m=payload.measured_height_m,
            affects_availability=payload.affects_availability,
            resulting_operational_status=payload.resulting_operational_status,
            rest_until=payload.rest_until,
            reservation_id=payload.reservation_id,
            assignment_id=payload.assignment_id,
        )

        doc = self._build_document(equine.id, payload)
        await doc.insert()
        await self._apply_side_effects(equine, doc)
        return doc

    async def list_for_equine(
        self,
        equine_id: str,
        filters: EquineEventListFilters,
    ) -> list[EquineEventDocument]:
        equine = await EquineDocument.get(equine_id)
        if equine is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EQUINE_NOT_FOUND,
                message="Equino no encontrado.",
            )

        query = self._build_list_query(equine_id, filters)
        return (
            await EquineEventDocument.find(query)
            .sort([("happened_at", -1)])
            .limit(filters.limit)
            .to_list()
        )

    async def count_for_equine(
        self,
        equine_id: str,
        filters: EquineEventListFilters,
    ) -> int:
        equine = await EquineDocument.get(equine_id)
        if equine is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EQUINE_NOT_FOUND,
                message="Equino no encontrado.",
            )
        query = self._build_list_query(equine_id, filters)
        return await EquineEventDocument.find(query).count()

    async def update(
        self,
        event_id: str,
        payload: EquineEventUpdateSchema,
    ) -> EquineEventDocument:
        doc = await self.get(event_id)
        updates = payload.model_dump(exclude_none=True)

        merged = {
            "event_type": updates.get("event_type", doc.event_type),
            "happened_at": updates.get("happened_at", doc.happened_at),
            "measured_weight_kg": updates.get("measured_weight_kg", doc.measured_weight_kg),
            "measured_height_m": updates.get("measured_height_m", doc.measured_height_m),
            "affects_availability": updates.get("affects_availability", doc.affects_availability),
            "resulting_operational_status": updates.get(
                "resulting_operational_status",
                doc.resulting_operational_status,
            ),
            "rest_until": updates.get("rest_until", doc.rest_until),
            "reservation_id": updates.get(
                "reservation_id",
                str(doc.reservation_id) if doc.reservation_id else None,
            ),
            "assignment_id": updates.get(
                "assignment_id",
                str(doc.assignment_id) if doc.assignment_id else None,
            ),
        }

        await self._validate_payload(
            equine_oid=doc.equine_id,
            event_type=merged["event_type"],
            happened_at=merged["happened_at"],
            measured_weight_kg=merged["measured_weight_kg"],
            measured_height_m=merged["measured_height_m"],
            affects_availability=merged["affects_availability"],
            resulting_operational_status=merged["resulting_operational_status"],
            rest_until=merged["rest_until"],
            reservation_id=merged["reservation_id"],
            assignment_id=merged["assignment_id"],
        )

        for field, value in updates.items():
            if field in {"reservation_id", "assignment_id", "participant_id"}:
                setattr(
                    doc,
                    field,
                    PydanticObjectId(value) if value is not None else None,
                )
            else:
                setattr(doc, field, value)

        await doc.save()
        return doc

    def _build_document(
        self,
        equine_oid: PydanticObjectId,
        payload: EquineEventCreateSchema,
    ) -> EquineEventDocument:
        data = payload.model_dump()
        data["equine_id"] = equine_oid
        for fk in ("reservation_id", "assignment_id", "participant_id"):
            if data.get(fk):
                data[fk] = PydanticObjectId(data[fk])
            else:
                data[fk] = None
        return EquineEventDocument(**data)

    def _build_list_query(
        self,
        equine_id: str,
        filters: EquineEventListFilters,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {
            "equine_id": PydanticObjectId(equine_id),
            "deleted_at": None,
        }
        if filters.event_type is not None:
            query["event_type"] = filters.event_type
        if filters.severity is not None:
            query["severity"] = filters.severity
        if filters.reservation_id is not None:
            query["reservation_id"] = PydanticObjectId(filters.reservation_id)
        if filters.affects_availability is not None:
            query["affects_availability"] = filters.affects_availability

        happened_filter: dict[str, datetime] = {}
        if filters.date_from is not None:
            happened_filter["$gte"] = filters.date_from
        if filters.date_to is not None:
            happened_filter["$lte"] = filters.date_to
        if happened_filter:
            query["happened_at"] = happened_filter

        return query

    async def _validate_payload(
        self,
        *,
        equine_oid: PydanticObjectId,
        event_type: EquineEventType,
        happened_at: datetime,
        measured_weight_kg: object,
        measured_height_m: object,
        affects_availability: bool,
        resulting_operational_status: object,
        rest_until: object,
        reservation_id: str | None,
        assignment_id: str | None,
    ) -> None:
        now = datetime.now(UTC)
        happened_utc = (
            happened_at.replace(tzinfo=UTC)
            if happened_at.tzinfo is None
            else happened_at.astimezone(UTC)
        )
        if happened_utc > now + self._FUTURE_TOLERANCE:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EQUINE_EVENT_INVALID_HAPPENED_AT,
                message="happened_at no puede estar en el futuro lejano.",
            )

        if event_type == EquineEventType.WEIGHT and measured_weight_kg is None:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EQUINE_EVENT_WEIGHT_REQUIRED,
                message="measured_weight_kg es obligatorio para event_type weight.",
            )

        if event_type == EquineEventType.HEIGHT and measured_height_m is None:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EQUINE_EVENT_HEIGHT_REQUIRED,
                message="measured_height_m es obligatorio para event_type height.",
            )

        if affects_availability and (resulting_operational_status is None and rest_until is None):
            raise ApiError(
                status_code=400,
                code=ErrorCode.EQUINE_EVENT_AVAILABILITY_FIELDS_REQUIRED,
                message=(
                    "resulting_operational_status o rest_until es obligatorio "
                    "cuando affects_availability es true."
                ),
            )

        if reservation_id is not None:
            reservation = await ReservationDocument.get(reservation_id)
            if reservation is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.RESERVATION_NOT_FOUND,
                    message="Reserva no encontrada.",
                )

        if assignment_id is not None:
            assignment = await AssignmentDocument.get(assignment_id)
            if assignment is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.ASSIGNMENT_NOT_FOUND,
                    message="Asignación no encontrada.",
                )
            if assignment.equine_id != equine_oid:
                raise ApiError(
                    status_code=400,
                    code=ErrorCode.EQUINE_EVENT_ASSIGNMENT_EQUINE_MISMATCH,
                    message="La asignación no corresponde a este equino.",
                )

    async def _apply_side_effects(
        self,
        equine: EquineDocument,
        doc: EquineEventDocument,
    ) -> None:
        changed = False

        if self._apply_positive_availability_recovery(equine, doc):
            changed = True
        elif self._apply_negative_availability_block(equine, doc):
            changed = True

        if doc.event_type == EquineEventType.WEIGHT and doc.measured_weight_kg is not None:
            equine.weight_kg = doc.measured_weight_kg
            equine.last_weight_at = doc.happened_at.date()
            changed = True

        if doc.event_type == EquineEventType.HEIGHT and doc.measured_height_m is not None:
            equine.height_m = doc.measured_height_m
            equine.last_height_at = doc.happened_at.date()
            changed = True

        if changed:
            await equine.save()

    def _apply_positive_availability_recovery(
        self,
        equine: EquineDocument,
        doc: EquineEventDocument,
    ) -> bool:
        """Recuperación: availability_change con estado operativo available."""
        if doc.event_type != EquineEventType.AVAILABILITY_CHANGE:
            return False
        if doc.resulting_operational_status != EquineOperationalStatus.AVAILABLE:
            return False

        equine.is_available = True
        equine.operational_status = EquineOperationalStatus.AVAILABLE
        equine.rest_until = None
        equine.availability_reasons = doc.description or doc.title or None
        equine.availability_notes = doc.description
        return True

    def _apply_negative_availability_block(
        self,
        equine: EquineDocument,
        doc: EquineEventDocument,
    ) -> bool:
        """Bloqueo operativo por eventos críticos de salud/descanso."""
        if not doc.affects_availability:
            return False
        if doc.event_type not in _AVAILABILITY_BLOCKING_TYPES:
            return False

        equine.is_available = False
        equine.operational_status = (
            doc.resulting_operational_status or _DEFAULT_BLOCKING_STATUS[doc.event_type]
        )
        if doc.rest_until is not None:
            equine.rest_until = doc.rest_until

        reason = (doc.description or doc.title or "").strip()
        if reason:
            equine.availability_reasons = reason[:200]
            equine.availability_notes = doc.description
        return True
