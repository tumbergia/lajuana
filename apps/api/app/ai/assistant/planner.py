import time

from app.ai.assistant.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.ai.providers.factory import get_llm_provider
from app.core.logging import logger
from app.schemas.assistant_plan import AssistantPlan


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

        context = {
            "channel": channel,
            "conversation_context": conversation_context or "",
            "user_message": user_message,
        }

        result = await get_llm_provider().generate_structured(
            system=PLANNER_SYSTEM_PROMPT,
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
