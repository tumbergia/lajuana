"""Admin tools for equine event timeline."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateEquineEventOutput,
    AdminListEquineEventsItem,
    AdminListEquineEventsOutput,
    AdminUpdateEquineEventOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.documents.equine_event_document import EquineEventType
from app.schemas.equine_event import (
    EquineEventCreateSchema,
    EquineEventListFilters,
    EquineEventUpdateSchema,
)
from app.services.equine_event_service import EquineEventService


def _get_service() -> EquineEventService:
    from app.core.di import Container
    return Container.get_instance().equine_event_service


async def _log(
    *,
    trace_id: str,
    conversation_turn_id: str | None,
    tool_name: str,
    input_data: dict[str, Any],
    output: dict[str, Any] | None,
    error_code: str | None,
    started: float,
) -> None:
    from app.documents.tool_call_log_document import ToolCallLogDocument

    latency_ms = int((time.perf_counter() - started) * 1000)
    await ToolCallLogDocument(
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
        tool_name=tool_name,
        input=input_data,
        output=output or {},
        status="error" if error_code else "success",
        error_code=error_code,
        latency_ms=latency_ms,
    ).insert()


async def admin_list_equine_events(
    equine_id: str,
    event_type: str | None = None,
    limit: int = 50,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListEquineEventsOutput | None = None

    try:
        etype = EquineEventType(event_type) if event_type else None
        filters = EquineEventListFilters(event_type=etype, limit=limit)
        docs = await _get_service().list_for_equine(equine_id, filters)
        items = [
            AdminListEquineEventsItem(
                event_id=str(doc.id),
                event_type=str(doc.event_type),
                title=doc.title,
                happened_at=doc.happened_at.isoformat(),
                severity=doc.severity,
                affects_availability=doc.affects_availability,
            )
            for doc in docs
        ]
        output = AdminListEquineEventsOutput(
            trace_id=trace_id,
            equine_id=equine_id,
            total=len(items),
            events=items,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminListEquineEventsOutput(
            trace_id=trace_id,
            equine_id=equine_id,
            total=0,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListEquineEventsOutput(
            trace_id=trace_id,
            equine_id=equine_id,
            total=0,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_equine_events",
            input_data={"equine_id": equine_id, "event_type": event_type, "limit": limit},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_create_equine_event(
    equine_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateEquineEventOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in EquineEventCreateSchema.model_fields}
        filtered.setdefault("source", "ai_tool")
        payload = EquineEventCreateSchema.model_validate(filtered)
        doc = await _get_service().create_for_equine(equine_id, payload)
        output = AdminCreateEquineEventOutput(
            created=True,
            trace_id=trace_id,
            event_id=str(doc.id),
            equine_id=equine_id,
            title=doc.title,
            message=f"Evento '{doc.title}' registrado para el equino.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateEquineEventOutput(
            created=False,
            trace_id=trace_id,
            equine_id=equine_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateEquineEventOutput(
            created=False,
            trace_id=trace_id,
            equine_id=equine_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_create_equine_event",
            input_data={"equine_id": equine_id, **{k: v for k, v in kwargs.items() if k in EquineEventCreateSchema.model_fields}},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_update_equine_event(
    event_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateEquineEventOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in EquineEventUpdateSchema.model_fields}
        payload = EquineEventUpdateSchema.model_validate(filtered)
        doc = await _get_service().update(event_id, payload)
        output = AdminUpdateEquineEventOutput(
            updated=True,
            trace_id=trace_id,
            event_id=str(doc.id),
            title=doc.title,
            message=f"Evento '{doc.title}' actualizado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateEquineEventOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateEquineEventOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_equine_event",
            input_data={"event_id": event_id, **{k: v for k, v in kwargs.items() if k in EquineEventUpdateSchema.model_fields}},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )
