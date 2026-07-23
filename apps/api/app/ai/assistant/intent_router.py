from __future__ import annotations

import logging
import re
from typing import Any

from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs

_logger = logging.getLogger(__name__)

_EXPERIENCE_KEYWORDS = [
    # "dime" solo NO basta (rompe "dime eso en español" / "dime la ubicación").
    r"\b(listame|lista|muestra|enseñame|enseñame|cuales|que.ofrecen|que.hay|que.tienen)\b",
    r"\b(dime|dame)\b.*\b(experiencias|actividades|planes|recorridos|catalogo|opciones|servicios)\b",
    r"\b(experiencias|actividades|planes|recorridos|catalogo|opciones|servicios)\b",
]

_DETAIL_KEYWORDS = [
    r"\b(detalles?|descripcion|descripción|informacion|información|en.que.consiste|como.es|cómo.es|que.incluye|qué.incluye|que.se.hace|qué.se.hace)\b",
    r"\b(hablame|háblame|cuentame|cuéntame|dime.mas|dime.más|explicame|explícame|mas.sobre|más.sobre|quiero.saber)\b",
    r"\bacerca\s+de\b",
    r"\b(dime|dima|dame)\b.*\b(acerca|sobre)\b",
    r"\bsobre\s+(la|el|los|las|una?|esta|este)\b",
]

_PRICE_KEYWORDS = [
    r"\b(cuanto.vale?|cuanto.cuesta|precio|tarifa|cotizame|cotizacion|valor|cuanto.sale)\b",
]

_AVAILABILITY_KEYWORDS = [
    r"\b(hay.cupo|disponibilidad|se.puede|hay.lugar|cabemos|caben|cupo.disponible)\b",
]

# Intención de reservar con datos completos: cuando el usuario dice "quiero
# reservar X para fecha N personas", disparamos la tool combinada
# (check_availability_and_quote) que verifica cupo, cotiza y pregunta por
# nombre/correo en una sola respuesta.
_RESERVE_INTENT_KEYWORDS = [
    r"\b(quiero|quisiera|me.gustaria|me.interesa|deseo|necesito)\b.*\b(reservar|apartar|separar|agendar|reserva|apartado|separado)\b",
    r"\b(reservar|apartar|separar|agendar|reserva|apartado|separado)\b.*\b(para|el|la|una|otra)\b",
    r"\b(hazme|hazme.la|armame|montame)\b.*\b(reserva|apartado)\b",
    r"\b(i\s+want\s+to|i'?d\s+like\s+to|i\s+would\s+like\s+to|please|need\s+to|let'?s)\b.*\b(book|reserve)\b",
    r"\b(book|reserve)\b.*\b(the|for|on)\b",
    r"\b(make\s+a\s+booking|make\s+a\s+reservation)\b",
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
    r"\b(donde|dónde|dnd).*(queda|quedan|qda|ubicacion|ubicación|ubikcion)\b",
    r"\b(ubicacion|ubicación|ubikcion|como.llegar|cómo.llegar|google.maps|maps)\b",
    r"\b(que|qué|q|cuales|cuáles).*(edad|edades)\b",
    r"\b(edad|minima|mínima|maxima|máxima|rango.de.edad)\b",
    r"\b(cuanto|cuánto|qto).*(tiempo|tmpo).*(pre.?reserva|preresrva|pagar)\b",
    r"\b(vencimiento|vence|caduca).*(pre.?reserva|preresrva)\b",
    r"\b(cuantos|cuántos).*(dias|días).*(anticipacion|anticipación|antes).*(reservar|rsrvar)\b",
    r"\b(necesito|tengo.que|debo).*(comprobante|soporte).*(pago)\b",
]

