import time
from datetime import UTC, datetime

from app.ai.assistant.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.ai.providers.factory import get_llm_provider
from app.core.logging import logger
from app.schemas.assistant_plan import AssistantPlan

_DAYS_ES = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]
_MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


class GeminiPlanner:
    async def plan(
        self,
        *,
        user_message: str,
        channel: str,
        conversation_context: str | None = None,
        conversation_id: str | None = None,
    ) -> AssistantPlan:
        logger.info(
            "[conversation_id=%s] LLM receives message | channel=%s",
            conversation_id,
            channel,
        )

        started = time.perf_counter()

        now = datetime.now(UTC)
        wd = _DAYS_ES[now.weekday()]
        mo = _MONTHS_ES[now.month - 1]
        today_formatted = f"{wd.capitalize()} {now.day} de {mo} de {now.year}"

        system_prompt = PLANNER_SYSTEM_PROMPT.format(
            today_formatted=today_formatted,
            today_year=str(now.year),
        )

        context = {
            "today": now.strftime("%Y-%m-%d"),
            "today_description": today_formatted,
            "current_time": now.strftime("%H:%M"),
            "channel": channel,
            "conversation_context": conversation_context or "",
            "user_message": user_message,
        }

        result = await get_llm_provider().generate_structured(
            system=system_prompt,
            user=str(context),
            response_model=AssistantPlan,
            temperature=0.1,
        )

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "[conversation_id=%s] LLM response | elapsed_ms=%d",
            conversation_id,
            elapsed_ms,
        )

        return result
