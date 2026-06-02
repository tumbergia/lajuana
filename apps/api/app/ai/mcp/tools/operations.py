from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    CloseServiceExecutionInput,
    CloseServiceExecutionOutput,
    CreateServiceLogInput,
    CreateServiceLogOutput,
    EquineHealthEventInput,
    EquineHealthEventOutput,
    EquineWorkloadInput,
    EquineWorkloadItem,
    EquineWorkloadOutput,
    LogisticsChecklistInput,
    LogisticsChecklistItem,
    LogisticsChecklistOutput,
    ReportIncidentInput,
    ReportIncidentOutput,
    ToolBlockingReason,
    UpdateEquineAvailabilityInput,
    UpdateEquineAvailabilityOutput,
)
from app.common.enums import ReservationStatus
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ParticipantDocument,
    PolicyDocument,
    ReservationDocument,
    ServiceLogDocument,
    ServiceLogEventType,
)
from app.documents.tool_call_log_document import ToolCallLogDocument


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _field(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


async def _find_reservation(reservation_id: str) -> ReservationDocument | None:
    return await ReservationDocument.get(reservation_id)


async def admin_get_logistics_checklist(
    reservation_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: LogisticsChecklistInput | None = None
    output: LogisticsChecklistOutput | None = None
    error_code: str | None = None

    try:
        payload = LogisticsChecklistInput(reservation_id=reservation_id)

        reservation = await _find_reservation(payload.reservation_id)
        if reservation is None:
            output = LogisticsChecklistOutput(
                trace_id=trace_id,
                reservation_id=payload.reservation_id,
                items=[],
                total=0,
                completed=0,
                pending=0,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Reserva no encontrada.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        items: list[LogisticsChecklistItem] = []

        status_label = {
            ReservationStatus.CONTACT: "contacto",
            ReservationStatus.QUOTED: "cotizada",
            ReservationStatus.PENDING_PAYMENT: "pendiente de pago",
            ReservationStatus.PAYMENT_RECEIVED: "comprobante recibido",
            ReservationStatus.CONFIRMED: "confirmada",
            ReservationStatus.CANCELLED: "cancelada",
            ReservationStatus.COMPLETED: "completada",
        }
        items.append(
            LogisticsChecklistItem(
                category="reserva",
                label=f"Estado: {status_label.get(reservation.status, reservation.status.value)}",
                status="completed"
                if reservation.status == ReservationStatus.CONFIRMED
                else "pending",
                details=(
                    f"{reservation.participant_count} participantes, "
                    f"{reservation.holder_name or 'sin titular'}"
                ),
            )
        )

        participants = await ParticipantDocument.find(
            {"reservation_id": reservation.id}
        ).to_list()
        completed_participants = sum(1 for p in participants if p.is_completed)
        items.append(
            LogisticsChecklistItem(
                category="participantes",
                label=f"Formularios: {completed_participants}/{len(participants)} completos",
                status="completed"
                if participants and completed_participants == len(participants)
                else "pending",
                details=(
                    None if not participants else f"{len(participants)} participantes registrados"
                ),
            )
        )

        assignments = await AssignmentDocument.find(
            {"reservation_id": reservation.id, "is_active": True}
        ).to_list()
        assigned_participants = len(assignments)
        expected_participants = len(participants)

        # Asignaciones completas (todos los participantes tienen asignación)
        all_assigned = assigned_participants >= expected_participants if expected_participants > 0 else False
        assignment_details = (
            f"{assigned_participants}/{expected_participants} participantes asignados"
            if expected_participants > 0
            else None
        )
        items.append(
            LogisticsChecklistItem(
                category="asignaciones",
                label=f"Asignaciones: {assigned_participants}/{expected_participants} completas",
                status="completed" if all_assigned else "pending",
                details=assignment_details,
            )
        )

        # Sillas asignadas — verificar que cada asignación tenga silla
        all_saddles_assigned = all(a.saddle_id is not None for a in assignments) if assignments else False
        saddles_detail = None
        if assignments:
            missing_saddles = sum(1 for a in assignments if a.saddle_id is None)
            if missing_saddles > 0:
                saddles_detail = f"{missing_saddles} asignaciones sin silla"
        items.append(
            LogisticsChecklistItem(
                category="asignaciones",
                label="Sillas asignadas",
                status="completed" if (assignments and all_saddles_assigned) else "pending",
                details=saddles_detail,
            )
        )

        # Mulas disponibles — verificar que equinos asignados sigan disponibles
        equines_unavailable = 0
        if assignments:
            for a in assignments:
                equine = await EquineDocument.get(a.equine_id)
                if equine is None or not equine.is_available or not equine.is_active:
                    equines_unavailable += 1
        equine_availability_detail = (
            f"{equines_unavailable} equino(s) asignado(s) no disponible(s)" if equines_unavailable > 0 else None
        )
        items.append(
            LogisticsChecklistItem(
                category="asignaciones",
                label="Equinos asignados verificados",
                status="completed" if equines_unavailable == 0 else "pending",
                details=equine_availability_detail,
            )
        )

        policies = await PolicyDocument.find(
            {"reservation_id": reservation.id}
        ).to_list()
        items.append(
            LogisticsChecklistItem(
                category="polizas",
                label=f"Pólizas: {len(policies)} registradas",
                status="completed" if policies else "pending",
                details=None,
            )
        )

        logs = await ServiceLogDocument.find(
            {"reservation_id": reservation.id}
        ).to_list()
        has_arrival = any(
            getattr(log, "event_type", None) == ServiceLogEventType.ARRIVAL for log in logs
        )
        items.append(
            LogisticsChecklistItem(
                category="operacion",
                label="Registro de llegada",
                status="completed" if has_arrival else "pending",
                details=None,
            )
        )

        total = len(items)
        completed = sum(1 for i in items if i.status == "completed")
        pending = sum(1 for i in items if i.status == "pending")

        output = LogisticsChecklistOutput(
            trace_id=trace_id,
            reservation_id=payload.reservation_id,
            items=items,
            total=total,
            completed=completed,
            pending=pending,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        rid = payload.reservation_id if payload else reservation_id
        output = LogisticsChecklistOutput(
            trace_id=trace_id,
            reservation_id=rid,
            items=[],
            total=0,
            completed=0,
            pending=0,
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_logistics_checklist",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def guide_create_service_log(
    reservation_id: str,
    event_type: str,
    happened_at: str | None = None,
    checkpoint_name: str | None = None,
    notes: str | None = None,
    related_participant_id: str | None = None,
    related_equine_id: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: CreateServiceLogInput | None = None
    output: CreateServiceLogOutput | None = None
    error_code: str | None = None

    try:
        payload = CreateServiceLogInput(
            reservation_id=reservation_id,
            event_type=event_type,
            happened_at=happened_at,
            checkpoint_name=checkpoint_name,
            notes=notes,
            related_participant_id=related_participant_id,
            related_equine_id=related_equine_id,
        )

        reservation = await _find_reservation(payload.reservation_id)
        if reservation is None:
            output = CreateServiceLogOutput(
                trace_id=trace_id,
                created=False,
                message="Reserva no encontrada.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Reserva no encontrada.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        event_type_enum = getattr(ServiceLogEventType, payload.event_type.upper(), None)
        if event_type_enum is None:
            output = CreateServiceLogOutput(
                trace_id=trace_id,
                created=False,
                message=f"Tipo de evento no válido: {payload.event_type}",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="log.invalid_event_type",
                        message=f"Tipo de evento no válido: {payload.event_type}",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if event_type_enum == ServiceLogEventType.CHECKPOINT and not payload.checkpoint_name:
            output = CreateServiceLogOutput(
                trace_id=trace_id,
                created=False,
                message="checkpoint_name es obligatorio para event_type checkpoint.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="log.checkpoint_name_required",
                        message="checkpoint_name es obligatorio para event_type checkpoint.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        happened = (
            datetime.fromisoformat(payload.happened_at)
            if payload.happened_at
            else datetime.now(UTC)
        )

        doc = ServiceLogDocument(
            reservation_id=reservation.id,
            event_type=event_type_enum,
            happened_at=happened,
            checkpoint_name=payload.checkpoint_name,
            notes=payload.notes,
            related_participant_id=payload.related_participant_id,
            related_equine_id=payload.related_equine_id,
        )
        await doc.insert()

        output = CreateServiceLogOutput(
            trace_id=trace_id,
            created=True,
            log_id=_safe_str(doc.id),
            message="Bitácora registrada exitosamente.",
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = CreateServiceLogOutput(
            trace_id=trace_id,
            created=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="guide_create_service_log",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def guide_report_incident(
    reservation_id: str,
    severity: str,
    description: str,
    happened_at: str | None = None,
    related_participant_id: str | None = None,
    related_equine_id: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: ReportIncidentInput | None = None
    output: ReportIncidentOutput | None = None
    error_code: str | None = None

    try:
        payload = ReportIncidentInput(
            reservation_id=reservation_id,
            severity=severity,
            description=description,
            happened_at=happened_at,
            related_participant_id=related_participant_id,
            related_equine_id=related_equine_id,
        )

        reservation = await _find_reservation(payload.reservation_id)
        if reservation is None:
            output = ReportIncidentOutput(
                trace_id=trace_id,
                reported=False,
                message="Reserva no encontrada.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Reserva no encontrada.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        happened = (
            datetime.fromisoformat(payload.happened_at)
            if payload.happened_at
            else datetime.now(UTC)
        )

        doc = ServiceLogDocument(
            reservation_id=reservation.id,
            event_type=ServiceLogEventType.INCIDENT,
            happened_at=happened,
            notes=f"[{payload.severity.upper()}] {payload.description}",
            related_participant_id=payload.related_participant_id,
            related_equine_id=payload.related_equine_id,
        )
        await doc.insert()

        output = ReportIncidentOutput(
            trace_id=trace_id,
            reported=True,
            incident_id=_safe_str(doc.id),
            message=f"Incidente reportado con severidad {payload.severity}.",
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = ReportIncidentOutput(
            trace_id=trace_id,
            reported=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="guide_report_incident",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_close_service_execution(
    reservation_id: str,
    notes: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: CloseServiceExecutionInput | None = None
    output: CloseServiceExecutionOutput | None = None
    error_code: str | None = None

    try:
        payload = CloseServiceExecutionInput(
            reservation_id=reservation_id,
            notes=notes,
        )

        reservation = await _find_reservation(payload.reservation_id)
        if reservation is None:
            output = CloseServiceExecutionOutput(
                trace_id=trace_id,
                closed=False,
                message="Reserva no encontrada.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Reserva no encontrada.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if reservation.status != ReservationStatus.CONFIRMED:
            output = CloseServiceExecutionOutput(
                trace_id=trace_id,
                closed=False,
                message=f"No se puede cerrar una reserva en estado {reservation.status.value}.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.invalid_status_transition",
                        message=(
                            "Debe estar confirmada para cerrarse. "
                            f"Estado actual: {reservation.status.value}."
                        ),
                    )
                ],
            )
            return output.model_dump(mode="json")

        reservation.status = ReservationStatus.COMPLETED
        reservation.completed_at = datetime.now(UTC)
        await reservation.save()

        await ServiceLogDocument(
            reservation_id=reservation.id,
            event_type=ServiceLogEventType.CLOSURE,
            happened_at=datetime.now(UTC),
            notes=payload.notes or "Cierre operativo ejecutado.",
        ).insert()

        output = CloseServiceExecutionOutput(
            trace_id=trace_id,
            closed=True,
            reservation_id=_safe_str(reservation.id),
            message="Ejecución de servicio cerrada exitosamente.",
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = CloseServiceExecutionOutput(
            trace_id=trace_id,
            closed=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_close_service_execution",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_add_equine_health_event(
    equine_id: str,
    event_type: str,
    description: str,
    happened_at: str | None = None,
    severity: str = "low",
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: EquineHealthEventInput | None = None
    output: EquineHealthEventOutput | None = None
    error_code: str | None = None

    try:
        payload = EquineHealthEventInput(
            equine_id=equine_id,
            event_type=event_type,
            description=description,
            happened_at=happened_at,
            severity=severity,
        )

        equine = await EquineDocument.get(payload.equine_id)
        if equine is None:
            output = EquineHealthEventOutput(
                trace_id=trace_id,
                created=False,
                message="Equino no encontrado.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="equine.not_found",
                        message="Equino no encontrado.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        happened = (
            datetime.fromisoformat(payload.happened_at)
            if payload.happened_at
            else datetime.now(UTC)
        )

        doc = ServiceLogDocument(
            reservation_id=None,
            event_type=ServiceLogEventType.NOTE,
            happened_at=happened,
            notes=f"[SALUD:{payload.severity.upper()}:{payload.event_type}] {payload.description}",
            related_equine_id=equine.id,
        )
        await doc.insert()

        output = EquineHealthEventOutput(
            trace_id=trace_id,
            created=True,
            event_id=_safe_str(doc.id),
            message=f"Evento de salud registrado para {equine.name}.",
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = EquineHealthEventOutput(
            trace_id=trace_id,
            created=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_add_equine_health_event",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_equine_workload(
    equine_ids: list[str] | None = None,
    only_available: bool = False,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: EquineWorkloadInput | None = None
    output: EquineWorkloadOutput | None = None
    error_code: str | None = None

    try:
        payload = EquineWorkloadInput(
            equine_ids=equine_ids,
            only_available=only_available,
        )

        if payload.equine_ids:
            equines: list[EquineDocument] = []
            for eid in payload.equine_ids:
                e = await EquineDocument.get(eid)
                if e is not None:
                    equines.append(e)
        else:
            equines = await EquineDocument.find_all().to_list()  # known-small: < 50 equines

        if payload.only_available:
            equines = [e for e in equines if e.is_available]

        workload: list[EquineWorkloadItem] = []
        for equine in equines:
            assignments = await AssignmentDocument.find(
                {"equine_id": equine.id, "is_active": True}
            ).to_list()

            upcoming = 0
            next_date: str | None = None
            for a in assignments:
                reservation = await ReservationDocument.get(a.reservation_id)
                if reservation and reservation.status == ReservationStatus.CONFIRMED:
                    upcoming += 1
                    if reservation.requested_date:
                        d = reservation.requested_date.isoformat()
                        if next_date is None or d < next_date:
                            next_date = d

            workload.append(
                EquineWorkloadItem(
                    equine_id=_safe_str(equine.id) or "",
                    name=equine.name,
                    is_available=equine.is_available,
                    upcoming_assignments=upcoming,
                    next_date=next_date,
                )
            )

        output = EquineWorkloadOutput(
            trace_id=trace_id,
            workload=workload,
            total=len(workload),
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = EquineWorkloadOutput(
            trace_id=trace_id,
            workload=[],
            total=0,
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_equine_workload",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_update_equine_availability(
    equine_id: str,
    is_available: bool,
    reason: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: UpdateEquineAvailabilityInput | None = None
    output: UpdateEquineAvailabilityOutput | None = None
    error_code: str | None = None

    try:
        payload = UpdateEquineAvailabilityInput(
            equine_id=equine_id,
            is_available=is_available,
            reason=reason,
        )

        equine = await EquineDocument.get(payload.equine_id)
        if equine is None:
            output = UpdateEquineAvailabilityOutput(
                trace_id=trace_id,
                updated=False,
                message="Equino no encontrado.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="equine.not_found",
                        message="Equino no encontrado.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        equine.is_available = payload.is_available
        equine.availability_notes = payload.reason
        await equine.save()

        output = UpdateEquineAvailabilityOutput(
            trace_id=trace_id,
            updated=True,
            equine_id=_safe_str(equine.id),
            is_available=equine.is_available,
            message=(
                f"Disponibilidad de {equine.name} actualizada a "
                f"{'disponible' if equine.is_available else 'no disponible'}."
            ),
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = UpdateEquineAvailabilityOutput(
            trace_id=trace_id,
            updated=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_equine_availability",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
