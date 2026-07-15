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
    r"\b(hablame|cuentame|dime.mas|cuentame|explicame|mas.sobre|quiero.saber)\b",
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

# Consulta de medios/detalles de pago. Las peticiones explícitas de Bold se
# resuelven primero mediante _BOLD_KEYWORDS.
_PAYMENT_INFO_KEYWORDS = [
    r"\b(detalles?.del.?pago|detalles?.para.?pagar|como.?pago|como.?realizo.?el.?pago)\b",
    r"\b(medios.?de.?pago|formas.?de.?pago|opciones.?de.?pago|numero.?de.?cuenta)\b",
    r"\b(informacion.?del.?pago|informacion.?de.?pago|datos.?de.?pago|donde.?pago)\b",
    r"\b(cuenta.?bancolombia|bancolombia|cuenta.?de.?ahorros?)\b",
]

_BOLD_KEYWORDS = [
    r"\bbold\b",
    r"\bbld\b",
    r"\blink.de.pago.bold\b",
    r"\bpago.bold\b",
    r"\blink.bold\b",
    r"\b(link|pagar|pago).*(bold)\b",
    r"\bquiero.*link\b",
]

_PUBLIC_CONFIGURATION_KEYWORDS = [
    r"\b(donde|dnd).*(queda|qda|ubicacion|ubikcion)\b",
    r"\b(ubicacion|ubikcion|como.llegar|google.maps|maps)\b",
    r"\b(que|q|cuales).*(edad|edades)\b",
    r"\b(edad|minima|maxima|rango.de.edad)\b",
    r"\b(cuanto|cuanto|qto).*(tiempo|tmpo).*(pre.?reserva|preresrva|pagar)\b",
    r"\b(vencimiento|vence|caduca).*(pre.?reserva|preresrva)\b",
    r"\b(cuantos|cuántos).*(dias|días).*(anticipacion|anticipación|antes).*(reservar|rsrvar)\b",
    r"\b(necesito|tengo.que|debo).*(comprobante|soporte).*(pago)\b",
]

_ADMIN_CONTEXT_KEYWORDS = [
    r"\b(reservas?|equinos?|mulas?|proveedores?|sillas?|monturas?|asignaciones?|tablero)\b",
    r"\b(comprobante|reporte|ventas|ocupacion|carga.equina)\b",
    r"\b(contactos?.de.?emergencia|emergencias?)\b",
]

_ADMIN_LIST_RESERVATIONS = [
    r"\b(lista(r|me|r)?|muestra(r|me)?|dime|ver|dame)\b.*\b(reservas?)\b",
    r"\b(reservas?)\b.*\b(pendientes?|confirmadas?|hoy|manana|mañana)\b",
    r"\b(qu[eé]|que)\s+reservas?\s+hay\b",
    r"\bdame\b.*\b(reservas?)\b",
    r"\b(reservas?)\b.*\b(esta\s+semana|semana)\b",
]

_ADMIN_LIST_EQUINES = [
    r"\b(lista(r|me|r)?|muestra(r|me)?|dime|ver)\b.*\b(equinos?|mulas?)\b",
]

_ADMIN_APPROVE_PAYMENT = [
    r"\b(aprobar|aprueba|confirma)\b.*\b(pago|comprobante)\b",
]

_ADMIN_REJECT_PAYMENT = [
    r"\b(rechaza(r|me)?|rechazar)\b.*\b(pago|comprobante)\b",
]

_ADMIN_SALES_REPORT = [
    r"\b(reporte|resumen)\b.*\b(ventas?)\b",
    r"\b(ventas?)\b.*\b(reporte|resumen)\b",
    r"\b(ingresos?|facturacion|facturación)\b",
    r"\bcuantos?\s+ingresos?\b",
    r"\bcuántos?\s+ingresos?\b",
]

_ADMIN_CHANNEL_PERFORMANCE = [
    r"\b(redes?|canales?|canal|origen|origenes|orígenes)\b",
    r"\b(de\s+donde|de\s+dónde)\b.*\b(viene|vienen|gente|clientes?)\b",
    r"\bwhatsapp\b.*\b(facebook|instagram|email)\b",
]

_ADMIN_FUNNEL_REPORT = [
    r"\b(embudo|funnel|conversion|conversión)\b",
]

_ADMIN_OCCUPANCY_REPORT = [
    r"\b(reporte|ocupacion|ocupación)\b",
]

_ADMIN_EQUINE_WORKLOAD = [
    r"\b(carga|workload)\b.*\b(equina|equinos?|mulas?)\b",
]

_ADMIN_ASSIGNMENT_BOARD = [
    r"\b(tablero|asignaciones?)\b",
    r"\b(asignaciones?)\b.*\b(reserva)\b",
]

