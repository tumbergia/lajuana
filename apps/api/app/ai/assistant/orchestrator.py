from __future__ import annotations

import time
from datetime import UTC, date, datetime, timezone
from uuid import uuid4

from app.ai.assistant.date_extractor import extract_date_from_message
from app.ai.assistant.date_guard import (
    InvalidRequestedDateError,
    validate_requested_date_for_business,
)
from app.ai.assistant.intent_router import detect_and_build_plan
from app.ai.assistant.planner import GeminiPlanner
from app.ai.assistant.policy import ToolPolicyEngine
from app.ai.assistant.response_composer import compose_tool_response
from app.ai.language.detector import detect_explicit_language_request
from app.ai.language.messages import t
from app.ai.mcp import registry
from app.ai.providers.contracts import LLMProviderError, LLMResourceExhausted, LLMUnavailable
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
from app.schemas.assistant_plan import AssistantAction, ToolArgs
from app.schemas.conversation_session import merge_slots

FIELD_LABELS: dict[str, tuple[str, str]] = {
    "experience_id": ("¿qué experiencia te interesa?", "which experience are you interested in?"),
    "requested_date": ("¿para qué fecha?", "what date?"),
    "participant_count": ("¿cuántas personas serían?", "how many people?"),
    "holder_phone": ("¿cuál es tu número de teléfono?", "what's your phone number?"),
    "holder_name": ("¿cuál es tu nombre completo?", "what's your full name?"),
    "holder_email": ("¿cuál es tu correo electrónico?", "what's your email?"),
    "schedule_id": ("¿para qué fecha?", "what date?"),
    "quote_snapshot": ("necesito primero consultar disponibilidad y precio", "I need to check availability and price first"),
    "conversation_id": None,
    "code": ("¿cuál es el código de tu reserva?", "what's your reservation code?"),
    "reservation_code": ("¿cuál es el código de tu reserva?", "what's your reservation code?"),
    "new_date": ("¿cuál es la nueva fecha?", "what's the new date?"),
    "new_participant_count": ("¿cuántas personas serían ahora?", "how many people now?"),
}

# Constants extracted for testability (W3.6, conv. #6: no lógica en métodos)
CONFIRM_WORDS: set[str] = {
    "sí", "si", "yes", "confirmar", "confirmo", "ok", "okay",
    "dale", "adelante", "hazlo", "ejecutar",
}
CANCEL_WORDS: set[str] = {
    "no", "cancelar", "cancelo", "nope", "abortar", "detener",
    "deten", "no quiero", "olvídalo",
}

REQUIRED_FIELDS_BY_TOOL: dict[str, list[str]] = {
    "check_availability": ["experience_id", "requested_date", "participant_count"],
    "create_reservation": ["experience_id", "requested_date", "participant_count"],
    "suggest_alternative_dates": ["experience_id"],
    "create_reservation_draft": [
        "experience_id",
        "participant_count",
        "holder_phone",
        "holder_name",
        "holder_email",
        "requested_date",
        "quote_snapshot",
    ],
    "get_reservation_public_summary": ["code", "holder_phone"],
    "get_reservation_status_by_phone": ["holder_phone"],
    "cancel_reservation": ["reservation_code", "holder_phone"],
    "update_reservation_date": ["reservation_code", "holder_phone", "new_date"],
    "update_reservation_participants": [
        "reservation_code", "holder_phone", "new_participant_count",
    ],
}

# Tools requiring user confirmation before execution
WRITE_TOOLS_REQUIRING_CONFIRMATION: set[str] = {
    "admin_deactivate_experience",
    "admin_deactivate_user",
    "admin_deactivate_schedule",
    "admin_deactivate_equine",
    "admin_close_service_execution",
    "admin_cancel_reservation",
    "admin_confirm_reservation",
    "admin_approve_payment",
    "admin_reject_payment_proof",
    "admin_unverify_payment_proof",
    "admin_unreject_payment_proof",
    "admin_update_equine_availability",
    "admin_update_reservation_rules",
    "admin_deactivate_provider",
    "admin_deactivate_saddle",
    "admin_delete_assignment",
    "admin_finalize_all_assignments",
}


