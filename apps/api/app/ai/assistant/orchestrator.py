from __future__ import annotations

import re
import time
from datetime import UTC, date, datetime
from typing import Any
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
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs
from app.schemas.conversation_session import merge_slots
from app.services.equine_service import EquineService
from app.services.experience_service import ExperienceService
from app.services.provider_service import ProviderService
from app.services.saddle_service import SaddleService
from app.services.user_service import UserService

FIELD_LABELS: dict[str, tuple[str, str]] = {
    "experience_id": ("¿qué experiencia te interesa?", "which experience are you interested in?"),
    "requested_date": ("¿para qué fecha?", "what date?"),
    "participant_count": ("¿cuántas personas serían?", "how many people?"),
    "holder_phone": ("¿cuál es tu número de teléfono?", "what's your phone number?"),
    "holder_name": ("¿cuál es tu nombre completo?", "what's your full name?"),
    "holder_email": ("¿cuál es tu correo electrónico?", "what's your email?"),
    "schedule_id": ("¿para qué fecha?", "what date?"),
    "quote_snapshot": (
        "necesito primero consultar disponibilidad y precio",
        "I need to check availability and price first",
    ),
    "conversation_id": None,
    "code": ("¿cuál es el código de tu reserva?", "what's your reservation code?"),
    "reservation_code": ("¿cuál es el código de tu reserva?", "what's your reservation code?"),
    "new_date": ("¿cuál es la nueva fecha?", "what's the new date?"),
    "new_participant_count": ("¿cuántas personas serían ahora?", "how many people now?"),
}