_ADMIN_LIST_PROVIDERS = [
    r"\b(lista(r|me|r)?|muestra(r|me)?|dime|ver)\b.*\b(proveedores?)\b",
]

_ADMIN_LIST_SADDLES = [
    r"\b(lista(r|me|r)?|muestra(r|me)?|dime|ver)\b.*\b(sillas?|monturas?)\b",
]

_ADMIN_EMERGENCY_CONTACTS = [
    r"\b(contactos?.de.?emergencia|emergencias?|numeros?.de.?emergencia)\b",
]


def _extract_reservation_code(text: str) -> str | None:
    m = re.search(r"\b([A-Z]{2,4}-?\d{4,})\b", text.upper())
    if m:
        return m.group(1)
    m = re.search(r"\b(reserva|codigo)\s+([A-Z0-9-]{4,})\b", text, flags=re.IGNORECASE)
    if m:
        return m.group(2).upper()
    return None


def _is_admin_context(channel: str | None, msg_lower: str) -> bool:
    if channel == "admin_api":
        return True
    return _matches_any(msg_lower, _ADMIN_CONTEXT_KEYWORDS)


def _extract_date_range(text: str) -> tuple[str, str] | None:
    from app.ai.assistant.date_extractor import extract_date_range_from_message

    try:
        return extract_date_range_from_message(text)
    except Exception:
        return None


def _build_admin_reservation_args(msg_lower: str) -> ToolArgs:
    args = ToolArgs(limit=50)
    date_range = _extract_date_range(msg_lower)
    if date_range:
        date_from, date_to = date_range
        args.date_from = date_from  # type: ignore[attr-defined]
        args.date_to = date_to  # type: ignore[attr-defined]
    elif date_str := _extract_date(msg_lower):
        args.date_from = date_str  # type: ignore[attr-defined]
        args.date_to = date_str  # type: ignore[attr-defined]
    if re.search(r"\bpendientes?\b", msg_lower):
        args.status = "pending"  # type: ignore[attr-defined]
    elif re.search(r"\bconfirmadas?\b", msg_lower):
        args.status = "confirmed"  # type: ignore[attr-defined]
    return args


def _detect_admin_plan(msg_lower: str) -> AssistantPlan | None:
    args = ToolArgs()
    date_str = _extract_date(msg_lower)
    if date_str:
        args.requested_date = date_str

    if _matches_any(msg_lower, _ADMIN_EMERGENCY_CONTACTS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.92,
            tool_name="admin_get_emergency_contacts",
            arguments=ToolArgs(),
            user_goal="El admin quiere ver contactos de emergencia.",
            audit_summary="Intent admin: contactos de emergencia.",
        )

    if _matches_any(msg_lower, _ADMIN_ASSIGNMENT_BOARD):
        code = _extract_reservation_code(msg_lower)
        plan_args = ToolArgs(reservation_code=code) if code else ToolArgs()
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_assignment_board",
            arguments=plan_args,
            user_goal="El admin quiere ver el tablero de asignación.",
            audit_summary="Intent admin: tablero de asignación.",
        )

    if _matches_any(msg_lower, _ADMIN_LIST_PROVIDERS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_list_providers",
            arguments=ToolArgs(limit=50),
            user_goal="El admin quiere listar proveedores.",
            audit_summary="Intent admin: listar proveedores.",
        )

    if _matches_any(msg_lower, _ADMIN_LIST_SADDLES):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_list_saddles",
            arguments=ToolArgs(limit=200),
            user_goal="El admin quiere listar sillas/monturas.",
            audit_summary="Intent admin: listar sillas.",
        )

    if _matches_any(msg_lower, _ADMIN_APPROVE_PAYMENT):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_approve_payment",
            arguments=ToolArgs(),
            user_goal="El admin quiere aprobar un pago.",
            audit_summary="Intent admin: aprobar pago.",
        )

    if _matches_any(msg_lower, _ADMIN_REJECT_PAYMENT):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_reject_payment_proof",
            arguments=ToolArgs(),
            user_goal="El admin quiere rechazar un comprobante.",
            audit_summary="Intent admin: rechazar comprobante.",
        )

    if _matches_any(msg_lower, _ADMIN_SALES_REPORT):
        report_args = ToolArgs()
        date_range = _extract_date_range(msg_lower)
        if date_range:
            report_args.date_from = date_range[0]  # type: ignore[attr-defined]
            report_args.date_to = date_range[1]  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_sales_summary",
            arguments=report_args,
            user_goal="El admin quiere un reporte de ventas / ingresos.",
            audit_summary="Intent admin: reporte de ventas.",
        )

    if _matches_any(msg_lower, _ADMIN_CHANNEL_PERFORMANCE):
        report_args = ToolArgs()
        date_range = _extract_date_range(msg_lower)
        if date_range:
            report_args.date_from = date_range[0]  # type: ignore[attr-defined]
            report_args.date_to = date_range[1]  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_channel_performance",
            arguments=report_args,
            user_goal="El admin quiere ver de qué canales/redes viene la gente.",
            audit_summary="Intent admin: rendimiento por canal.",
        )

    if _matches_any(msg_lower, _ADMIN_FUNNEL_REPORT):
        report_args = ToolArgs()
        date_range = _extract_date_range(msg_lower)
        if date_range:
            report_args.date_from = date_range[0]  # type: ignore[attr-defined]
            report_args.date_to = date_range[1]  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_reservation_funnel",
            arguments=report_args,
            user_goal="El admin quiere ver el embudo de reservas.",
            audit_summary="Intent admin: embudo de conversión.",
        )

    if _matches_any(msg_lower, _ADMIN_OCCUPANCY_REPORT):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_occupancy_report",
            arguments=args,
            user_goal="El admin quiere un reporte de ocupación.",
            audit_summary="Intent admin: reporte de ocupación.",
        )

    if _matches_any(msg_lower, _ADMIN_EQUINE_WORKLOAD):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_equine_workload_report",
            arguments=args,
            user_goal="El admin quiere reporte de carga equina.",
            audit_summary="Intent admin: carga equina.",
        )

    if _matches_any(msg_lower, _ADMIN_LIST_EQUINES):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.92,
            tool_name="admin_list_equines",
            arguments=ToolArgs(),
            user_goal="El admin quiere listar equinos.",
            audit_summary="Intent admin: listar equinos.",
        )

    if _matches_any(msg_lower, _ADMIN_LIST_RESERVATIONS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.92,
            tool_name="admin_list_reservations",
            arguments=_build_admin_reservation_args(msg_lower),
            user_goal="El admin quiere listar reservas.",
            audit_summary="Intent admin: listar reservas.",
        )

    code = _extract_reservation_code(msg_lower)
    if code and re.search(r"\b(detalle|detalles|info|informacion)\b.*\b(reserva)\b", msg_lower):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_reservation_detail",
            arguments=ToolArgs(code=code),
            user_goal=f"El admin quiere detalle de la reserva {code}.",
            audit_summary="Intent admin: detalle de reserva.",
        )

    return None