def _fallback_tool_response(tool_output: dict) -> str:
    """Respuesta determinista cuando el composer LLM falla."""
    if tool_output.get("response"):
        return str(tool_output["response"])
    if tool_output.get("message"):
        return str(tool_output["message"])
    if tool_output.get("error"):
        return f"Error: {tool_output['error']}"
    parts: list[str] = []
    if "total" in tool_output:
        parts.append(f"Total: {tool_output['total']}")
    blocking = tool_output.get("blocking_reasons") or []
    if blocking and isinstance(blocking[0], dict):
        msg = blocking[0].get("message")
        if msg:
            parts.append(str(msg))
    return " ".join(parts) if parts else "Operación completada."


def _build_missing_fields_response(missing: list[str], language: str = "es") -> str:
    idx = 0 if language == "es" else 1
    labels = []
    for f in missing:
        entry = FIELD_LABELS.get(f)
        if entry is None:
            continue
        labels.append(entry[idx] if isinstance(entry, tuple) else entry)
    if not labels:
        return t("missing_fields_default", language)
    return t("missing_fields", language, fields=", ".join(labels))


class AssistantOrchestrator:
    def __init__(self, planner: GeminiPlanner | None = None) -> None:
        self._planner = planner or GeminiPlanner()
        self._policy = ToolPolicyEngine()

    async def ask(self, request: AskRequest) -> AskResponse:
        def _has_value(value: object) -> bool:
            if value is None or value == "":
                return False
            if isinstance(value, (dict, list, tuple, set)) and len(value) == 0:
                return False
            return True

        trace_id = request.trace_id or str(uuid4())
        conversation_id = request.conversation_id
        conversation_key = conversation_id or request.from_phone or trace_id
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
                {"conversation_id": conversation_key, "status": "responded"},
            )
            .sort("-created_at")
            .limit(8)
            .to_list()
        )
        # ── Política de idioma del bot ────────────────────────────────────
        # El idioma NUNCA se auto-detecta. El bot nace en español y sólo
        # cambia cuando el usuario lo pide explícitamente (override persistente)
        # o revierte a otro idioma con otra petición explícita. Ver ADR-0010.
        explicit_request = detect_explicit_language_request(request.message)
        if explicit_request:
            session.language_override = explicit_request
            session.language = explicit_request
            session.language_streak = 0
            session.language_streak_lang = None
            session.updated_at = datetime.now(UTC)
            await session.save()
        elif session.language_override:
            override = session.language_override
            if override not in ("es", "en"):
                override = "en"
            if session.language != override:
                session.language = override
                session.updated_at = datetime.now(UTC)
                await session.save()
        # Sin override → se conserva session.language (por defecto "es").
        # No hay auto-detección: si el usuario no pide explícitamente otro
        # idioma, el bot sigue respondiendo en el idioma efectivo actual.

        # Propagate from_phone as holder_phone only on client/guide channels
        phone = request.from_phone or getattr(session, "from_phone", None)
        if request.channel in {"whatsapp", "test", "mobile_api"}:
            if phone and "holder_phone" not in session.slot_values:
                session.slot_values["holder_phone"] = phone

        # Auto-clear stale pending tools (30min timeout)
        _pending_ts = session.slot_values.get("_pending_tool_timestamp")
        if _pending_ts:
            try:
                from datetime import timedelta
                if isinstance(_pending_ts, str):
                    _pending_ts = datetime.fromisoformat(_pending_ts)
                if (datetime.now(UTC) - _pending_ts) > timedelta(minutes=30):
                    session.slot_values.pop("_pending_tool_name", None)
                    session.slot_values.pop("_pending_tool_args", None)
                    session.slot_values.pop("_pending_tool_timestamp", None)
                    logger.info(
                        "[conversation_id=%s] Cleared stale pending tool (30min timeout)",
                        conversation_id,
                    )
            except Exception:
                pass

        # Handle pending tool confirmations
        pending_tool = session.slot_values.get("_pending_tool_name")
        if pending_tool and self._is_confirmation(request.message):
            # User confirmed, execute pending tool
            return await self._execute_pending_tool(
                request=request,
                session=session,
                trace_id=trace_id,
                conversation_key=conversation_key,
            )
        elif pending_tool and self._is_cancellation(request.message):
            # User cancelled, clear pending tool
            session.slot_values.pop("_pending_tool_name", None)
            session.slot_values.pop("_pending_tool_args", None)
            session.slot_values.pop("_pending_tool_timestamp", None)
            session.last_intent = "confirmation_cancelled"
            session.turn_count += 1
            await session.save()
            return AskResponse(
                trace_id=trace_id,
                action=AssistantAction.FINAL_RESPONSE,
                response=t("operation_cancelled", session.language),
            )

        turn = ConversationTurnDocument(
            trace_id=trace_id,
            channel=request.channel,
            conversation_id=conversation_key,
            user_message=request.message,
            from_phone=request.from_phone,
        )

        history_lines = []
        for turn_history in reversed(history_turns):
            if turn_history.user_message:
                history_lines.append(f"Usuario: {turn_history.user_message}")
            if turn_history.response_text:
                history_lines.append(f"Asistente: {turn_history.response_text}")

        conversation_history = "\n".join(history_lines)

        enriched_context = None
        if session.slot_values or conversation_history:
            parts = []
            if session.slot_values:
                # Never expose holder_name/holder_email in planner context so the bot
                # always asks for them explicitly on new reservations.
                safe_slots = {
                    k: v for k, v in session.slot_values.items()
                    if k not in ("holder_name", "holder_email")
                }
                if safe_slots:
                    parts.append(f"Datos de la sesión: {safe_slots}")
            if conversation_history:
                parts.append(f"Historial de la conversación:\n{conversation_history}")
            enriched_context = "\n\n".join(parts)

        # ── Intent router: pre-procesa mensajes comunes para forzar tool calls ──
        #     Sin pasar por el LLM que a veces ignora las instrucciones.
        forced_plan = detect_and_build_plan(
            user_message=request.message,
            conversation_context=enriched_context,
            session_slots=session.slot_values,
            channel=request.channel,
        )
        if forced_plan:
            logger.info(
                "[conversation_id=%s] Intent router matched | tool=%s | action=%s | audit=%s",
                conversation_id,
                forced_plan.tool_name,
                forced_plan.action.value,
                forced_plan.audit_summary,
            )
            plan = forced_plan
            token_usage = None
        else:
            logger.info(
                "[conversation_id=%s] Intent router no match, falling back to LLM",
                conversation_id,
            )
            try:
                token_usage: dict[str, int] | None = None
                plan = await self._planner.plan(
                    user_message=request.message,
                    channel=request.channel,
                    conversation_context=enriched_context,
                    conversation_id=conversation_id,
                    language=session.language,
                )
                token_usage = getattr(self._planner, "last_token_usage", None)
            except (GeminiResourceExhausted, LLMResourceExhausted):
                return AskResponse(
                    trace_id=trace_id,
                    action=AssistantAction.FINAL_RESPONSE,
                    planner_output={},
                    tool_output={},
                    response=t("resource_exhausted", session.language),
                )
            except (GeminiModelUnavailable, LLMUnavailable):
                return AskResponse(
                    trace_id=trace_id,
                    action=AssistantAction.HUMAN_HANDOFF,
                    planner_output={},
                    tool_output={},
                    response=t("model_unavailable", session.language),
                )
            except (GeminiProviderError, LLMProviderError):
                return AskResponse(
                    trace_id=trace_id,
                    action=AssistantAction.HUMAN_HANDOFF,
                    planner_output={},
                    tool_output={},
                    response=t("provider_error", session.language),
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
                plan.response = t("invalid_date", session.language)
                plan.arguments.requested_date = None

        turn.planner_output = plan.model_dump(mode="json")
        await turn.save()

        if conversation_id:
            session.slot_values["conversation_id"] = conversation_id

        # Save all non-null arguments from planner to session slots
        if plan.arguments:
            for key, value in plan.arguments.model_dump(exclude_none=True).items():
                if _has_value(value):
                    session.slot_values[key] = value

        # Session merge: fill null plan args from session slots
        # REQUIRED_FIELDS_BY_TOOL definido a nivel módulo (ver arriba)
        if (
            plan.action in {AssistantAction.TOOL_CALL, AssistantAction.ASK_CLARIFYING_QUESTION}
            and plan.arguments
        ):
            required_fields = REQUIRED_FIELDS_BY_TOOL.get(plan.tool_name or "", [])
            if required_fields:
                plan_args = plan.arguments.model_dump()
                # For new reservations, never auto-fill name/email from session slots
                # so the bot always asks the user explicitly.
                slots_for_merge = dict(session.slot_values)
                if plan.tool_name == "create_reservation_draft":
                    slots_for_merge.pop("holder_name", None)
                    slots_for_merge.pop("holder_email", None)
                merge = merge_slots(
                    session_slots=slots_for_merge,
                    plan_args=plan_args,
                    required_fields=required_fields,
                )
                # Always apply merged args and check for missing required fields
                valid_keys = ToolArgs.model_fields.keys()
                for key, value in merge.merged.items():
                    if key in valid_keys:
                        setattr(plan.arguments, key, value)
                if not merge.still_missing:
                    plan.action = AssistantAction.TOOL_CALL
                    plan.missing_fields = []
                else:
                    plan.action = AssistantAction.ASK_CLARIFYING_QUESTION
                    plan.missing_fields = merge.still_missing
                    plan.response = _build_missing_fields_response(merge.still_missing, session.language)

        if plan.action in {
            AssistantAction.FINAL_RESPONSE,
            AssistantAction.ASK_CLARIFYING_QUESTION,
            AssistantAction.HUMAN_HANDOFF,
        }:
            logger.info(
                "[conversation_id=%s] Plan decision: no tool call | action=%s | missing=%s",
                conversation_id,
                plan.action.value,
                plan.missing_fields,
            )
            response = (
                plan.response
                or _build_missing_fields_response(plan.missing_fields, session.language)
                or t("needs_more_info", session.language)
            )
            if plan.action == AssistantAction.ASK_CLARIFYING_QUESTION:
                session.pending_fields = plan.missing_fields
            session.last_intent = plan.action.value
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = datetime.now(timezone.utc)
            await session.save()
            return AskResponse(
                trace_id=trace_id,
                action=plan.action,
                planner_output=plan.model_dump(mode="json"),
                tool_output={},
                response=response,
            )

        if plan.arguments:
            for key, value in plan.arguments.model_dump(exclude_none=True).items():
                if _has_value(value):
                    session.slot_values[key] = value
        session.pending_fields = []

        policy_decision = self._policy.validate(plan, channel=request.channel)
        if not policy_decision.allowed:
            response = (
                plan.response
                or _build_missing_fields_response(plan.missing_fields, session.language)
                or t("policy_blocked", session.language)
            )
            session.last_intent = "blocked_by_policy"
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = datetime.now(timezone.utc)
            await session.save()
            return AskResponse(
                trace_id=trace_id,
                action=AssistantAction.ASK_CLARIFYING_QUESTION,
                tool_name=plan.tool_name,
                planner_output=plan.model_dump(mode="json"),
                tool_output={},
                response=response,
            )

        # Confirmación pre-ejecución (constante module-level, ver arriba)
        if plan.tool_name in WRITE_TOOLS_REQUIRING_CONFIRMATION:
            confirm_msg = t("tool_confirmation", session.language, tool_name=plan.tool_name or "")
            session.slot_values["_pending_tool_name"] = plan.tool_name
            session.slot_values["_pending_tool_args"] = plan.arguments.model_dump(exclude_none=True) if plan.arguments else {}
            session.slot_values["_pending_tool_timestamp"] = datetime.now(UTC).isoformat()
            session.last_intent = "pending_confirmation"
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = datetime.now(timezone.utc)
            await session.save()
            return AskResponse(
                trace_id=trace_id,
                action=AssistantAction.ASK_CLARIFYING_QUESTION,
                tool_name=plan.tool_name,
                planner_output=plan.model_dump(mode="json"),
                tool_output={},
                response=confirm_msg,
            )

        logger.info(
            "[conversation_id=%s] Executing tool | tool=%s | args=%s",
            conversation_id,
            plan.tool_name,
            {k: v for k, v in (plan.arguments.model_dump(exclude_none=True) if plan.arguments else {}).items()
             if k not in ("quote_snapshot",)},
        )

        started = time.perf_counter()
        error_code: str | None = None
        tool_output: dict = {}

        try:
            tool_kwargs = plan.arguments.model_dump(exclude_none=True)
            tool_output = await registry.call(
                plan.tool_name or "",
                conversation_id_for_log=conversation_id,
                trace_id=trace_id,
                conversation_turn_id=request.conversation_turn_id or str(uuid4()),
                **tool_kwargs,
            )
            status = "success"
        except Exception as exc:
            error_code = "tool.execution_failed"
            status = "error"
            tool_output = {"error": str(exc), "trace_id": trace_id}

        latency_ms = int((time.perf_counter() - started) * 1000)

        logger.info(
            "[conversation_id=%s] Tool result | tool=%s | status=%s | latency_ms=%d | output_keys=%s",
            conversation_id,
            plan.tool_name,
            status,
            latency_ms,
            list(tool_output.keys())[:10],
        )

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

        # Tools que entregan un `response` literal en su output y NO deben pasar
        # por compose_tool_response (evita que el LLM mienta, p.ej. "te envié
        # los detalles al correo" cuando no hay sistema de email). Incluye
        # create_reservation_draft (pasos + banco + ubicación) y
        # get_payment_instructions (medios de pago por WhatsApp) y
        # attach_payment_proof_to_reservation (confirmación de comprobante).
        LITERAL_RESPONSE_TOOLS: set[str] = {
            "create_reservation_draft",
            "get_payment_instructions",
            "attach_payment_proof_to_reservation",
        }
        if plan.tool_name in LITERAL_RESPONSE_TOOLS and tool_output.get("response"):
            response = tool_output["response"]
        else:
            try:
                response = await compose_tool_response(
                    user_message=request.message,
                    plan=plan,
                    tool_output=tool_output,
                    conversation_id=conversation_id,
                    channel=request.channel,
                    language=session.language,
                )
            except (
                GeminiProviderError,
                GeminiResourceExhausted,
                GeminiModelUnavailable,
                LLMProviderError,
            ) as exc:
                logger.warning(
                    "[conversation_id=%s] Compose fallback | tool=%s | error=%s",
                    conversation_id,
                    plan.tool_name,
                    exc,
                )
                response = _fallback_tool_response(tool_output)

        if (
            plan.tool_name == "suggest_alternative_dates"
            and tool_output.get("total", 0) == 0
            and not tool_output.get("blocking_reasons")
        ):
            plan.action = AssistantAction.HUMAN_HANDOFF
            response = t("no_alternative_dates", session.language)

        turn.tool_output = tool_output
        turn.response_text = response
        turn.status = "completed" if not error_code else "tool_error"
        turn.error_code = error_code
        await turn.save()

        # Propagate resolved fields from tool output to session slots
        if tool_output:
            exp_id = tool_output.get("experience_id")
            exp_name = tool_output.get("experience_name")
            if exp_id:
                session.slot_values["experience_id"] = exp_id
            if exp_name:
                session.slot_values["experience_name"] = exp_name
            sched_id = tool_output.get("schedule_id")
            if sched_id:
                session.slot_values["schedule_id"] = sched_id
            qs = tool_output.get("quote_snapshot")
            if qs:
                session.slot_values["quote_snapshot"] = qs
            code = tool_output.get("code")
            if code:
                session.slot_values["reservation_code"] = code

        session.last_intent = plan.action.value if plan.action else "tool_executed"
        session.last_trace_id = trace_id
        session.turn_count += 1
        session.updated_at = datetime.now(timezone.utc)
        await session.save()

        return AskResponse(
            trace_id=trace_id,
            action=plan.action,
            tool_name=plan.tool_name,
            planner_output=plan.model_dump(mode="json"),
            tool_output=tool_output,
            response=response,
            token_usage=token_usage,
        )

    @staticmethod
    def _is_confirmation(message: str) -> bool:
        msg_lower = message.lower().strip()
        if msg_lower in CONFIRM_WORDS:
            return True
        for phrase in CONFIRM_WORDS:
            words = phrase.split()
            pattern = r'\b' + r'\s+'.join(re.escape(w) for w in words) + r'\b'
            if re.search(pattern, msg_lower):
                return True
        return False

    @staticmethod
    def _is_cancellation(message: str) -> bool:
        msg_lower = message.lower().strip()
        if msg_lower in CANCEL_WORDS:
            return True
        for phrase in CANCEL_WORDS:
            words = phrase.split()
            pattern = r'\b' + r'\s+'.join(re.escape(w) for w in words) + r'\b'
            if re.search(pattern, msg_lower):
                return True
        return False

    async def _execute_pending_tool(
        self,
        *,
        request: AskRequest,
        session: ConversationSessionDocument,
        trace_id: str,
        conversation_key: str,
    ) -> AskResponse:
        """Ejecuta una tool pendiente de confirmación."""
        from app.ai.language.messages import t as _t
        from app.ai.mcp.registry import registry
        from app.documents.tool_call_log_document import ToolCallLogDocument

        lang = session.language
        pending_tool_name = session.slot_values.pop("_pending_tool_name", None)
        pending_args = session.slot_values.pop("_pending_tool_args", {})
        pending_args["conversation_id_for_log"] = conversation_key
        pending_args["trace_id"] = trace_id
        pending_args["conversation_turn_id"] = str(uuid4())

        started = time.perf_counter()
        error_code: str | None = None
        tool_output: dict = {}

        try:
            tool_output = await registry.call(pending_tool_name, **pending_args)
            status = "success"
            if (
                pending_tool_name
                in {"create_reservation_draft", "get_payment_instructions", "attach_payment_proof_to_reservation"}
                and tool_output.get("response")
            ):
                response = tool_output["response"]
            else:
                response = tool_output.get("response", _t("tool_success", lang, tool_name=pending_tool_name or ""))
        except Exception as exc:
            error_code = "tool.execution_failed"
            status = "error"
            tool_output = {"error": str(exc), "trace_id": trace_id}
            response = _t("provider_error", lang)

        latency_ms = int((time.perf_counter() - started) * 1000)

        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=pending_args.get("conversation_turn_id"),
            tool_name=pending_tool_name or "unknown",
            input=pending_args,
            output=tool_output,
            status=status,
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()

        session.last_intent = "tool_executed_after_confirmation"
        session.last_trace_id = trace_id
        session.turn_count += 1
        session.updated_at = datetime.now(timezone.utc)
        await session.save()

        return AskResponse(
            trace_id=trace_id,
            action=AssistantAction.TOOL_CALL,
            tool_name=pending_tool_name,
            planner_output={},
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
            {"conversation_key": conversation_key, "status": "active"},
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
