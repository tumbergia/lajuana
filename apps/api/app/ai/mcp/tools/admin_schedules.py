"""Admin CRUD tools for schedules."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateScheduleOutput,
    AdminDeactivateScheduleOutput,
    AdminListSchedulesOutput,
    AdminUpdateScheduleOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.schemas.schedule import ScheduleCreateSchema, ScheduleUpdateSchema
from app.services.schedule_service import ScheduleService


def _get_service() -> ScheduleService:
    from app.core.di import Container
    return Container.get_instance().schedule_service


async def admin_create_schedule(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateScheduleOutput | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in ScheduleCreateSchema.model_fields
        }
        payload = ScheduleCreateSchema.model_validate(filtered)
        doc = await _get_service().create(payload)

        output = AdminCreateScheduleOutput(
            created=True,
            trace_id=trace_id,
            schedule_id=str(doc.id),
            experience_id=str(doc.experience_id),
            scheduled_date=doc.date.isoformat() if doc.date else "",
            message=f"Schedule creado para {doc.date}.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateScheduleOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateScheduleOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_create_schedule",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_update_schedule(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateScheduleOutput | None = None

    try:
        schedule_id = kwargs.get("schedule_id")
        if not schedule_id:
            output = AdminUpdateScheduleOutput(
                updated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="schedule.id_required",
                        message="El campo schedule_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in ScheduleUpdateSchema.model_fields and v is not None
        }
        payload = ScheduleUpdateSchema.model_validate(filtered)
        doc = await _get_service().update(schedule_id, payload)

        output = AdminUpdateScheduleOutput(
            updated=True,
            trace_id=trace_id,
            schedule_id=str(doc.id),
            experience_id=str(doc.experience_id),
            scheduled_date=doc.date.isoformat() if doc.date else "",
            message=f"Schedule actualizado para {doc.date}.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateScheduleOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateScheduleOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_schedule",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_list_schedules_admin(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListSchedulesOutput | None = None

    try:
        experience_id = kwargs.get("experience_id")
        date_from = kwargs.get("date_from")
        date_to = kwargs.get("date_to")
        status = kwargs.get("status")
        is_active = kwargs.get("is_active")

        docs = await _get_service().list(
            experience_id=experience_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
            is_active=is_active,
        )

        items = []
        for doc in docs:
            items.append(
                {
                    "schedule_id": str(doc.id),
                    "experience_id": str(doc.experience_id),
                    "scheduled_date": doc.date.isoformat() if doc.date else "",
                    "start_time": str(getattr(doc, "start_time", "")),
                    "capacity_total": doc.capacity_total,
                    "available_slots": doc.available_slots,
                    "reserved_slots": doc.reserved_slots,
                    "held_slots": doc.held_slots,
                    "blocked_slots": getattr(doc, "blocked_slots", 0),
                    "internal_slots": getattr(doc, "internal_slots", 0),
                    "status": str(doc.status),
                    "is_active": doc.is_active,
                }
            )

        output = AdminListSchedulesOutput(
            trace_id=trace_id,
            total=len(items),
            schedules=items,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListSchedulesOutput(
            trace_id=trace_id,
            total=0,
            schedules=[],
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_schedules_admin",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_deactivate_schedule(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminDeactivateScheduleOutput | None = None

    try:
        schedule_id = kwargs.get("schedule_id")
        if not schedule_id:
            output = AdminDeactivateScheduleOutput(
                deactivated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="schedule.id_required",
                        message="El campo schedule_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        doc = await _get_service().deactivate(schedule_id)
        output = AdminDeactivateScheduleOutput(
            deactivated=True,
            trace_id=trace_id,
            schedule_id=str(doc.id),
            scheduled_date=doc.date.isoformat() if doc.date else "",
            message=f"Schedule de {doc.date} desactivado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminDeactivateScheduleOutput(
            deactivated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminDeactivateScheduleOutput(
            deactivated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_deactivate_schedule",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()