# Constants extracted for testability (W3.6, conv. #6: no lógica en métodos)
CONFIRM_WORDS: set[str] = {
    "sí",
    "si",
    "yes",
    "confirmar",
    "confirmo",
    "ok",
    "okay",
    "dale",
    "adelante",
    "hazlo",
    "ejecutar",
}
CANCEL_WORDS: set[str] = {
    "no",
    "cancelar",
    "cancelo",
    "nope",
    "abortar",
    "detener",
    "deten",
    "no quiero",
    "olvídalo",
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
        "reservation_code",
        "holder_phone",
        "new_participant_count",
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
    blocking_message = _extract_blocking_reason_message(tool_output)
    if blocking_message:
        return blocking_message
    if tool_output.get("response"):
        return str(tool_output["response"])
    if tool_output.get("message"):
        return str(tool_output["message"])
    if tool_output.get("error"):
        return f"Error: {tool_output['error']}"
    analytics = _analytics_summary_response(tool_output)
    if analytics:
        return analytics
    parts: list[str] = []
    if "total" in tool_output:
        parts.append(f"Total: {tool_output['total']}")
    blocking = tool_output.get("blocking_reasons") or []
    if blocking and isinstance(blocking[0], dict):
        msg = blocking[0].get("message")
        if msg:
            parts.append(str(msg))
    return " ".join(parts) if parts else "Operación completada."


def _extract_blocking_reason_message(tool_output: dict) -> str | None:
    blocking = tool_output.get("blocking_reasons") or []
    for item in blocking:
        if isinstance(item, dict) and item.get("message"):
            return str(item["message"])
        if isinstance(item, str) and item.strip():
            return item
    return None


def _extract_tool_result_message(tool_name: str | None, tool_output: dict) -> str:
    literal_response_tools: set[str] = {
        "create_reservation_draft",
        "get_payment_instructions",
        "attach_payment_proof_to_reservation",
    }
    analytics_summary = (
        _analytics_summary_response(tool_output) if tool_name in ANALYTICS_LITERAL_TOOLS else None
    )
    blocking_message = _extract_blocking_reason_message(tool_output)
    if blocking_message:
        return blocking_message
    if tool_name in literal_response_tools and tool_output.get("response"):
        return str(tool_output["response"])
    if tool_output.get("response"):
        return str(tool_output["response"])
    if tool_output.get("message"):
        return str(tool_output["message"])
    if analytics_summary:
        return analytics_summary
    return _fallback_tool_response(tool_output)


def _humanize_tool_name(tool_name: str | None) -> str:
    if not tool_name:
        return "esta acción"
    text = tool_name
    for prefix in ("admin_", "guide_"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    replacements = {
        "deactivate": "desactivar",
        "update": "actualizar",
        "create": "crear",
        "confirm": "confirmar",
        "cancel": "cancelar",
        "approve": "aprobar",
        "reject": "rechazar",
        "unverify": "revertir verificación de",
        "unreject": "revertir rechazo de",
        "close": "cerrar",
        "finalize": "finalizar",
        "list": "listar",
        "get": "ver",
        "experience": "experiencia",
        "user": "usuario",
        "reservation": "reserva",
        "payment": "pago",
        "proof": "comprobante",
        "equine": "equino",
        "participant": "participante",
        "provider": "proveedor",
        "saddle": "silla",
        "assignment": "asignación",
        "event": "evento",
        "schedule": "horario",
        "rules": "reglas",
        "service": "servicio",
    }
    words = [replacements.get(word, word) for word in text.split("_")]
    return " ".join(words)


def _format_cop(amount: Any) -> str:
    try:
        numeric = float(amount)
    except (TypeError, ValueError):
        numeric = 0.0
    text = f"{int(round(numeric)):,}".replace(",", ".")
    return f"${text} COP"


def _analytics_summary_response(tool_output: dict) -> str | None:
    """Resumen corto y determinista para tools de analítica con chart."""
    tool_name = tool_output.get("tool_name")
    blocking = tool_output.get("blocking_reasons") or []
    if blocking:
        first = blocking[0] if isinstance(blocking[0], dict) else {}
        msg = first.get("message") if isinstance(first, dict) else None
        return str(msg) if msg else None

    period = ""
    date_from = tool_output.get("date_from")
    date_to = tool_output.get("date_to")
    if date_from and date_to:
        period = f" del {date_from} al {date_to}"
    elif date_from:
        period = f" desde {date_from}"

    if tool_name == "admin_get_sales_summary":
        revenue = tool_output.get("total_revenue") or 0
        total = tool_output.get("total_reservations") or 0
        return (
            f"Ingresos comprometidos{period}: {_format_cop(revenue)}. "
            f"{total} reservas en el periodo. Te muestro la gráfica."
        )
    if tool_name == "admin_get_channel_performance":
        total = tool_output.get("total") or 0
        channels = tool_output.get("channels") or []
        top = ""
        if channels and isinstance(channels[0], dict):
            top = f" El canal líder es {channels[0].get('channel', '')}."
        return f"Origen de {total} reservas{period}.{top} Te muestro la gráfica."
    if tool_name == "admin_get_reservation_funnel":
        start = tool_output.get("total_start") or 0
        converted = tool_output.get("total_converted") or 0
        return (
            f"Embudo{period}: {start} reservas al inicio, "
            f"{converted} confirmadas/completadas. Te muestro la gráfica."
        )
    if tool_name == "admin_get_occupancy_report":
        avg = tool_output.get("avg_occupancy_pct") or 0
        return f"Ocupación promedio{period}: {avg}%. Te muestro la gráfica."
    if tool_name == "admin_get_equine_workload_report":
        total = tool_output.get("total_assignments") or 0
        equines = tool_output.get("total_equines") or 0
        return (
            f"Carga equina{period}: {total} asignaciones en {equines} equinos. "
            "Te muestro la gráfica."
        )
    return None


ANALYTICS_LITERAL_TOOLS: set[str] = {
    "admin_get_sales_summary",
    "admin_get_channel_performance",
    "admin_get_reservation_funnel",
    "admin_get_occupancy_report",
    "admin_get_equine_workload_report",
}

_OBJECT_ID_RE = re.compile(r"\b[a-f0-9]{24}\b", flags=re.IGNORECASE)

_ADMIN_ID_ALIASES: dict[str, tuple[str, ...]] = {
    "admin_get_reservation_detail": ("reservation_id", "code", "reservation_code"),
    "admin_confirm_reservation": ("reservation_id", "reservation_code", "code"),
    "admin_cancel_reservation": ("reservation_id", "reservation_code", "code"),
    "admin_close_service_execution": ("reservation_id", "reservation_code", "code"),
    "admin_get_assignment_board": ("reservation_id", "reservation_code"),
    "admin_list_available_saddles_for_reservation": ("reservation_id",),
    "admin_update_user": ("user_id",),
    "admin_deactivate_user": ("user_id",),
    "admin_get_equine": ("equine_id",),
    "admin_update_equine": ("equine_id",),
    "admin_deactivate_equine": ("equine_id",),
    "admin_create_equine_event": ("equine_id",),
    "admin_list_equine_events": ("equine_id",),
    "admin_update_equine_event": ("event_id",),
    "admin_get_participant": ("participant_id",),
    "admin_update_participant": ("participant_id",),
    "admin_get_provider": ("provider_id",),
    "admin_update_provider": ("provider_id",),
    "admin_deactivate_provider": ("provider_id",),
    "admin_get_saddle": ("saddle_id",),
    "admin_update_saddle": ("saddle_id",),
    "admin_deactivate_saddle": ("saddle_id",),
    "admin_update_assignment": ("assignment_id",),
    "admin_delete_assignment": ("assignment_id",),
    "admin_finalize_assignment": ("assignment_id",),
    "admin_get_payment_proof": ("payment_proof_id",),
    "admin_approve_payment": ("payment_proof_id",),
    "admin_reject_payment_proof": ("payment_proof_id",),
    "admin_unverify_payment_proof": ("payment_proof_id",),
    "admin_unreject_payment_proof": ("payment_proof_id",),
}


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


def _extract_explicit_id(message: str, field_name: str) -> str | None:
    pattern = rf"\b{re.escape(field_name)}\b\s*[:=]?\s*([A-Za-z0-9_-]{{6,}})"
    match = re.search(pattern, message, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _extract_explicit_arguments(message: str) -> dict[str, Any]:
    pattern = re.compile(r"\b([a-z_]+)\s*=\s*(.+?)(?=(?:\s*[;,]\s*[a-z_]+\s*=)|$)", re.IGNORECASE)
    extracted: dict[str, Any] = {}
    for key, raw_value in pattern.findall(message):
        value = raw_value.strip().strip("'\"")
        lowered = value.lower()
        if lowered in {"true", "false"}:
            extracted[key] = lowered == "true"
            continue
        if re.fullmatch(r"-?\d+", value):
            extracted[key] = int(value)
            continue
        extracted[key] = value
    return extracted


def _normalize_admin_plan_arguments(plan: AssistantPlan, message: str) -> None:
    if not plan.tool_name or not plan.arguments:
        return
    explicit_args = _extract_explicit_arguments(message)
    for key, value in explicit_args.items():
        if getattr(plan.arguments, key, None) in {None, ""}:
            setattr(plan.arguments, key, value)

    aliases = _ADMIN_ID_ALIASES.get(plan.tool_name)
    if not aliases:
        return

    args = plan.arguments
    for field_name in aliases:
        explicit = _extract_explicit_id(message, field_name)
        if explicit and not getattr(args, field_name, None):
            setattr(args, field_name, explicit)

    if plan.tool_name == "admin_get_reservation_detail":
        reservation_id = getattr(args, "reservation_id", None)
        reservation_code = getattr(args, "reservation_code", None)
        code = getattr(args, "code", None)
        if not reservation_id:
            for candidate in (reservation_code, code):
                if isinstance(candidate, str) and _OBJECT_ID_RE.fullmatch(candidate):
                    args.reservation_id = candidate
                    break
        if args.reservation_id and isinstance(code, str) and _OBJECT_ID_RE.fullmatch(code):
            args.code = None
        return

    primary_field = aliases[0]
    if getattr(args, primary_field, None):
        return

    for alias in aliases[1:]:
        candidate = getattr(args, alias, None)
        if isinstance(candidate, str) and _OBJECT_ID_RE.fullmatch(candidate):
            setattr(args, primary_field, candidate)
            break


def _format_admin_user_match_summary(matches: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for match in matches[:5]:
        full_name = match.get("full_name")
        email = match.get("email")
        if full_name and email:
            parts.append(f"{full_name} <{email}>")
    return ", ".join(parts)


def _format_admin_reference_match_summary(matches: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for match in matches[:5]:
        label = match.get("label")
        if isinstance(label, str) and label.strip():
            parts.append(label)
            continue
        full_name = match.get("full_name")
        email = match.get("email")
        if full_name and email:
            parts.append(f"{full_name} <{email}>")
            continue
        name = match.get("name")
        code = match.get("code")
        slug = match.get("slug")
        if code and name:
            parts.append(f"{code} ({name})")
        elif name and slug:
            parts.append(f"{name} ({slug})")
        elif name:
            parts.append(str(name))
        elif code:
            parts.append(str(code))
    return ", ".join(parts)


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
                    k: v
                    for k, v in session.slot_values.items()
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
                    plan.response = _build_missing_fields_response(
                        merge.still_missing, session.language
                    )

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
            session.updated_at = datetime.now(UTC)
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

        _normalize_admin_plan_arguments(plan, request.message)

        if await self._resolve_admin_reference(plan, session.language):
            session.pending_fields = plan.missing_fields
            session.last_intent = plan.action.value
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = datetime.now(UTC)
            await session.save()
            return AskResponse(
                trace_id=trace_id,
                action=plan.action,
                tool_name=plan.tool_name,
                planner_output=plan.model_dump(mode="json"),
                tool_output={},
                response=plan.response or t("needs_more_info", session.language),
            )

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
            session.updated_at = datetime.now(UTC)
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
            confirm_msg = t(
                "tool_confirmation",
                session.language,
                tool_name=_humanize_tool_name(plan.tool_name),
            )
            session.slot_values["_pending_tool_name"] = plan.tool_name
            session.slot_values["_pending_tool_args"] = (
                plan.arguments.model_dump(exclude_none=True) if plan.arguments else {}
            )
            session.slot_values["_pending_tool_timestamp"] = datetime.now(UTC).isoformat()
            session.last_intent = "pending_confirmation"
            session.last_trace_id = trace_id
            session.turn_count += 1
            session.updated_at = datetime.now(UTC)
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
            {
                k: v
                for k, v in (
                    plan.arguments.model_dump(exclude_none=True) if plan.arguments else {}
                ).items()
                if k not in ("quote_snapshot",)
            },
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
        deterministic_response = _extract_tool_result_message(plan.tool_name, tool_output)
        if plan.tool_name in ANALYTICS_LITERAL_TOOLS or plan.tool_name in {
            "create_reservation_draft",
            "get_payment_instructions",
            "attach_payment_proof_to_reservation",
        }:
            response = deterministic_response
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
                response = deterministic_response

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
        session.updated_at = datetime.now(UTC)
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
            pattern = r"\b" + r"\s+".join(re.escape(w) for w in words) + r"\b"
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
            pattern = r"\b" + r"\s+".join(re.escape(w) for w in words) + r"\b"
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
            response = _extract_tool_result_message(pending_tool_name, tool_output)
        except Exception as exc:
            error_code = "tool.execution_failed"
            status = "error"
            tool_output = {"error": str(exc), "trace_id": trace_id}
            response = _extract_tool_result_message(pending_tool_name, tool_output)

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
        session.updated_at = datetime.now(UTC)
        await session.save()

        return AskResponse(
            trace_id=trace_id,
            action=AssistantAction.TOOL_CALL,
            tool_name=pending_tool_name,
            planner_output={},
            tool_output=tool_output,
            response=response,
        )

    async def _resolve_admin_reference(self, plan: AssistantPlan, language: str) -> bool:
        configs: dict[str, dict[str, Any]] = {
            "admin_deactivate_user": {
                "id_field": "user_id",
                "resolver": UserService().resolve_user_reference,
                "entity": "usuario" if language == "es" else "user",
                "exact_hint": "correo" if language == "es" else "email",
                "use_user_messages": True,
            },
            "admin_update_user": {
                "id_field": "user_id",
                "resolver": UserService().resolve_user_reference,
                "entity": "usuario" if language == "es" else "user",
                "exact_hint": "correo" if language == "es" else "email",
                "use_user_messages": True,
            },
            "admin_deactivate_provider": {
                "id_field": "provider_id",
                "resolver": ProviderService().resolve_provider_reference,
                "entity": "proveedor" if language == "es" else "provider",
                "exact_hint": "nombre o slug" if language == "es" else "name or slug",
            },
            "admin_deactivate_equine": {
                "id_field": "equine_id",
                "resolver": EquineService().resolve_equine_reference,
                "entity": "equino" if language == "es" else "equine",
                "exact_hint": "nombre" if language == "es" else "name",
            },
            "admin_deactivate_saddle": {
                "id_field": "saddle_id",
                "resolver": SaddleService().resolve_saddle_reference,
                "entity": "silla" if language == "es" else "saddle",
                "exact_hint": "código o nombre" if language == "es" else "code or name",
            },
            "admin_deactivate_experience": {
                "id_field": "experience_id",
                "resolver": ExperienceService().resolve_experience_reference,
                "entity": "experiencia" if language == "es" else "experience",
                "exact_hint": "nombre o slug" if language == "es" else "name or slug",
            },
        }

        config = configs.get(plan.tool_name or "")
        if not config:
            return False
        if not plan.arguments or getattr(plan.arguments, config["id_field"], None):
            return False

        reference = getattr(plan.arguments, "q", None)
        if not isinstance(reference, str) or not reference.strip():
            return False

        resolution = await config["resolver"](reference)
        if resolution.get("status") == "resolved":
            setattr(plan.arguments, config["id_field"], str(resolution[config["id_field"]]))
            return False

        plan.action = AssistantAction.ASK_CLARIFYING_QUESTION
        plan.missing_fields = [config["id_field"]]
        if config.get("use_user_messages") and resolution.get("status") == "ambiguous":
            plan.response = t(
                "admin_user_ambiguous",
                language,
                reference=str(resolution.get("reference", reference)),
                matches=_format_admin_user_match_summary(resolution.get("matches", [])),
            )
        elif config.get("use_user_messages"):
            plan.response = t(
                "admin_user_not_found",
                language,
                reference=str(resolution.get("reference", reference)),
            )
        elif resolution.get("matches"):
            plan.response = t(
                "admin_entity_ambiguous",
                language,
                entity=str(config["entity"]),
                reference=str(resolution.get("reference", reference)),
                matches=_format_admin_reference_match_summary(resolution.get("matches", [])),
                id_field=str(config["id_field"]),
            )
        else:
            plan.response = t(
                "admin_entity_not_found",
                language,
                entity=str(config["entity"]),
                reference=str(resolution.get("reference", reference)),
                id_field=str(config["id_field"]),
                exact_hint=str(config["exact_hint"]),
            )
        return True

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
