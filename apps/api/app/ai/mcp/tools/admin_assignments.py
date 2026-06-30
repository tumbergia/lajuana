"""Admin tools for assignment management."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateAssignmentOutput,
    AdminDeleteAssignmentOutput,
    AdminFinalizeAllAssignmentsOutput,
    AdminFinalizeAssignmentOutput,
    AdminGetAssignmentBoardOutput,
    AdminUpdateAssignmentOutput,
    ToolBlockingReason,
)
from app.common.enums import UserRole
from app.core.errors import ApiError
from app.schemas.assignment import AssignmentCreateSchema, AssignmentUpdateSchema
from app.services.assignment_service import AssignmentService


def _get_service() -> AssignmentService:
    from app.core.di import Container
    return Container.get_instance().assignment_service


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


async def admin_get_assignment_board(
    reservation_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetAssignmentBoardOutput | None = None

    try:
        board = await _get_service().get_board(reservation_id)
        output = AdminGetAssignmentBoardOutput(
            trace_id=trace_id,
            found=True,
            reservation_id=reservation_id,
            board=board,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminGetAssignmentBoardOutput(
            trace_id=trace_id,
            found=False,
            reservation_id=reservation_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetAssignmentBoardOutput(
            trace_id=trace_id,
            found=False,
            reservation_id=reservation_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_assignment_board",
            input_data={"reservation_id": reservation_id},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_create_assignment(
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateAssignmentOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in AssignmentCreateSchema.model_fields}
        payload = AssignmentCreateSchema.model_validate(filtered)
        doc = await _get_service().create(
            payload,
            actor_id=None,
            actor_role=UserRole.ADMIN,
        )
        output = AdminCreateAssignmentOutput(
            created=True,
            trace_id=trace_id,
            assignment_id=str(doc.id),
            message="Asignación creada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateAssignmentOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateAssignmentOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_create_assignment",
            input_data={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_update_assignment(
    assignment_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateAssignmentOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in AssignmentUpdateSchema.model_fields}
        payload = AssignmentUpdateSchema.model_validate(filtered)
        doc = await _get_service().update(assignment_id, payload, actor_id=None)
        output = AdminUpdateAssignmentOutput(
            updated=True,
            trace_id=trace_id,
            assignment_id=str(doc.id),
            message="Asignación actualizada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateAssignmentOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateAssignmentOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_assignment",
            input_data={"assignment_id": assignment_id, **{k: v for k, v in kwargs.items() if k in AssignmentUpdateSchema.model_fields}},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_delete_assignment(
    assignment_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminDeleteAssignmentOutput | None = None

    try:
        await _get_service().remove(assignment_id, actor_id=None)
        output = AdminDeleteAssignmentOutput(
            deleted=True,
            trace_id=trace_id,
            assignment_id=assignment_id,
            message="Asignación eliminada del tablero.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminDeleteAssignmentOutput(
            deleted=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminDeleteAssignmentOutput(
            deleted=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_delete_assignment",
            input_data={"assignment_id": assignment_id},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_finalize_assignment(
    assignment_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminFinalizeAssignmentOutput | None = None

    try:
        doc = await _get_service().finalize(assignment_id, actor_id=None)
        output = AdminFinalizeAssignmentOutput(
            finalized=True,
            trace_id=trace_id,
            assignment_id=str(doc.id),
            message="Asignación finalizada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminFinalizeAssignmentOutput(
            finalized=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminFinalizeAssignmentOutput(
            finalized=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_finalize_assignment",
            input_data={"assignment_id": assignment_id},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_finalize_all_assignments(
    reservation_id: str,
    notes: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminFinalizeAllAssignmentsOutput | None = None

    try:
        board = await _get_service().finalize_all(
            reservation_id,
            actor_id=None,
            notes=notes,
        )
        output = AdminFinalizeAllAssignmentsOutput(
            finalized=True,
            trace_id=trace_id,
            reservation_id=reservation_id,
            board=board,
            message="Todas las asignaciones confirmadas fueron finalizadas.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminFinalizeAllAssignmentsOutput(
            finalized=False,
            trace_id=trace_id,
            reservation_id=reservation_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminFinalizeAllAssignmentsOutput(
            finalized=False,
            trace_id=trace_id,
            reservation_id=reservation_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_finalize_all_assignments",
            input_data={"reservation_id": reservation_id, "notes": notes},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )
