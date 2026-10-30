"""Admin tools for reservation management."""

from __future__ import annotations

import time
from datetime import date
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCancelReservationOutput,
    AdminConfirmReservationOutput,
    AdminGetReservationDetailOutput,
    AdminListReservationsItem,
    AdminListReservationsOutput,
    ToolBlockingReason,
)
from app.core.di import Container
from app.core.errors import ApiError
from app.documents import ExperienceDocument

_service = None  # lazy via _get_service()


def _get_service():
    global _service
    if _service is None:
        _service = Container.get_instance().reservation_service
    return _service


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


async def admin_list_reservations(
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminListReservationsOutput | None = None

    try:
        docs = await _get_service().list(actor_role="admin")  # type: ignore[arg-type]

        # Apply filters
        filtered = docs
        if status:
            filtered = [d for d in filtered if str(d.status.value).lower() == status.lower()]
        if date_from:
            df = date.fromisoformat(date_from)
            filtered = [d for d in filtered if d.requested_date and d.requested_date >= df]
        if date_to:
            dt = date.fromisoformat(date_to)
            filtered = [d for d in filtered if d.requested_date and d.requested_date <= dt]

        filtered = filtered[:limit]

        items = []
        for doc in filtered:
            exp_name = ""
            if doc.experience_id:
                exp = await ExperienceDocument.get(doc.experience_id)
                if exp:
                    exp_name = exp.name

            items.append(
                AdminListReservationsItem(
                    reservation_id=str(doc.id),
                    code=doc.code,
                    status=str(doc.status.value),
                    participant_count=doc.participant_count,
                    payment_status=str(doc.payment_status.value) if doc.payment_status else "",
                    holder_name=doc.holder_name,
                    holder_phone=doc.holder_phone,
                    experience_id=str(doc.experience_id) if doc.experience_id else "",
                    experience_name=exp_name or None,
                    requested_date=doc.requested_date.isoformat() if doc.requested_date else None,
                    channel=str(doc.channel.value) if doc.channel else None,
                )
            )

        output = AdminListReservationsOutput(
            trace_id=trace_id,
            total=len(items),
            reservations=items,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListReservationsOutput(
            trace_id=trace_id,
            total=0,
            reservations=[],
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_reservations",
            input={
                "status": status,
                "date_from": date_from,
                "date_to": date_to,
                "limit": limit,
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_reservation_detail(
    reservation_id: str | None = None,
    code: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminGetReservationDetailOutput | None = None

    try:
        doc = None
        if reservation_id:
            doc = await _get_service().get(reservation_id)
        elif code:
            doc = await _get_service().find_by_code_or_id(code)
        else:
            output = AdminGetReservationDetailOutput(
                trace_id=trace_id,
                found=False,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.id_required",
                        message="Se requiere reservation_id o code.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if doc is None:
            output = AdminGetReservationDetailOutput(
                trace_id=trace_id,
                found=False,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Reserva no encontrada.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        exp_name = ""
        if doc.experience_id:
            exp = await ExperienceDocument.get(doc.experience_id)
            if exp:
                exp_name = exp.name

        output = AdminGetReservationDetailOutput(
            trace_id=trace_id,
            found=True,
            reservation_id=str(doc.id),
            code=doc.code,
            status=str(doc.status.value),
            participant_count=doc.participant_count,
            payment_status=str(doc.payment_status.value) if doc.payment_status else None,
            holder_name=doc.holder_name,
            holder_phone=doc.holder_phone,
            experience_id=str(doc.experience_id) if doc.experience_id else None,
            experience_name=exp_name or None,
            requested_date=doc.requested_date.isoformat() if doc.requested_date else None,
            quoted_total_amount=str(doc.quoted_total_amount) if doc.quoted_total_amount else None,
            participant_form_status=str(doc.participant_form_status.value)
            if doc.participant_form_status
            else None,
            form_url=doc.form_url,
            confirmed_at=doc.confirmed_at.isoformat() if doc.confirmed_at else None,
            cancelled_at=doc.cancelled_at.isoformat() if doc.cancelled_at else None,
            completed_at=doc.completed_at.isoformat() if doc.completed_at else None,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminGetReservationDetailOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetReservationDetailOutput(
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
            tool_name="admin_get_reservation_detail",
            input={"reservation_id": reservation_id, "code": code},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_confirm_reservation(
    reservation_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminConfirmReservationOutput | None = None

    try:
        doc = await _get_service().confirm_reservation(
            reservation_id=reservation_id,
            actor_id=None,
        )

        output = AdminConfirmReservationOutput(
            trace_id=trace_id,
            confirmed=True,
            reservation_id=str(doc.id),
            code=doc.code,
            message="Reserva confirmada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminConfirmReservationOutput(
            trace_id=trace_id,
            confirmed=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminConfirmReservationOutput(
            trace_id=trace_id,
            confirmed=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_confirm_reservation",
            input={"reservation_id": reservation_id},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_cancel_reservation(
    reservation_id: str,
    reason: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminCancelReservationOutput | None = None

    try:
        doc = await _get_service().cancel_reservation(
            reservation_id=reservation_id,
            actor_id=None,
        )

        msg = "Reserva cancelada exitosamente."
        if reason:
            msg = f"Reserva cancelada. Motivo: {reason}"

        output = AdminCancelReservationOutput(
            trace_id=trace_id,
            cancelled=True,
            reservation_id=str(doc.id),
            code=doc.code,
            message=msg,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCancelReservationOutput(
            trace_id=trace_id,
            cancelled=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCancelReservationOutput(
            trace_id=trace_id,
            cancelled=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_cancel_reservation",
            input={"reservation_id": reservation_id, "reason": reason},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
