from __future__ import annotations

import time
from typing import Any

from app.ai.assistant.prompts.planner import TOOL_RESULT_RESPONSE_SYSTEM_PROMPT
from app.ai.language.messages import build_language_instruction
from app.ai.providers.factory import get_llm_provider
from app.core.logging import logger
from app.schemas.assistant_plan import AssistantPlan, ToolResultResponse


async def compose_tool_response(
    *,
    user_message: str,
    plan: AssistantPlan,
    tool_output: dict[str, Any],
    conversation_id: str | None = None,
    channel: str | None = None,
    language: str = "es",
) -> str:
    logger.info(
        "[conversation_id=%s] Composing final response | tool=%s",
        conversation_id,
        plan.tool_name,
    )

    language_instruction = build_language_instruction(language)
    response_prompt = TOOL_RESULT_RESPONSE_SYSTEM_PROMPT.format(
        language_instruction=language_instruction,
    )

    started = time.perf_counter()

    payload = {
        "user_message": user_message,
        "plan": plan.model_dump(mode="json"),
        "tool_output": tool_output,
    }

    llm_result = await get_llm_provider().generate_structured(
        system=response_prompt,
        user=str(payload),
        response_model=ToolResultResponse,
        temperature=0.6,
        telemetry_context={"channel": channel, "conversation_id": conversation_id},
    )
    result = llm_result.response

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "[conversation_id=%s] Response composed | elapsed_ms=%d",
        conversation_id,
        elapsed_ms,
    )

    return result
