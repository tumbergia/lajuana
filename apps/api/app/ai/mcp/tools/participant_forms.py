from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    GenerateParticipantFormLinkInput,
    GenerateParticipantFormLinkOutput,
    GetParticipantFormStatusInput,
    GetParticipantFormStatusOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.documents import ReservationDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.services.participant_form_link_service import ParticipantFormLinkService


async def generate_participant_form_link(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: GenerateParticipantFormLinkInput | None = None
    output: GenerateParticipantFormLinkOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in GenerateParticipantFormLinkInput.model_fields
        }
        payload = GenerateParticipantFormLinkInput.model_validate(filtered)

        service = ParticipantFormLinkService()
        # Get the reservation to know expected participants count
        reservation = await ReservationDocument.get(payload.reservation_id)
        expected_count = reservation.participant_count if reservation else 1
        doc, raw_token = await service.generate(
            reservation_id=payload.reservation_id,
            expected_participants_count=expected_count,
        )

        from app.core.config import settings

        form_url = f"{settings.app_base_url}/formulario-participantes?t={raw_token}"

        output = GenerateParticipantFormLinkOutput(
            generated=True,
            trace_id=trace_id,
            reservation_id=payload.reservation_id,
            public_reservation_code=reservation.code if reservation else "",
            form_url=form_url,
            participant_limit=doc.max_participants,
            participants_registered=doc.used_count,
            participants_remaining=max(0, doc.max_participants - doc.used_count),
            expires_at=doc.expires_at,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = GenerateParticipantFormLinkOutput(
            generated=False,
            trace_id=trace_id,
            reservation_id=payload.reservation_id if payload else "",
            public_reservation_code="",
            blocking_reasons=[
                ToolBlockingReason(
                    code=exc.code,
                    message=exc.message,
                    details=exc.details or {},
                )
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = GenerateParticipantFormLinkOutput(
            generated=False,
            trace_id=trace_id,
            reservation_id=payload.reservation_id if payload else "",
            public_reservation_code="",
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
            tool_name="generate_participant_form_link",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def get_participant_form_status(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: GetParticipantFormStatusInput | None = None
    output: GetParticipantFormStatusOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in GetParticipantFormStatusInput.model_fields
        }
        payload = GetParticipantFormStatusInput.model_validate(filtered)

        if payload.reservation_id:
            reservation = await ReservationDocument.get(payload.reservation_id)
        elif payload.public_reservation_code:
            reservation = await ReservationDocument.find_one(
                {"code": payload.public_reservation_code}
            )
        else:
            output = GetParticipantFormStatusOutput(
                found=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Debe proporcionar reservation_id o public_reservation_code.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if reservation is None:
            output = GetParticipantFormStatusOutput(
                found=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Reserva no encontrada.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        limit = reservation.expected_participants_count or reservation.participant_count
        registered = reservation.participants_completed_count
        output = GetParticipantFormStatusOutput(
            found=True,
            trace_id=trace_id,
            reservation_id=str(reservation.id),
            public_reservation_code=reservation.code,
            participant_limit=limit,
            participants_registered=registered,
            participants_remaining=max(0, limit - registered),
            form_status=reservation.participant_form_status,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = GetParticipantFormStatusOutput(
            found=False,
            trace_id=trace_id,
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
            tool_name="get_participant_form_status",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