# Historia / cultura / empresa (KB estática). Solo empresa — no “qué es una experiencia”.
_COMPANY_KNOWLEDGE_KEYWORDS = [
    r"\b(quienes|quiénes)\s+(somos|son)\b",
    r"\b(quien|quién|quienes|quiénes)\s+(fundo|fundó|funda|fundaron)\b",
    r"\bfundador(es)?\b",
    r"\b(jairo|pamela)\b",
    r"\b(historia|origen)\b.*\b(juana|empresa|finca|ustedes)\b",
    r"\b(historia|origen)\s+(de\s+)?(la\s+)?juana\b",
    r"\b(que|qué)\s+es\s+(esto\s+)?(de\s+)?(la\s+)?juana\b",
    r"\b(que|qué)\s+es\s+esto\s+de\s+la\s+juana",
    r"\b(sobre|acerca\s+de)\s+(la\s+)?juana\b",
    r"\bdescripci[oó]n\s+(general\s+)?(de\s+)?(la\s+)?juana\b",
    r"\b(informaci[oó]n|info)\s+(general\s+)?(de\s+)?(la\s+)?juana\b",
    r"\b(cuentame|cuéntame|hablame|háblame|dime)\s+(mas\s+|más\s+)?(sobre\s+|de\s+)?(la\s+)?juana\b",
    r"\bpaisaje\s+cultural\s+cafetero\b",
    r"\bunesco\b",
    r"\bsostenibilidad\b",
    r"\bpropuesta\s+de\s+valor\b",
    r"\b(historia|tradicion|tradición)\b.*(mulas?|arrier)",
    r"\barrier[ií]a\b",
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

_ADMIN_DEACTIVATE_USER = [
    r"\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b.*\b(usuario)\b",
    r"\b(usuario)\b.*\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b",
]

_ADMIN_DEACTIVATE_PROVIDER = [
    r"\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b.*\b(proveedor)\b",
    r"\b(proveedor)\b.*\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b",
]

_ADMIN_DEACTIVATE_EQUINE = [
    r"\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b.*\b(equino|mula)\b",
    r"\b(equino|mula)\b.*\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b",
]

_ADMIN_DEACTIVATE_SADDLE = [
    r"\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b.*\b(silla|montura)\b",
    r"\b(silla|montura)\b.*\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b",
]

_ADMIN_DEACTIVATE_EXPERIENCE = [
    r"\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b.*\b(experiencia)\b",
    r"\b(experiencia)\b.*\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b",
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

_ADMIN_SADDLES_AVAILABLE = [
    r"\b(sillas?|monturas?)\b.*\b(disponibles?)\b.*\b(reserva)\b",
    r"\b(reserva)\b.*\b(sillas?|monturas?)\b.*\b(disponibles?)\b",
]

_ADMIN_LIST_EQUINE_EVENTS = [
    r"\b(eventos?)\b.*\b(equino|equinos?|mula|mulas)\b",
    r"\b(equino|equinos?|mula|mulas)\b.*\b(eventos?)\b",
]

_ADMIN_CREATE_EQUINE_EVENT = [
    r"\b(crea(r)?|registra(r)?|agrega(r)?)\b.*\b(eventos?)\b.*\b(equino|equinos?|mula|mulas)\b",
]

_ADMIN_UPDATE_EQUINE_EVENT = [
    r"\b(actualiza(r)?|edita(r)?|modifica(r)?)\b.*\b(eventos?)\b",
]

_ADMIN_FINALIZE_ALL_ASSIGNMENTS = [
    r"\b(finaliza(r)?|cerra(r)?)\b.*\b(todas)\b.*\b(asignaciones?)\b",
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


def _extract_object_id(text: str, field_name: str) -> str | None:
    pattern = rf"\b{re.escape(field_name)}\b\s*[:=]?\s*([a-f0-9]{{24}})"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _extract_admin_user_reference(text: str) -> str | None:
    return _extract_admin_entity_reference(text, ["usuario"])


def _extract_admin_entity_reference(text: str, entity_terms: list[str]) -> str | None:
    cleaned = text.strip()
    cleaned = re.sub(
        r"\b(borra(r)?|elimina(r)?|desactiva(r)?|inhabilita(r)?|deshabilita(r)?)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    for entity_term in entity_terms:
        cleaned = re.sub(rf"\b{re.escape(entity_term)}s?\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(el|la|al|a|de|del|por favor)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.!?:;\n\r\t")
    return cleaned or None


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

    if _matches_any(msg_lower, _ADMIN_FINALIZE_ALL_ASSIGNMENTS):
        reservation_id = _extract_object_id(msg_lower, "reservation_id")
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_finalize_all_assignments",
            arguments=ToolArgs(reservation_id=reservation_id) if reservation_id else ToolArgs(),
            user_goal="El admin quiere finalizar todas las asignaciones de una reserva.",
            audit_summary="Intent admin: finalizar todas las asignaciones.",
        )

    if _matches_any(msg_lower, _ADMIN_SADDLES_AVAILABLE):
        reservation_id = _extract_object_id(msg_lower, "reservation_id")
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_list_available_saddles_for_reservation",
            arguments=ToolArgs(reservation_id=reservation_id) if reservation_id else ToolArgs(),
            user_goal="El admin quiere ver sillas disponibles para una reserva.",
            audit_summary="Intent admin: sillas disponibles por reserva.",
        )

    if _matches_any(msg_lower, _ADMIN_CREATE_EQUINE_EVENT):
        equine_id = _extract_object_id(msg_lower, "equine_id")
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_create_equine_event",
            arguments=ToolArgs(equine_id=equine_id) if equine_id else ToolArgs(),
            user_goal="El admin quiere registrar un evento de equino.",
            audit_summary="Intent admin: crear evento equino.",
        )

    if _matches_any(msg_lower, _ADMIN_UPDATE_EQUINE_EVENT):
        event_id = _extract_object_id(msg_lower, "event_id")
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_update_equine_event",
            arguments=ToolArgs(event_id=event_id) if event_id else ToolArgs(),
            user_goal="El admin quiere actualizar un evento de equino.",
            audit_summary="Intent admin: actualizar evento equino.",
        )

    if _matches_any(msg_lower, _ADMIN_LIST_EQUINE_EVENTS):
        equine_id = _extract_object_id(msg_lower, "equine_id")
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_list_equine_events",
            arguments=ToolArgs(equine_id=equine_id) if equine_id else ToolArgs(),
            user_goal="El admin quiere ver eventos de un equino.",
            audit_summary="Intent admin: listar eventos equinos.",
        )

    saddle_id = _extract_object_id(msg_lower, "saddle_id")
    if saddle_id and re.search(r"\b(detalle|detalles|info|informacion|ver)\b", msg_lower):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_saddle",
            arguments=ToolArgs(saddle_id=saddle_id),
            user_goal="El admin quiere ver detalle de una silla.",
            audit_summary="Intent admin: detalle de silla.",
        )

    provider_id = _extract_object_id(msg_lower, "provider_id")
    if provider_id and re.search(r"\b(detalle|detalles|info|informacion|ver)\b", msg_lower):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_get_provider",
            arguments=ToolArgs(provider_id=provider_id),
            user_goal="El admin quiere ver detalle de un proveedor.",
            audit_summary="Intent admin: detalle de proveedor.",
        )

    if _matches_any(msg_lower, _ADMIN_ASSIGNMENT_BOARD):
        code = _extract_reservation_code(msg_lower)
        reservation_id = _extract_object_id(msg_lower, "reservation_id")
        if reservation_id:
            plan_args = ToolArgs(reservation_id=reservation_id)
        else:
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

    if _matches_any(msg_lower, _ADMIN_DEACTIVATE_USER):
        user_id = _extract_object_id(msg_lower, "user_id")
        user_reference = None if user_id else _extract_admin_user_reference(msg_lower)
        plan_args = ToolArgs(user_id=user_id) if user_id else ToolArgs()
        if user_reference:
            plan_args.q = user_reference  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_deactivate_user",
            arguments=plan_args,
            user_goal="El admin quiere desactivar un usuario.",
            audit_summary="Intent admin: desactivar usuario.",
        )

    if _matches_any(msg_lower, _ADMIN_DEACTIVATE_PROVIDER):
        provider_id = _extract_object_id(msg_lower, "provider_id")
        provider_reference = None if provider_id else _extract_admin_entity_reference(msg_lower, ["proveedor"])
        plan_args = ToolArgs(provider_id=provider_id) if provider_id else ToolArgs()
        if provider_reference:
            plan_args.q = provider_reference  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_deactivate_provider",
            arguments=plan_args,
            user_goal="El admin quiere desactivar un proveedor.",
            audit_summary="Intent admin: desactivar proveedor.",
        )

    if _matches_any(msg_lower, _ADMIN_DEACTIVATE_EQUINE):
        equine_id = _extract_object_id(msg_lower, "equine_id")
        equine_reference = None if equine_id else _extract_admin_entity_reference(msg_lower, ["equino", "mula"])
        plan_args = ToolArgs(equine_id=equine_id) if equine_id else ToolArgs()
        if equine_reference:
            plan_args.q = equine_reference  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_deactivate_equine",
            arguments=plan_args,
            user_goal="El admin quiere desactivar un equino.",
            audit_summary="Intent admin: desactivar equino.",
        )

    if _matches_any(msg_lower, _ADMIN_DEACTIVATE_SADDLE):
        saddle_id = _extract_object_id(msg_lower, "saddle_id")
        saddle_reference = None if saddle_id else _extract_admin_entity_reference(msg_lower, ["silla", "montura"])
        plan_args = ToolArgs(saddle_id=saddle_id) if saddle_id else ToolArgs()
        if saddle_reference:
            plan_args.q = saddle_reference  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_deactivate_saddle",
            arguments=plan_args,
            user_goal="El admin quiere desactivar una silla.",
            audit_summary="Intent admin: desactivar silla.",
        )

    if _matches_any(msg_lower, _ADMIN_DEACTIVATE_EXPERIENCE):
        experience_id = _extract_object_id(msg_lower, "experience_id")
        experience_reference = None if experience_id else _extract_admin_entity_reference(msg_lower, ["experiencia"])
        plan_args = ToolArgs(experience_id=experience_id) if experience_id else ToolArgs()
        if experience_reference:
            plan_args.q = experience_reference  # type: ignore[attr-defined]
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.9,
            tool_name="admin_deactivate_experience",
            arguments=plan_args,
            user_goal="El admin quiere desactivar una experiencia.",
            audit_summary="Intent admin: desactivar experiencia.",
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
    # Remove leading intent phrases (order matters: longer / more specific first)
    for prefix in [
        r"dame\s+(los\s+)?(detalles?\s+)?(de\s+)?(la\s+)?(para\s+)?(esta\s+)?(de\s+)?",
        r"en\s+que\s+consiste\s+",
        r"cuentame\s+de\s+",
        r"hablame\s+de\s+",
        r"(dime|dima)\s+(acerca\s+de\s+|sobre\s+)?",
        r"dime\s+mas\s+(sobre|de)\s+",
        r"quiero\s+saber\s+(de|sobre)\s+",
        r"acerca\s+de\s+(la|el|los|las)?\s*",
        r"sobre\s+(la|el|los|las|una?)\s+",
        r"(i\s+want\s+to|i\s+would\s+like\s+to|please|need\s+to)\s+(book|reserve)\s+(the\s+)?",
        r"(book|reserve)\s+(the\s+)?",
        # "quiero hacer una reserva para la montaña..." / "me gustaria hacer una reservacion para..."
        r"(quiero|quisiera|me\s+gustaria|me\s+gustaría|deseo|necesito)\s+"
        r"(hacer\s+)?(una\s+)?(reserva|reservaci[oó]n)\s+(para\s+)?(la|el|los|las)?\s*",
        r"(hacer\s+)?(una\s+)?(reserva|reservaci[oó]n)\s+(para\s+)?(la|el|los|las)?\s*",
        r"(quiero|quisiera|me.gustaria|me.interesa|deseo|necesito)\s+(reservar|apartar|separar|agendar)\s+(la|el|los|las)?\s*",
        r"(reservar|apartar|separar|agendar)\s+(la|el|los|las)\s+",
    ]:
        cleaned = re.sub(f"^{prefix}", "", cleaned, flags=re.IGNORECASE).strip()
    # Strip leading articles (ES + EN)
    cleaned = re.sub(r"^(el|la|los|las|un|una|the|a|an)\s+", "", cleaned, flags=re.IGNORECASE).strip()
    # Strip trailing date/people info. Do NOT split on bare "para" when it was already
    # consumed by a reservation-prefix ("reserva para X"); use "para N personas" patterns.
    cleaned = re.split(
        r"\s+(para\s+\d+|el\s+\d|la\s+\d|los|las|y\s+\d|a\s+\d|con\s+\d|"
        r"for\s+\d|on\s+\d|at\s+\d|people|personas|participantes|adultos|kids|guests|niños|"
        r"\d+\s*(personas?|participantes?|people|guests?|adultos?))\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    # Also strip "para 4" style if left after name
    cleaned = re.split(
        r"\s+para\s+\d+\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    # Strip trailing month names / date words: "X 5 de agosto" or "X august 5"
    cleaned = re.split(
        r"\s+\d{1,2}\s+(de\s+)?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|ago|sep|sept|oct|nov|dec|agust|augus|agost)",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    # Strip trailing bare date: "X august 5" / "X 5"
    cleaned = re.split(
        r"\s+\d{1,2}$",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    # Strip trailing prepositions/words que quedaron sueltos
    cleaned = re.sub(
        r"\s+(para|con|de|y|a|for|with|on|at|in)$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    # Strip trailing punctuation
    cleaned = cleaned.rstrip(",.!?;:.\n\r ")
    if len(cleaned) > 2 and not any(
        w in cleaned.lower()
        for w in ["experiencias", "actividades", "planes", "precio", "tienes", "ofrecen", "reserva", "reservacion", "reservación"]
    ):
        return cleaned
    return None


def _extract_participant_count(text: str) -> int | None:
    m = re.search(
        r"(\d+)\s*(?:personas?|participantes?|pax|adultos?|niños?|people|persons?|guests?)",
        text.lower(),
    )
    if m:
        return int(m.group(1))
    m = re.search(
        r"(?:para|somos?|seriamos?|for)\s*(\d+)",
        text.lower(),
    )
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


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def _extract_name_and_email(text: str) -> tuple[str | None, str | None]:
    """Extrae nombre y correo de frases como 'juan diego - juan@email.com'."""
    email_match = _EMAIL_RE.search(text)
    if not email_match:
        return None, None
    email = email_match.group(0)
    name_part = text[:email_match.start()].strip().rstrip("- ,;:")
    if not name_part or len(name_part) < 3:
        name_part = text[email_match.end():].strip().rstrip("- ,;:")
    if not name_part or len(name_part) < 3:
        return None, email
    return name_part, email


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

    # ── Horarios de atención → reglas públicas (incluyen opening_hours) ──
    if re.search(r"\b(horario|horarios|abren|abre|cierran|abierto|opening\s+hours)\b", msg_lower):
        # Si también piden ubicación, igual usamos reglas públicas (tienen ambos).
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.93,
            tool_name="get_public_business_rules",
            arguments=ToolArgs(),
            user_goal="El usuario pregunta por horarios (y/o ubicación) de La Juana.",
            audit_summary="Intent detectado: horarios/ubicación vía reglas públicas.",
        )

    # ── “Qué es una experiencia” → catálogo, NO RAG ──
    if re.search(r"\b(que|qué)\s+es\s+una\s+experiencia\b", msg_lower):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.92,
            tool_name="list_experiences",
            arguments=ToolArgs(limit=50),
            user_goal="El usuario pregunta qué es una experiencia; mostrar catálogo.",
            audit_summary="Intent detectado: explicar experiencias vía list_experiences.",
        )

    # ── Historia / cultura / empresa → KB estática (RAG) ──
    # Después de reglas live; antes de reserva. Keywords acotados para no
    # interceptar "quiero reservar… 3 personas…".
    if _matches_any(msg_lower, _COMPANY_KNOWLEDGE_KEYWORDS):
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.93,
            tool_name="search_company_knowledge",
            arguments=ToolArgs(query=user_message.strip()[:500]),
            user_goal="El usuario pregunta por historia, fundadores o cultura de La Juana.",
            audit_summary="Intent detectado: consulta de conocimiento corporativo (RAG).",
        )

    # ── Name + email response → create_reservation_draft direct ──
    # Cuando el usuario envía su nombre y correo (típicamente después de que
    # check_availability_and_quote pidió esos datos), y la sesión ya tiene
    # experience_id + quote_snapshot, disparamos directo la tool de pre-reserva
    # sin pasar por el LLM.
    hname, hmail = _extract_name_and_email(user_message)
    if hname and hmail:
        slots = session_slots or {}
        exp_id = slots.get("experience_id")
        qs = slots.get("quote_snapshot")
        holder_phone = slots.get("holder_phone")
        _logger.info(
            "[name_email_debug] name=%s email=%s exp_id=%s qs=%s holder_phone=%s slots_keys=%s",
            hname, hmail, exp_id, bool(qs), holder_phone, list(slots.keys()),
        )
        if exp_id and qs and holder_phone:
            # Extract participant count/date from session or message
            participants = _extract_participant_count(user_message) or slots.get("participant_count", 1)
            date_str = _extract_date(user_message) or slots.get("requested_date")
            args = ToolArgs(
                experience_id=exp_id,
                participant_count=participants,
                holder_phone=holder_phone,
                holder_name=hname,
                holder_email=hmail,
                requested_date=date_str,
                quote_snapshot=qs,
            )
            if date_str:
                args.requested_date = date_str
            return AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.95,
                tool_name="create_reservation_draft",
                arguments=args,
                user_goal=(
                    "El usuario proporcionó nombre y correo para completar "
                    "la pre-reserva."
                ),
                audit_summary=(
                    "Intent detectado: nombre+correo proporcionados, "
                    "disparando create_reservation_draft directo."
                ),
            )

    # ── Follow-up de reserva: fecha + personas con experiencia ya en sesión ──
    # Evita el flujo lento check_availability → "¿te parece?" → quote → "¿aviso?".
    slots = session_slots or {}
    followup_participants = _extract_participant_count(msg_lower) or (
        int(slots["participant_count"])
        if str(slots.get("participant_count") or "").isdigit()
        else None
    )
    # Fecha del mensaje O de la sesión (turno "3 personas" tras elegir fecha).
    followup_date = _extract_date(msg_lower) or slots.get("requested_date")
    if followup_date is not None:
        followup_date = str(followup_date)
    session_exp_id = slots.get("experience_id")
    session_exp_query = slots.get("experience_query") or slots.get("experience_name")
    # Si el mensaje trae personas (o fecha) y la sesión ya tiene el resto → combinada.
    msg_has_participants = _extract_participant_count(msg_lower) is not None
    msg_has_date = _extract_date(msg_lower) is not None
    if (
        followup_participants
        and followup_date
        and (exp_name or session_exp_id or session_exp_query)
        and (msg_has_participants or msg_has_date)
        and msg_lower.strip() not in {"si", "sí", "yes", "ok", "okay", "dale"}
    ):
        args = ToolArgs(
            participant_count=int(followup_participants),
            requested_date=followup_date,
        )
        if exp_name:
            args.experience_query = exp_name
        elif session_exp_query:
            args.experience_query = str(session_exp_query)
        if session_exp_id:
            args.experience_id = str(session_exp_id)
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.93,
            tool_name="check_availability_and_quote",
            arguments=args,
            user_goal="El usuario completó fecha y personas para cotizar/reservar.",
            audit_summary=(
                "Intent detectado: fecha+personas con experiencia en sesión; "
                "tool combinada."
            ),
        )

    # ── Experience details (check before list to avoid "dime" matching list) ──
    # Excepción: "información de todas las experiencias" / "todas" → listado.
    _catalog_all = bool(
        re.search(
            r"\b(todas?|toditos?|completas?|lista\s+completa|el\s+cat[aá]logo)\b",
            msg_lower,
        )
        and _matches_any(msg_lower, _EXPERIENCE_KEYWORDS)
    )
    if _matches_any(msg_lower, _DETAIL_KEYWORDS) and not _catalog_all:
        # "descripción/info de la juana" no es una experiencia del catálogo → RAG
        if _matches_any(msg_lower, _COMPANY_KNOWLEDGE_KEYWORDS) or re.search(
            r"\b(descripci[oó]n|informaci[oó]n|info|detalles?)\b.*\b(la\s+)?juana\b",
            msg_lower,
        ):
            return AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.94,
                tool_name="search_company_knowledge",
                arguments=ToolArgs(query=user_message.strip()[:500]),
                user_goal="El usuario pide una descripción general de La Juana.",
                audit_summary=(
                    "Intent detectado: descripción de empresa (RAG), "
                    "no detalle de experiencia."
                ),
            )
        # "en qué consiste / no entiendo" sin nombre de experiencia → catálogo
        vague = bool(
            re.search(
                r"\b(no\s+entiend|entiendo|consiste|que\s+se\s+va\s+a\s+hacer|"
                r"qué\s+se\s+va\s+a\s+hacer|que\s+es\s+una\s+experiencia|"
                r"qué\s+es\s+una\s+experiencia)\b",
                msg_lower,
            )
        )
        if not exp_name or vague:
            return AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.9,
                tool_name="list_experiences",
                arguments=ToolArgs(limit=50),
                user_goal="El usuario no entiende qué se hace; mostrar catálogo.",
                audit_summary=(
                    "Intent detectado: detalle vago sin experiencia → list_experiences."
                ),
            )
        # Pass the full message so the tool can load the catalog and match
        # one or many experiences (typos / multi-ask in the same turn).
        detail_query = (user_message or "").strip()[:800] or exp_name
        return AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.92,
            tool_name="get_experience_detail",
            arguments=ToolArgs(experience_query=detail_query),
            user_goal="El usuario quiere detalles de una o más experiencias.",
            audit_summary=(
                "Intent detectado: detalle de experiencia(s) "
                "(catálogo completo + match)."
            ),
        )

    # ── Intención de reservar: experiencia + fecha + personas → check_availability_and_quote ──
    # Se evalúa ANTES que PRICE/AVAILABILITY para que "quiero reservar la
    # montaña de cristal para el 5 de agosto 3 personas" dispare la tool
    # combinada (ahorra 1 turno y reduce tokens).
    if _matches_any(msg_lower, _RESERVE_INTENT_KEYWORDS) and exp_name:
        args = ToolArgs()
        args.experience_query = exp_name
        participants = _extract_participant_count(msg_lower)
        if participants:
            args.participant_count = participants
        date_str = _extract_date(msg_lower)
        if date_str:
            args.requested_date = date_str
        if args.participant_count and args.requested_date:
            return AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.95,
                tool_name="check_availability_and_quote",
                arguments=args,
                user_goal="El usuario quiere reservar (disponibilidad + cotización combinadas).",
                audit_summary=(
                    "Intent detectado: reserva con datos completos, "
                    "usando tool combinada."
                ),
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
        # Si tenemos los 3 datos (experiencia + fecha + personas) usamos la
        # tool combinada (ahorra un turno al cliente).
        if args.experience_query and args.participant_count and args.requested_date:
            return AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.92,
                tool_name="check_availability_and_quote",
                arguments=args,
                user_goal="El usuario quiere saber precio y disponibilidad.",
                audit_summary="Intent detectado: cotizar (combinado con disponibilidad).",
            )
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
        # Si tenemos los 3 datos, usamos la combinada.
        if args.experience_query and args.participant_count and args.requested_date:
            return AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.92,
                tool_name="check_availability_and_quote",
                arguments=args,
                user_goal="El usuario quiere saber disponibilidad y precio.",
                audit_summary="Intent detectado: disponibilidad (combinado con cotización).",
            )
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

    # ── Fallback: si el usuario entrega experiencia + fecha + personas en un
    # solo mensaje sin ningún keyword explícito (típico de respuestas a
    # "¿qué experiencia, cuántas personas, qué fecha?"), asumimos intención
    # de reservar y disparamos la tool combinada. Esto evita un turno extra.
    if exp_name:
        participants = _extract_participant_count(user_message)
        date_str = _extract_date(user_message)
        if participants and date_str:
            return AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.85,
                tool_name="check_availability_and_quote",
                arguments=ToolArgs(
                    experience_query=exp_name,
                    participant_count=participants,
                    requested_date=date_str,
                ),
                user_goal="El usuario entregó experiencia + fecha + personas.",
                audit_summary=(
                    "Intent fallback: el usuario completó los 3 datos "
                    "sin keyword explícito, asumiendo intención de reservar."
                ),
            )

    return None
