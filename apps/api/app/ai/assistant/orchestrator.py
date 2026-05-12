from __future__ import annotations

import time
from uuid import uuid4

from app.ai.assistant.planner import GeminiPlanner
from app.ai.assistant.policy import ToolPolicyEngine
from app.ai.assistant.response_composer import compose_tool_response
from app.ai.mcp import registry
from app.documents.conversation_session_document import ConversationSessionDocument
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.schemas.ask import AskRequest, AskResponse
from app.schemas.assistant_plan import AssistantAction
from app.schemas.conversation_session import merge_slots


class AssistantOrchestrator:
    def __init__(self) -> None:
        self._planner = GeminiPlanner()
        self._policy = ToolPolicyEngine()

    async def ask(self, request: AskRequest) -> AskResponse:
        trace_id = request.trace_id or str(uuid4())
        conversation_key = request.conversation_id or request.from_phone or trace_id

        session = await self._load_or_create_session(
            channel=request.channel,
            conversation_key=conversation_key,
            from_phone=request.from_phone,
            conversation_id=request.conversation_id,
            trace_id=trace_id,
        )

        turn = ConversationTurnDocument(
            trace_id=trace_id,
            channel=request.channel,
            from_phone=request.from_phone,
            user_message=request.message,
        )
        await turn.insert()

        plan = await self._planner.plan(
            user_message=request.message,
            channel=request.channel,
            conversation_context=str(session.slot_values) if session.slot_values else None,
        )

        turn.planner_output = plan.model_dump(mode="json")
        await turn.save()

        # Save all non-null arguments from planner to session slots
        if plan.arguments:
            for key, value in plan.arguments.model_dump(exclude_none=True).items():
                session.slot_values[key] = value

        # Session merge: fill null plan args from session slots
        REQUIRED_FIELDS = ["requested_date", "participant_count", "experience_query"]

        if (
            plan.action
            in {
                AssistantAction.TOOL_CALL,
                AssistantAction.ASK_CLARIFYING_QUESTION,
            }
            and plan.arguments
        ):
            plan_args = plan.arguments.model_dump()
            merge = merge_slots(
                session_slots=session.slot_values,
                plan_args=plan_args,
                required_fields=REQUIRED_FIELDS,
            )

            if merge.filled_from_session or plan.action == AssistantAction.ASK_CLARIFYING_QUESTION:
                for key, value in merge.merged.items():
                    setattr(plan.arguments, key, value)

                if not merge.still_missing:
                    plan.action = AssistantAction.TOOL_CALL
                    plan.missing_fields = []
                else:
                    plan.action = AssistantAction.ASK_CLARIFYING_QUESTION
                    plan.missing_fields = merge.still_missing

        # Handle actions that don't need tools
        if plan.action in {
            AssistantAction.FINAL_RESPONSE,
            AssistantAction.ASK_CLARIFYING_QUESTION,
            AssistantAction.HUMAN_HANDOFF,
        }:
            response = plan.response or "Necesito un poco más de información para ayudarte bien."

            if plan.action == AssistantAction.ASK_CLARIFYING_QUESTION:
                session.pending_fields = plan.missing_fields

            session.last_intent = plan.action.value
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
            await session.save()

            turn.response_text = response
            turn.status = "completed"
            await turn.save()

            return AskResponse(
                trace_id=trace_id,
                action=plan.action,
                tool_name=None,
                planner_output=plan.model_dump(mode="json"),
                tool_output={},
                response=response,
            )

        # Save session slots before tool call
        if plan.arguments:
            session.slot_values.update(plan.arguments.model_dump(exclude_none=True))
        session.pending_fields = []

        policy_decision = self._policy.validate(plan)
        if not policy_decision.allowed:
            response = (
                plan.response
                or "Necesito confirmar algunos datos antes de avanzar con esa solicitud."
            )

            turn.status = "blocked_by_policy"
            turn.error_code = policy_decision.reason
            turn.response_text = response
            await turn.save()

            session.last_intent = "blocked_by_policy"
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
            await session.save()

            return AskResponse(
                trace_id=trace_id,
                action=AssistantAction.ASK_CLARIFYING_QUESTION,
                tool_name=plan.tool_name,
                planner_output=plan.model_dump(mode="json"),
                tool_output={},
                response=response,
            )

        started = time.perf_counter()
        error_code: str | None = None
        tool_output: dict = {}

        try:
            tool_output = await registry.call(
                plan.tool_name or "",
                trace_id=trace_id,
                conversation_turn_id=str(turn.id),
                **plan.arguments.model_dump(exclude_none=True),
            )
            status = "success"
        except Exception as exc:
            error_code = "tool.execution_failed"
            status = "error"
            tool_output = {
                "error": str(exc),
                "trace_id": trace_id,
            }

        latency_ms = int((time.perf_counter() - started) * 1000)

        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=str(turn.id),
            tool_name=plan.tool_name or "unknown",
            input=plan.arguments.model_dump(),
            output=tool_output,
            status=status,
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()

        response = await compose_tool_response(
            user_message=request.message,
            plan=plan,
            tool_output=tool_output,
        )

        turn.tool_output = tool_output
        turn.response_text = response
        turn.status = "completed" if not error_code else "tool_error"
        turn.error_code = error_code
        await turn.save()

        session.last_intent = plan.action.value if plan.action else "tool_executed"
        session.last_trace_id = trace_id
        session.turn_count += 1
        session.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
        await session.save()

        return AskResponse(
            trace_id=trace_id,
            action=plan.action,
            tool_name=plan.tool_name,
            planner_output=plan.model_dump(mode="json"),
            tool_output=tool_output,
            response=response,
        )

    async def _load_or_create_session(
        self,
        *,
        channel: str,
        conversation_key: str,
        from_phone: str | None,
        conversation_id: str | None,
        trace_id: str,
    ) -> ConversationSessionDocument:
        existing = await ConversationSessionDocument.find_one(
            ConversationSessionDocument.channel == channel,
            ConversationSessionDocument.conversation_key == conversation_key,
            ConversationSessionDocument.status == "active",
        )

        if existing:
            return existing

        return await ConversationSessionDocument(
            channel=channel,
            conversation_key=conversation_key,
            from_phone=from_phone,
            conversation_id=conversation_id,
            last_trace_id=trace_id,
        ).insert()