_GREETINGS = [
    r"^(buen(?:os)?\s*d[ií][aá]s?|buenas\s*(tardes|noches)|hola|buenas|saludos|que\s*hay|que\s*mas)\b\s*[,.!?]?\s*",
]


def _extract_experience_name(text: str) -> str | None:
    cleaned = text.strip()
    # Strip common greetings first
    for greeting in _GREETINGS:
        cleaned = re.sub(greeting, "", cleaned, flags=re.IGNORECASE).strip()
    # Remove leading intent phrases
    for prefix in [
        r"dame\s+(los\s+)?(detalles?\s+)?(de\s+)?(la\s+)?(para\s+)?(esta\s+)?(de\s+)?",
        r"en\s+que\s+consiste\s+",
        r"cuentame\s+de\s+",
        r"hablame\s+de\s+",
        r"dime\s+mas\s+(sobre|de)\s+",
        r"quiero\s+saber\s+(de|sobre)\s+",
    ]:
        cleaned = re.sub(f"^{prefix}", "", cleaned, flags=re.IGNORECASE).strip()
    # Strip leading articles
    cleaned = re.sub(r"^(el|la|los|las|un|una)\s+", "", cleaned, flags=re.IGNORECASE).strip()
    # Strip trailing punctuation
    cleaned = cleaned.rstrip(",.!?;:.\n\r ")
    if len(cleaned) > 2 and not any(
        w in cleaned.lower()
        for w in ["experiencias", "actividades", "planes", "precio", "tienes", "ofrecen"]
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
    channel: str | None = None,
) -> AssistantPlan | None:
    msg_lower = user_message.lower().strip()

    exp_name = _extract_experience_name(user_message)

    if _is_admin_context(channel, msg_lower):
        admin_plan = _detect_admin_plan(msg_lower)
        if admin_plan:
            return admin_plan
        if channel == "admin_api":
            return None

    # ── Bold payment request → configured payment instructions ──
    if _matches_any(msg_lower, _BOLD_KEYWORDS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.95,
            tool_name="get_payment_instructions",
            arguments=ToolArgs(bold_requested=True),
            user_goal="El usuario solicita link de pago Bold.",
            audit_summary=("Intent detectado: solicitud de enlace Bold configurado."),
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

    # ── Public rules and location → live configuration ──
    if _matches_any(msg_lower, _PUBLIC_CONFIGURATION_KEYWORDS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.95,
            tool_name="get_public_business_rules",
            arguments=ToolArgs(),
            user_goal="El usuario consulta reglas o ubicación configuradas de La Juana.",
            audit_summary="Intent detectado: consulta de configuración pública vigente.",
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
