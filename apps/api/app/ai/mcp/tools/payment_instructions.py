from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import GetPaymentInstructionsInput, GetPaymentInstructionsOutput
from app.core.di import Container
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.services.payment_message_service import render_payment_steps


async def get_payment_instructions(**kwargs: Any) -> dict[str, Any]:
    trace_id = str(kwargs.pop("trace_id", None) or uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()
    filtered = {k: v for k, v in kwargs.items() if k in GetPaymentInstructionsInput.model_fields}
    payload = GetPaymentInstructionsInput.model_validate(filtered)
    config = await Container.get_instance().config_service.get_payment_instructions()
    code_line = f"Reserva: {payload.reservation_code}\n\n" if payload.reservation_code else ""
    if payload.bold_requested and not config.bold_enabled:
        response = (
            f"{code_line}El pago por Bold no está disponible en este momento.\n\n"
            f"{render_payment_steps(config)}"
        )
    else:
        response = (
            f"{code_line}Para confirmar tu reserva sigue estos pasos:\n\n"
            f"{render_payment_steps(config)}"
        )
    output = GetPaymentInstructionsOutput(
        trace_id=trace_id,
        reservation_code=payload.reservation_code,
        bold_requested=payload.bold_requested,
        response=response,
    )
    await ToolCallLogDocument(
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
        tool_name="get_payment_instructions",
        input=payload.model_dump(mode="json"),
        output=output.model_dump(mode="json"),
        status="success",
        latency_ms=int((time.perf_counter() - started) * 1000),
    ).insert()
    return output.model_dump(mode="json")
