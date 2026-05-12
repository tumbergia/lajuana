from __future__ import annotations

import time
from typing import Any

from app.ai.assistant.prompts.planner import TOOL_RESULT_RESPONSE_SYSTEM_PROMPT
from app.ai.providers.factory import get_llm_provider
from app.core.config import settings
from app.core.logging import logger
from app.schemas.assistant_plan import AssistantPlan, ToolResultResponse


def _fmt_duration(val: Any) -> str:
    if val is None:
        return ""
    text = str(val)
    if text.isdigit():
        h = int(text)
        return f"{h} hora(s)" if h < 24 else f"{h // 24} día(s)"
    return text


def _fmt_price(val: Any) -> str:
    if val is None:
        return ""
    return f"Desde ${val:,} COP"


def cheap_tool_summary(*, plan: AssistantPlan, tool_output: dict[str, Any]) -> str:
    if plan.tool_name == "check_experience_availability":
        if tool_output.get("available") is True:
            experience_name = tool_output.get("experience_name") or "la experiencia solicitada"
            requested_date = tool_output.get("requested_date")
            participant_count = tool_output.get("participant_count")
            capacity_available = tool_output.get("capacity_available")

            return (
                f"Sí, hay disponibilidad para {experience_name} el {requested_date} "
                f"para {participant_count} persona(s). Cupos disponibles: {capacity_available}. "
                "Esto aún no confirma la reserva; para avanzar puedes continuar con la cotización "
                "y el proceso de pago."
            )

        reasons = tool_output.get("blocking_reasons") or []
        message = (
            reasons[0].get("message")
            if reasons and isinstance(reasons[0], dict)
            else "No hay disponibilidad para esa solicitud."
        )

        return f"No puedo avanzar con esa fecha: {message}"

    if plan.tool_name == "list_experiences":
        items = tool_output.get("experiences") or []
        if not items:
            return "Actualmente no hay experiencias activas en el catálogo."

        lines: list[str] = []
        for exp in items:
            name = exp.get("name", "")
            desc = exp.get("short_description", "")
            dur = _fmt_duration(exp.get("duration"))
            price = _fmt_price(exp.get("starting_price"))
            parts = [name]
            if desc:
                parts.append(desc)
            if dur:
                parts.append(dur)
            if price:
                parts.append(price)
            lines.append(" • ".join(parts))

        return (
            "Estas son las experiencias que tenemos disponibles:\n\n"
            + "\n\n".join(lines)
            + "\n\n¿Te gustaría saber más sobre alguna o te ayudo a revisar disponibilidad?"
        )

    if plan.tool_name == "quote_experience":
        if tool_output.get("quoted") is True:
            experience_name = tool_output.get("experience_name") or "la experiencia solicitada"
            participants_count = tool_output.get("participants_count")
            unit_price = tool_output.get("unit_price")
            subtotal = tool_output.get("subtotal")
            currency = tool_output.get("currency", "COP")

            lines = [
                f"Para {experience_name}, la tarifa para {participants_count} persona(s) "
                f"es de {unit_price:,} {currency} por persona.",
                f"Total estimado: {subtotal:,} {currency}.",
            ]

            disclaimer = tool_output.get("disclaimer")
            if disclaimer:
                lines.append(disclaimer)

            return " ".join(lines)

        reasons = tool_output.get("blocking_reasons") or []
        message = (
            reasons[0].get("message")
            if reasons and isinstance(reasons[0], dict)
            else "No pude generar la cotizacion con la informacion disponible."
        )

        return f"No pude cotizar todavia: {message}"

    return "Ya revisé la información solicitada, pero no pude generar una respuesta específica."


async def compose_tool_response(
    *,
    user_message: str,
    plan: AssistantPlan,
    tool_output: dict[str, Any],
    conversation_id: str | None = None,
) -> str:
    logger.info(
        "[conversation_id=%s] Composing final response | tool=%s | mode=%s",
        conversation_id,
        plan.tool_name,
        settings.assistant_tool_response_mode,
    )

    started = time.perf_counter()

    if settings.assistant_tool_response_mode == "cheap":
        result = cheap_tool_summary(plan=plan, tool_output=tool_output)
    else:
        payload = {
            "user_message": user_message,
            "plan": plan.model_dump(mode="json"),
            "tool_output": tool_output,
        }

        llm_result = await get_llm_provider().generate_structured(
            system=TOOL_RESULT_RESPONSE_SYSTEM_PROMPT,
            user=str(payload),
            response_model=ToolResultResponse,
            temperature=0.4,
        )
        result = llm_result.response

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "[conversation_id=%s] Response composed | elapsed_ms=%d",
        conversation_id,
        elapsed_ms,
    )

    return result
