from __future__ import annotations

import re
from typing import Any

from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs

_EXPERIENCE_KEYWORDS = [
    r"\b(listame|lista|muestra|dime|enseñame|enseñame|cuales|que.ofrecen|que.hay|que.tienen)\b",
    r"\b(experiencias|actividades|planes|recorridos|catalogo|opciones|servicios)\b",
]

_DETAIL_KEYWORDS = [
    r"\b(detalles?|descripcion|informacion|en.que.consiste|como.es|que.incluye|que.se.hace)\b",
    r"\b(hablame|cuentame|dime.mas|cuentame|explicame|mas.sobre)\b",
]

_PRICE_KEYWORDS = [
    r"\b(cuanto.vale?|cuanto.cuesta|precio|tarifa|cotizame|cotizacion|valor|cuanto.sale)\b",
]

_AVAILABILITY_KEYWORDS = [
    r"\b(hay.cupo|disponibilidad|se.puede|hay.lugar|cabemos|caben|cupo.disponible)\b",
]

_SESSION_KEYWORDS = [
    r"\b(en.que.va|estado|como.va.mi|status.de.mi|situacion.de.mi)\b",
]

# Consulta de medios/detalles de pago. NO incluye peticiones explicitas de
# link Bold (esas van a handoff a admin via _BOLD_KEYWORDS).
_PAYMENT_INFO_KEYWORDS = [
    r"\b(detalles?.del.?pago|detalles?.para.?pagar|como.?pago|como.?realizo.?el.?pago)\b",
    r"\b(medios.?de.?pago|formas.?de.?pago|opciones.?de.?pago|numero.?de.?cuenta)\b",
    r"\b(informacion.?del.?pago|informacion.?de.?pago|datos.?de.?pago|donde.?pago)\b",
    r"\b(cuenta.?bancolombia|bancolombia|cuenta.?de.?ahorros?)\b",
]

_BOLD_KEYWORDS = [
    r"\bbold\b",
    r"\blink.de.pago.bold\b",
    r"\bpago.bold\b",
    r"\blink.bold\b",
    r"\b(link|pagar|pago).*(bold)\b",
    r"\bquiero.*link\b",
]


def _extract_experience_name(text: str) -> str | None:
    cleaned = text.strip()
    # Remove leading intent phrases
    for prefix in [
        r"dame\s+(los\s+)?(detalles?\s+)?(de\s+)?(la\s+)?(para\s+)?(esta\s+)?(de\s+)?",
        r"en\s+que\s+consiste\s+",
        r"cuentame\s+de\s+",
        r"hablame\s+de\s+",
        r"dime\s+mas\s+(sobre|de)\s+",
    ]:
        cleaned = re.sub(f"^{prefix}", "", cleaned, flags=re.IGNORECASE).strip()
    # Strip leading articles
    cleaned = re.sub(r"^(el|la|los|las|un|una)\s+", "", cleaned, flags=re.IGNORECASE).strip()
    if len(cleaned) > 2 and not any(
        w in cleaned.lower() for w in ["experiencias", "actividades", "planes", "precio", "tienes", "ofrecen"]
    ):
        return cleaned
    return None


def _extract_participant_count(text: str) -> int | None:
    m = re.search(r"(\d+)\s*(?:personas?|participantes?|pax|adultos?|niños?)", text.lower())
    if m:
        return int(m.group(1))
    m = re.search(r"(?:para|somos?|seriamos?)\s*(\d+)", text.lower())
    if m:
        return int(m.group(1))
    return None


def _extract_date(text: str) -> str | None:
    from app.ai.assistant.date_extractor import extract_date_from_message
    try:
        return extract_date_from_message(text)
    except Exception:
        return None


def _matches_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def detect_and_build_plan(
    user_message: str,
    conversation_context: str | None = None,
    session_slots: dict[str, Any] | None = None,
) -> AssistantPlan | None:
    msg_lower = user_message.lower().strip()

    exp_name = _extract_experience_name(user_message)

    # ── Bold payment request → human review (flag al admin) ──
    # Check primero: el usuario pide el link de pago Bold, se levanta flag para
    # que un admin tome la conversación, genere el link y continúe. El bot no
    # lo hace solo. Prioridad alta para no mezclar con "detalles del pago".
    if _matches_any(msg_lower, _BOLD_KEYWORDS):
        return AssistantPlan(
            action=AssistantAction.HUMAN_HANDOFF,
            confidence=0.85,
            tool_name="request_human_review",
            arguments=ToolArgs(bold_requested=True),
            user_goal="El usuario solicita link de pago Bold.",
            audit_summary=(
                "Intent detectado: solicitud de pago Bold, se requiere "
                "intervención humana del admin para generar el link."
            ),
        )

    # ── Medios/detalles de pago → tool get_payment_instructions ──
    # Antes que _DETAIL_KEYWORDS para no confundir "detalles del pago" con
    # "detalles de una experiencia".
    if _matches_any(msg_lower, _PAYMENT_INFO_KEYWORDS):
        bold = bool(re.search(r"\bbold\b", msg_lower))
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="get_payment_instructions",
            arguments=ToolArgs(bold_requested=bold),
            user_goal="El usuario quiere conocer los medios de pago por WhatsApp.",
            audit_summary="Intent detectado: consulta de medios de pago.",
        )

    # ── Experience details (check before list to avoid "dime" matching list) ──
    if _matches_any(msg_lower, _DETAIL_KEYWORDS):
        args = ToolArgs()
        if exp_name:
            args.experience_query = exp_name
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.92,
            tool_name="get_experience_detail",
            arguments=args,
            user_goal=f"El usuario quiere detalles de una experiencia{' (' + exp_name + ')' if exp_name else ''}.",
            audit_summary="Intent detectado: consultar detalle de experiencia.",
        )

    # ── Price / quote ──
    if _matches_any(msg_lower, _PRICE_KEYWORDS):
        args = ToolArgs()
        if exp_name:
            args.experience_query = exp_name
        participants = _extract_participant_count(msg_lower)
        if participants:
            args.participant_count = participants
        date_str = _extract_date(msg_lower)
        if date_str:
            args.requested_date = date_str
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="quote_experience",
            arguments=args,
            user_goal="El usuario quiere saber el precio de una experiencia.",
            audit_summary="Intent detectado: cotizar experiencia.",
        )

    # ── Availability ──
    if _matches_any(msg_lower, _AVAILABILITY_KEYWORDS):
        args = ToolArgs()
        if exp_name:
            args.experience_query = exp_name
        participants = _extract_participant_count(msg_lower)
        if participants:
            args.participant_count = participants
        date_str = _extract_date(msg_lower)
        if date_str:
            args.requested_date = date_str
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="check_experience_availability",
            arguments=args,
            user_goal="El usuario quiere saber disponibilidad.",
            audit_summary="Intent detectado: consultar disponibilidad.",
        )

    # ── List experiences (keep last to avoid "dime" catching detail queries) ──
    if _matches_any(msg_lower, _EXPERIENCE_KEYWORDS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.95,
            tool_name="list_experiences",
            arguments=ToolArgs(limit=50),
            user_goal="El usuario quiere ver las experiencias disponibles.",
            audit_summary="Intent detectado: listar experiencias del catálogo.",
        )

    # ── Session / status check ──
    if _matches_any(msg_lower, _SESSION_KEYWORDS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="get_reservation_status_by_phone",
            user_goal="El usuario quiere saber el estado de su reserva.",
            audit_summary="Intent detectado: consulta de estado de reserva.",
        )

    return None
