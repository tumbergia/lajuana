"""Admin tools for participant management."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminGetParticipantOutput,
    AdminUpdateParticipantOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.schemas.participant import ParticipantUpdateSchema
from app.services.participant_service import ParticipantService

_service = ParticipantService()


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


async def admin_get_participant(
    participant_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetParticipantOutput | None = None

    try:
        doc = await _service.get(participant_id)
        ec = doc.emergency_contact
        output = AdminGetParticipantOutput(
            trace_id=trace_id,
            found=True,
            participant_id=str(doc.id),
            reservation_id=str(doc.reservation_id),
            first_name=doc.first_name,
            last_name=doc.last_name,
            birth_date=doc.birth_date.isoformat() if doc.birth_date else None,
            document_type=doc.document_type,
            document_number=doc.document_number,
            phone=doc.phone,
            country=doc.country,
            city=doc.city,
            height_cm=str(doc.height_cm) if doc.height_cm else None,
            weight_kg=str(doc.weight_kg) if doc.weight_kg else None,
            experience_level=str(doc.experience_level.value) if doc.experience_level else None,
            dietary_restrictions=doc.dietary_restrictions,
            blood_type=doc.blood_type,
            health_conditions=doc.health_conditions,
            emergency_contact_name=ec.name if ec else None,
            emergency_contact_phone=ec.phone if ec else None,
            accepted_data_processing=doc.accepted_data_processing,
            accepted_risk_release=doc.accepted_risk_release,
            is_completed=doc.is_completed,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminGetParticipantOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetParticipantOutput(
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
            tool_name="admin_get_participant",
            input={"participant_id": participant_id},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_update_participant(
    participant_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateParticipantOutput | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in ParticipantUpdateSchema.model_fields and v is not None
        }
        payload = ParticipantUpdateSchema.model_validate(filtered)
        doc = await _service.update(participant_id, payload)

        output = AdminUpdateParticipantOutput(
            trace_id=trace_id,
            updated=True,
            participant_id=str(doc.id),
            message=f"Participante '{doc.first_name} {doc.last_name}' actualizado exitosamente.",
            is_completed=doc.is_completed,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateParticipantOutput(
            trace_id=trace_id,
            updated=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateParticipantOutput(
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
            tool_name="admin_update_participant",
            input={
                "participant_id": participant_id,
                **{k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
