from __future__ import annotations

from typing import Any

from app.assistant.prompts.planner import TOOL_RESULT_RESPONSE_SYSTEM_PROMPT
from app.core.config import settings
from app.llm.factory import get_llm_provider
from app.schemas.assistant_plan import AssistantPlan, ToolResultResponse


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
                "Esto aún no confirma la reserva; para avanzar podemos continuar con la cotización "
                "y el proceso de pago."
            )

        reasons = tool_output.get("blocking_reasons") or []
        message = (
            reasons[0].get("message")
            if reasons and isinstance(reasons[0], dict)
            else "No hay disponibilidad para esa solicitud."
        )

        return f"No puedo avanzar con esa fecha: {message}"

    return "Ya revisé la información solicitada, pero no pude generar una respuesta específica."


async def compose_tool_response(
    *,
    user_message: str,
    plan: AssistantPlan,
    tool_output: dict[str, Any],
) -> str:
    if settings.assistant_tool_response_mode == "cheap":
        return cheap_tool_summary(plan=plan, tool_output=tool_output)

    payload = {
        "user_message": user_message,
        "plan": plan.model_dump(mode="json"),
        "tool_output": tool_output,
    }

    result = await get_llm_provider().generate_structured(
        system=TOOL_RESULT_RESPONSE_SYSTEM_PROMPT,
        user=str(payload),
        response_model=ToolResultResponse,
        temperature=0.4,
    )

    return result.response
