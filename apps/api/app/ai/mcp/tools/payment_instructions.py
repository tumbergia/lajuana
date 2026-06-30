from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    GetPaymentInstructionsInput,
    GetPaymentInstructionsOutput,
)
from app.ai.mcp.tools.reservation_draft import _GOOGLE_MAPS_LINK, _PAYMENT_STEPS
from app.documents.tool_call_log_document import ToolCallLogDocument


def _format_bold_notice() -> str:
    return (
        "Para el link de pago Bold, un asesor humano de La Juana se comunicará "
        "contigo para generarlo con el valor correspondiente. Te avisará en cuanto "
        "esté listo. Recuerda: con este medio se carga 7% adicional al valor del "
        "servicio, por comisión del intermediario."
    )


async def get_payment_instructions(**kwargs: Any) -> dict[str, Any]:
    """Entrega los medios de pago disponibles por WhatsApp (texto plano literal).

    No hay sistema de envío por correo: toda la información de pago se entrega
    aqui. Si el usuario pidió explícitamente el link de Bold, se marca la
    conversación para handoff a un admin, que será quien genere el link y
    continue la conversación.
    """
    trace_id = str(kwargs.pop("trace_id", None) or uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    filtered = {k: v for k, v in kwargs.items() if k in GetPaymentInstructionsInput.model_fields}
    payload = GetPaymentInstructionsInput.model_validate(filtered)

    base_steps = _PAYMENT_STEPS.format(location_link=_GOOGLE_MAPS_LINK)

    code_line = ""
    if payload.reservation_code:
        code_line = f"Reserva: {payload.reservation_code}\n\n"

    if payload.bold_requested:
        response = (
            f"{code_line}Medios de pago disponibles:\n\n{base_steps}\n\n"
            f"{_format_bold_notice()}"
        )
    else:
        response = f"{code_line}Para confirmar tu reserva sigue estos pasos:\n\n{base_steps}"

    output = GetPaymentInstructionsOutput(
        trace_id=trace_id,
        reservation_code=payload.reservation_code,
        bold_requested=payload.bold_requested,
        response=response,
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    await ToolCallLogDocument(
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
        tool_name="get_payment_instructions",
        input=payload.model_dump(mode="json"),
        output=output.model_dump(mode="json"),
        status="success",
        latency_ms=latency_ms,
    ).insert()

    return output.model_dump(mode="json")