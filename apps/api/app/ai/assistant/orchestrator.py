from __future__ import annotations

import time
from uuid import uuid4

from app.ai.assistant.date_extractor import extract_date_from_message
from app.ai.assistant.date_guard import (
    InvalidRequestedDateError,
    validate_requested_date_for_business,
)
from app.ai.assistant.planner import GeminiPlanner
from app.ai.assistant.policy import ToolPolicyEngine
from app.ai.assistant.response_composer import compose_tool_response
from app.ai.mcp import registry
from app.ai.providers.gemini_provider import (
    GeminiModelUnavailable,
    GeminiProviderError,
    GeminiResourceExhausted,
)
from app.core.logging import logger
from app.documents.conversation_session_document import ConversationSessionDocument
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.schemas.ask import AskRequest, AskResponse
from app.schemas.assistant_plan import AssistantAction
from app.schemas.conversation_session import merge_slots


class AssistantOrchestrator:
    def __init__(self, planner: GeminiPlanner | None = None) -> None:
        self._planner = planner or GeminiPlanner()
        self._policy = ToolPolicyEngine()

    async def ask(self, request: AskRequest) -> AskResponse:
        trace_id = request.trace_id or str(uuid4())
        conversation_id = request.conversation_id
        conversation_key = conversation_id or request.from_phone or trace_id
        flow_started = time.perf_counter()

        logger.info(
            "[conversation_id=%s] Message received | channel=%s | from=%s | trace_id=%s | message=%.120s",  # noqa: E501
            conversation_id,
            request.channel,
            request.from_phone,
            trace_id,
            request.message,
        )

        session = await self._load_or_create_session(
            channel=request.channel,
            conversation_key=conversation_key,
            from_phone=request.from_phone,
            conversation_id=conversation_id,
            trace_id=trace_id,
        )

        history_turns = (
            await ConversationTurnDocument.find(
                ConversationTurnDocument.conversation_id == conversation_key,
                ConversationTurnDocument.status == "responded",
            )
            .sort(-ConversationTurnDocument.created_at)
            .limit(8)
            .to_list()
        )

        history_lines = []
        for t in reversed(history_turns):
            if t.user_message:
                history_lines.append(f"Usuario: {t.user_message}")
            if t.response_text:
                history_lines.append(f"Asistente: {t.response_text}")

        conversation_history = "\n".join(history_lines)

        enriched_context = None
        if session.slot_values or conversation_history:
            parts = []
            if session.slot_values:
                parts.append(f"Datos de la sesión: {session.slot_values}")
            if conversation_history:
                parts.append(f"Historial de la conversación:\n{conversation_history}")
            enriched_context = "\n\n".join(parts)

        try:
            plan = await self._planner.plan(
                user_message=request.message,
                channel=request.channel,
                conversation_context=enriched_context,
                conversation_id=conversation_id,
            )
        except GeminiResourceExhausted:
            return AskResponse(
                trace_id=trace_id,
                action=AssistantAction.FINAL_RESPONSE,
                planner_output={}, tool_output={},
                response="Servicio de IA sobrepasado. Intenta en unos minutos.",
            )
        except GeminiModelUnavailable:
            return AskResponse(
                trace_id=trace_id,
                action=AssistantAction.HUMAN_HANDOFF,
                planner_output={}, tool_output={},
                response="Modelo no disponible. Te transfiero con un asesor.",
            )
        except GeminiProviderError:
            return AskResponse(
                trace_id=trace_id,
                action=AssistantAction.HUMAN_HANDOFF,
                planner_output={},
                tool_output={},
                response=(
                    "Ocurrió un error temporal en mi sistema de procesamiento. "
                    "Voy a transferirte con un asesor humano para que no te quedes "
                    "sin atención."
                ),
            )

        # Fallback: if planner didn't extract date but user message has one
        if (
            plan.arguments
            and plan.action in {AssistantAction.TOOL_CALL, AssistantAction.ASK_CLARIFYING_QUESTION}
            and not plan.arguments.requested_date
        ):
            extracted = extract_date_from_message(request.message)
            if extracted:
                plan.arguments.requested_date = extracted

        # Validate requested_date against Colombia business timezone
        if plan.arguments and plan.arguments.requested_date:
            try:
                parsed_date = date.fromisoformat(plan.arguments.requested_date)
                validate_requested_date_for_business(parsed_date)
            except (InvalidRequestedDateError, ValueError):
                plan.action = AssistantAction.ASK_CLARIFYING_QUESTION
                plan.response = (
                    "Para evitar errores con la reserva, necesito que me confirmes "
                    "la fecha exacta en formato día, mes y año."
                )
                plan.arguments.requested_date = None

        turn.planner_output = plan.model_dump(mode="json")
        await turn.save()

        # Save all non-null arguments from planner to session slots
        if plan.arguments:
            for key, value in plan.arguments.model_dump(exclude_none=True).items():
                session.slot_values[key] = value

        # Session merge: fill null plan args from session slots
        REQUIRED_FIELDS = [
            "requested_date",
            "participant_count",
            "experience_query",
            "experience_id",
        ]

        if (
            plan.action
            in {AssistantAction.TOOL_CALL, AssistantAction.ASK_CLARIFYING_QUESTION}
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

        if plan.action in {
            AssistantAction.FINAL_RESPONSE,
            AssistantAction.ASK_CLARIFYING_QUESTION,
            AssistantAction.HUMAN_HANDOFF,
        }:
            response = plan.response or "Necesito más información."
            if plan.action == AssistantAction.ASK_CLARIFYING_QUESTION:
                session.pending_fields = plan.missing_fields
            session.last_intent = plan.action.value
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
            await session.save()
            return AskResponse(
                trace_id=trace_id, action=plan.action,
                planner_output=plan.model_dump(mode="json"),
                tool_output={}, response=response,
            )

        if plan.arguments:
            session.slot_values.update(plan.arguments.model_dump(exclude_none=True))
        session.pending_fields = []

        policy_decision = self._policy.validate(plan)
        if not policy_decision.allowed:
            response = plan.response or "Necesito confirmar datos antes de avanzar."
            session.last_intent = "blocked_by_policy"
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
            await session.save()
            return AskResponse(
                trace_id=trace_id, action=AssistantAction.ASK_CLARIFYING_QUESTION,
                tool_name=plan.tool_name,
                planner_output=plan.model_dump(mode="json"),
                tool_output={}, response=response,
            )

        started = time.perf_counter()
        error_code: str | None = None
        tool_output: dict = {}

        try:
            tool_output = await registry.call(
                plan.tool_name or "",
                conversation_id=conversation_id,
                trace_id=trace_id,
                conversation_turn_id=request.conversation_turn_id or str(uuid4()),
                **plan.arguments.model_dump(exclude_none=True),
            )
            status = "success"
        except Exception as exc:
            error_code = "tool.execution_failed"
            status = "error"
            tool_output = {"error": str(exc), "trace_id": trace_id}

        latency_ms = int((time.perf_counter() - started) * 1000)

        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=request.conversation_turn_id or str(uuid4()),
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
            conversation_id=conversation_id,
        )

        if (
            plan.tool_name == "suggest_alternative_dates"
            and tool_output.get("total", 0) == 0
            and not tool_output.get("blocking_reasons")
        ):
            plan.action = AssistantAction.HUMAN_HANDOFF
            response = (
                "Lo siento, no encontré más fechas disponibles para "
                "esta experiencia. Un asesor humano podrá revisar opciones "
                "alternativas y ayudarte con lo que necesites. Te transfiero ahora."
            )

        turn.tool_output = tool_output
        turn.response_text = response
        turn.status = "completed" if not error_code else "tool_error"
        turn.error_code = error_code
        await turn.save()

        # Propagate resolved experience_id from tool output to session slots
        if tool_output:
            exp_id = tool_output.get("experience_id")
            exp_name = tool_output.get("experience_name")
            if exp_id:
                session.slot_values["experience_id"] = exp_id
            if exp_name:
                session.slot_values["experience_name"] = exp_name

        session.last_intent = plan.action.value if plan.action else "tool_executed"
        session.last_trace_id = trace_id
        session.turn_count += 1
        session.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
        await session.save()

        return AskResponse(
            trace_id=trace_id, action=plan.action, tool_name=plan.tool_name,
            planner_output=plan.model_dump(mode="json"),
            tool_output=tool_output, response=response,
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
