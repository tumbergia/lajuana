from app.assistant.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.llm.factory import get_llm_provider
from app.schemas.assistant_plan import AssistantPlan


class GeminiPlanner:
    async def plan(
        self,
        *,
        user_message: str,
        channel: str,
        conversation_context: str | None = None,
    ) -> AssistantPlan:
        context = {
            "channel": channel,
            "conversation_context": conversation_context or "",
            "user_message": user_message,
        }

        return await get_llm_provider().generate_structured(
            system=PLANNER_SYSTEM_PROMPT,
            user=str(context),
            response_model=AssistantPlan,
            temperature=0.1,
        )
