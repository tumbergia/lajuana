"""Admin CRUD tools for equines."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateEquineOutput,
    AdminDeactivateEquineOutput,
    AdminGetEquineOutput,
    AdminListEquinesItem,
    AdminListEquinesOutput,
    AdminUpdateEquineOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.documents import EquineDocument
from app.schemas.equine import EquineCreateSchema, EquineUpdateSchema
from app.services.equine_service import EquineService

_service = EquineService()


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


async def admin_list_equines(
    only_available: bool = False,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListEquinesOutput | None = None

    try:
        docs = await _service.list()
        if only_available:
            docs = [d for d in docs if d.is_available]

        items = [
            AdminListEquinesItem(
                equine_id=str(doc.id),
                name=doc.name,
                is_available=doc.is_available,
                breed=doc.breed,
                sex=doc.sex,
                approximate_age_years=doc.approximate_age_years,
            )
            for doc in docs
        ]

        output = AdminListEquinesOutput(
            trace_id=trace_id,
            total=len(items),
            equines=items,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListEquinesOutput(
            trace_id=trace_id,
            total=0,
            equines=[],
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_equines",
            input={"only_available": only_available},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_equine(
    equine_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetEquineOutput | None = None

    try:
        doc = await _service.get(equine_id)
        output = AdminGetEquineOutput(
            trace_id=trace_id,
            found=True,
            equine_id=str(doc.id),
            name=doc.name,
            approximate_birth_date=doc.approximate_birth_date.isoformat() if doc.approximate_birth_date else None,
            approximate_age_years=doc.approximate_age_years,
            weight_kg=str(doc.weight_kg) if doc.weight_kg else None,
            sex=doc.sex,
            breed=doc.breed,
            gait=doc.gait,
            is_available=doc.is_available,
            availability_notes=doc.availability_notes,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminGetEquineOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetEquineOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_equine",
            input={"equine_id": equine_id},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_create_equine(
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateEquineOutput | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in EquineCreateSchema.model_fields
        }
        payload = EquineCreateSchema.model_validate(filtered)
        doc = await _service.create(payload)

        output = AdminCreateEquineOutput(
            trace_id=trace_id,
            created=True,
            equine_id=str(doc.id),
            name=doc.name,
            message=f"Equino '{doc.name}' creado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateEquineOutput(
            trace_id=trace_id,
            created=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateEquineOutput(
            trace_id=trace_id,
            created=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_create_equine",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_update_equine(
    equine_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateEquineOutput | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in EquineUpdateSchema.model_fields and v is not None
        }
        payload = EquineUpdateSchema.model_validate(filtered)
        doc = await _service.update(equine_id, payload)

        output = AdminUpdateEquineOutput(
            trace_id=trace_id,
            updated=True,
            equine_id=str(doc.id),
            name=doc.name,
            message=f"Equino '{doc.name}' actualizado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateEquineOutput(
            trace_id=trace_id,
            updated=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateEquineOutput(
            trace_id=trace_id,
            updated=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_equine",
            input={
                "equine_id": equine_id,
                **{k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_deactivate_equine(
    equine_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminDeactivateEquineOutput | None = None

    try:
        doc = await _service.deactivate(equine_id)

        output = AdminDeactivateEquineOutput(
            trace_id=trace_id,
            deactivated=True,
            equine_id=str(doc.id),
            name=doc.name,
            message=f"Equino '{doc.name}' desactivado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminDeactivateEquineOutput(
            trace_id=trace_id,
            deactivated=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminDeactivateEquineOutput(
            trace_id=trace_id,
            deactivated=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_deactivate_equine",
            input={"equine_id": equine_id},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
