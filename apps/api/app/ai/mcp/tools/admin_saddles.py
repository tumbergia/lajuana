"""Admin CRUD tools for saddles."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateSaddleOutput,
    AdminDeactivateSaddleOutput,
    AdminGetSaddleOutput,
    AdminListAvailableSaddlesForReservationOutput,
    AdminListAvailableSaddlesItem,
    AdminListSaddlesItem,
    AdminListSaddlesOutput,
    AdminUpdateSaddleOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.schemas.saddle import SaddleCreateSchema, SaddleUpdateSchema
from app.services.saddle_service import SaddleService


def _get_service() -> SaddleService:
    from app.core.di import Container

    return Container.get_instance().saddle_service


def _format_saddle_matches(matches: list[dict[str, Any]]) -> str:
    return ", ".join(
        str(item.get("label") or item.get("code") or item.get("saddle_id"))
        for item in matches[:5]
        if isinstance(item, dict)
    )


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


async def admin_list_saddles(
    limit: int = 200,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListSaddlesOutput | None = None

    try:
        docs = await _get_service().list(limit=limit)
        items = [
            AdminListSaddlesItem(
                saddle_id=str(doc.id),
                code=doc.code,
                name=doc.name,
                is_available=doc.is_available,
            )
            for doc in docs
        ]
        output = AdminListSaddlesOutput(trace_id=trace_id, total=len(items), saddles=items)
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListSaddlesOutput(
            trace_id=trace_id,
            total=0,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_saddles",
            input_data={"limit": limit},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_get_saddle(
    saddle_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetSaddleOutput | None = None

    try:
        doc = await _get_service().get(saddle_id)
        output = AdminGetSaddleOutput(
            trace_id=trace_id,
            found=True,
            saddle_id=str(doc.id),
            code=doc.code,
            name=doc.name,
            is_available=doc.is_available,
            notes=doc.notes,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminGetSaddleOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetSaddleOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_saddle",
            input_data={"saddle_id": saddle_id},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_create_saddle(
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateSaddleOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in SaddleCreateSchema.model_fields}
        payload = SaddleCreateSchema.model_validate(filtered)
        doc = await _get_service().create(payload)
        output = AdminCreateSaddleOutput(
            created=True,
            trace_id=trace_id,
            saddle_id=str(doc.id),
            code=doc.code,
            message=f"Silla '{doc.code}' creada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateSaddleOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateSaddleOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_create_saddle",
            input_data={
                k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}
            },
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_update_saddle(
    saddle_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateSaddleOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in SaddleUpdateSchema.model_fields}
        payload = SaddleUpdateSchema.model_validate(filtered)
        doc = await _get_service().update(saddle_id, payload)
        output = AdminUpdateSaddleOutput(
            updated=True,
            trace_id=trace_id,
            saddle_id=str(doc.id),
            code=doc.code,
            message=f"Silla '{doc.code}' actualizada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateSaddleOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateSaddleOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_saddle",
            input_data={
                "saddle_id": saddle_id,
                **{k: v for k, v in kwargs.items() if k in SaddleUpdateSchema.model_fields},
            },
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_deactivate_saddle(
    saddle_id: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminDeactivateSaddleOutput | None = None

    try:
        if not saddle_id and kwargs.get("q"):
            resolution = await _get_service().resolve_saddle_reference(str(kwargs["q"]))
            if resolution.get("status") == "resolved":
                saddle_id = str(resolution.get("saddle_id"))
            elif resolution.get("matches"):
                matches = resolution.get("matches", [])
                message = (
                    f"Encontré estas coincidencias para silla '{resolution.get('reference', kwargs['q'])}': "
                    f"{_format_saddle_matches(matches)}. Indícame el saddle_id exacto o copia una de estas opciones."
                )
                output = AdminDeactivateSaddleOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    blocking_reasons=[
                        ToolBlockingReason(
                            code="saddle.reference_ambiguous",
                            message=message,
                            details={"matches": matches},
                        )
                    ],
                )
                return output.model_dump(mode="json")
            else:
                message = (
                    f"No encontré coincidencias para silla '{resolution.get('reference', kwargs['q'])}'. "
                    "Indícame el saddle_id exacto o el código/nombre exacto."
                )
                output = AdminDeactivateSaddleOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    blocking_reasons=[
                        ToolBlockingReason(code="saddle.reference_not_found", message=message)
                    ],
                )
                return output.model_dump(mode="json")

        if not saddle_id:
            output = AdminDeactivateSaddleOutput(
                deactivated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="saddle.id_required",
                        message="El campo saddle_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        doc = await _get_service().get(saddle_id)
        code = doc.code
        await _get_service().soft_delete(saddle_id)
        output = AdminDeactivateSaddleOutput(
            deactivated=True,
            trace_id=trace_id,
            saddle_id=saddle_id,
            code=code,
            message=f"Silla '{code}' desactivada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminDeactivateSaddleOutput(
            deactivated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminDeactivateSaddleOutput(
            deactivated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_deactivate_saddle",
            input_data={"saddle_id": saddle_id, "q": kwargs.get("q")},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_list_available_saddles_for_reservation(
    reservation_id: str,
    limit: int = 200,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListAvailableSaddlesForReservationOutput | None = None

    try:
        pairs = await _get_service().list_available_for_reservation(
            reservation_id,
            limit=limit,
        )
        items = [
            AdminListAvailableSaddlesItem(
                saddle_id=str(doc.id),
                code=doc.code,
                name=doc.name,
                is_available=doc.is_available,
                block_reason=block_reason,
            )
            for doc, block_reason in pairs
        ]
        output = AdminListAvailableSaddlesForReservationOutput(
            trace_id=trace_id,
            reservation_id=reservation_id,
            total=len(items),
            saddles=items,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminListAvailableSaddlesForReservationOutput(
            trace_id=trace_id,
            reservation_id=reservation_id,
            total=0,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListAvailableSaddlesForReservationOutput(
            trace_id=trace_id,
            reservation_id=reservation_id,
            total=0,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_available_saddles_for_reservation",
            input_data={"reservation_id": reservation_id, "limit": limit},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )
