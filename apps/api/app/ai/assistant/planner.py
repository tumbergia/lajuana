import inspect
import time

from app.ai.assistant.prompts.planner import (
    ADMIN_PLANNER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
)
from app.ai.assistant.tool_catalog import render_tools_for_prompt
from app.ai.language.messages import build_language_instruction
from app.ai.providers.factory import get_llm_provider
from app.core.logging import logger
from app.core.time import format_colombia_today_es, now_colombia
from app.schemas.assistant_plan import AssistantPlan

# Mapa de keywords → tools administrativas relevantes
# Si el mensaje del usuario contiene alguna keyword, solo mostramos esa categoría
_ADMIN_TOOL_CATEGORIES: dict[str, list[str]] = {
    "usuario": [
        "admin_list_users",
        "admin_create_user",
        "admin_update_user",
        "admin_deactivate_user",
    ],
    "usuarios": [
        "admin_list_users",
        "admin_create_user",
        "admin_update_user",
        "admin_deactivate_user",
    ],
    "experiencia": [
        "admin_list_experiences_admin",
        "admin_create_experience",
        "admin_update_experience",
        "admin_deactivate_experience",
    ],
    "experiencias": [
        "admin_list_experiences_admin",
        "admin_create_experience",
        "admin_update_experience",
        "admin_deactivate_experience",
    ],
    "fecha": [
        "admin_list_reservations",
        "admin_get_reservation_detail",
        "check_experience_availability",
        "list_available_schedules",
    ],
    "equino": [
        "admin_list_equines",
        "admin_get_equine",
        "admin_create_equine",
        "admin_update_equine",
        "admin_deactivate_equine",
        "admin_add_equine_health_event",
        "admin_update_equine_availability",
    ],
    "equinos": [
        "admin_list_equines",
        "admin_get_equine",
        "admin_create_equine",
        "admin_update_equine",
        "admin_deactivate_equine",
        "admin_add_equine_health_event",
        "admin_update_equine_availability",
    ],
    "mula": [
        "admin_list_equines",
        "admin_get_equine",
        "admin_create_equine",
        "admin_update_equine",
        "admin_deactivate_equine",
        "admin_add_equine_health_event",
        "admin_update_equine_availability",
    ],
    "mulas": [
        "admin_list_equines",
        "admin_get_equine",
        "admin_create_equine",
        "admin_update_equine",
        "admin_deactivate_equine",
        "admin_add_equine_health_event",
        "admin_update_equine_availability",
    ],
    "reserva": [
        "admin_list_reservations",
        "admin_get_reservation_detail",
        "admin_confirm_reservation",
        "admin_cancel_reservation",
        "admin_close_service_execution",
    ],
    "reservas": [
        "admin_list_reservations",
        "admin_get_reservation_detail",
        "admin_confirm_reservation",
        "admin_cancel_reservation",
        "admin_close_service_execution",
    ],
    "participante": ["admin_get_participant", "admin_update_participant"],
    "participantes": ["admin_get_participant", "admin_update_participant"],
    "pago": [
        "admin_get_payment_proof",
        "admin_approve_payment",
        "admin_reject_payment_proof",
        "admin_unverify_payment_proof",
        "admin_unreject_payment_proof",
    ],
    "comprobante": [
        "admin_get_payment_proof",
        "admin_approve_payment",
        "admin_reject_payment_proof",
        "admin_unverify_payment_proof",
        "admin_unreject_payment_proof",
    ],
    "venta": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
    ],
    "ventas": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
    ],
    "ingresos": ["admin_get_sales_summary"],
    "ingreso": ["admin_get_sales_summary"],
    "redes": ["admin_get_channel_performance"],
    "canal": ["admin_get_channel_performance"],
    "canales": ["admin_get_channel_performance"],
    "origen": ["admin_get_channel_performance"],
    "embudo": ["admin_get_reservation_funnel"],
    "ocupacion": ["admin_get_occupancy_report"],
    "ocupación": ["admin_get_occupancy_report"],
    "reporte": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
    ],
    "reportes": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
    ],
    "grafica": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
    ],
    "gráfica": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
    ],
    "analitica": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
    ],
    "analítica": [
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
    ],
    "configuracion": [
        "admin_get_system_config",
        "admin_update_reservation_rules",
        "admin_get_payment_instructions",
    ],
    "configuración": [
        "admin_get_system_config",
        "admin_update_reservation_rules",
        "admin_get_payment_instructions",
    ],
    "revision": ["admin_list_human_review_requests", "request_human_review"],
    "revisión": ["admin_list_human_review_requests", "request_human_review"],
    "cumpleaños": ["schedule_birthday_automation"],
    "aniversario": ["schedule_visit_anniversary_automation"],
    "proveedor": [
        "admin_list_providers",
        "admin_get_provider",
        "admin_create_provider",
        "admin_update_provider",
        "admin_deactivate_provider",
    ],
    "proveedores": [
        "admin_list_providers",
        "admin_get_provider",
        "admin_create_provider",
        "admin_update_provider",
        "admin_deactivate_provider",
    ],
    "silla": [
        "admin_list_saddles",
        "admin_get_saddle",
        "admin_create_saddle",
        "admin_update_saddle",
        "admin_deactivate_saddle",
        "admin_list_available_saddles_for_reservation",
    ],
    "sillas": [
        "admin_list_saddles",
        "admin_get_saddle",
        "admin_create_saddle",
        "admin_update_saddle",
        "admin_deactivate_saddle",
        "admin_list_available_saddles_for_reservation",
    ],
    "montura": [
        "admin_list_saddles",
        "admin_get_saddle",
        "admin_create_saddle",
        "admin_update_saddle",
        "admin_deactivate_saddle",
        "admin_list_available_saddles_for_reservation",
    ],
    "monturas": [
        "admin_list_saddles",
        "admin_get_saddle",
        "admin_create_saddle",
        "admin_update_saddle",
        "admin_deactivate_saddle",
        "admin_list_available_saddles_for_reservation",
    ],
    "asignacion": [
        "admin_get_assignment_board",
        "admin_create_assignment",
        "admin_update_assignment",
        "admin_delete_assignment",
        "admin_finalize_assignment",
        "admin_finalize_all_assignments",
    ],
    "asignación": [
        "admin_get_assignment_board",
        "admin_create_assignment",
        "admin_update_assignment",
        "admin_delete_assignment",
        "admin_finalize_assignment",
        "admin_finalize_all_assignments",
    ],
    "asignaciones": [
        "admin_get_assignment_board",
        "admin_create_assignment",
        "admin_update_assignment",
        "admin_delete_assignment",
        "admin_finalize_assignment",
        "admin_finalize_all_assignments",
    ],
    "tablero": ["admin_get_assignment_board"],
    "evento": [
        "admin_list_equine_events",
        "admin_create_equine_event",
        "admin_update_equine_event",
    ],
    "eventos": [
        "admin_list_equine_events",
        "admin_create_equine_event",
        "admin_update_equine_event",
    ],
    "emergencia": ["admin_get_emergency_contacts"],
    "emergencias": ["admin_get_emergency_contacts"],
}

# Descripciones breves de cada tool (categorizadas)
_ADMIN_TOOL_DESCRIPTIONS: dict[str, str] = {
    "admin_list_users": "Listar usuarios",
    "admin_create_user": "Crear usuario",
    "admin_update_user": "Actualizar usuario",
    "admin_deactivate_user": "Desactivar usuario",
    "admin_list_experiences_admin": "Listar experiencias",
    "admin_create_experience": "Crear experiencia",
    "admin_update_experience": "Actualizar experiencia",
    "admin_deactivate_experience": "Desactivar experiencia",
    "admin_get_sales_summary": "Reporte ventas",
    "admin_get_reservation_funnel": "Embudo conversión",
    "admin_get_channel_performance": "Rendimiento canal",
    "admin_get_occupancy_report": "Ocupación",
    "admin_get_equine_workload_report": "Carga equina",
    "admin_get_logistics_checklist": "Checklist logístico",
    "admin_close_service_execution": "Cerrar servicio",
    "admin_add_equine_health_event": "Evento salud equino",
    "admin_update_equine_availability": "Disponibilidad equino",
    "admin_get_system_config": "Config sistema",
    "admin_update_reservation_rules": "Reglas reserva",
    "admin_get_payment_instructions": "Instrucciones pago",
    "admin_list_human_review_requests": "Revisiones humanas",
    "admin_get_payment_proof": "Ver comprobante",
    "admin_approve_payment": "Aprobar pago",
    "admin_reject_payment_proof": "Rechazar comprobante",
    "admin_unverify_payment_proof": "Des-verificar",
    "admin_unreject_payment_proof": "Des-rechazar",
    "admin_list_reservations": "Listar reservas",
    "admin_get_reservation_detail": "Detalle reserva",
    "admin_confirm_reservation": "Confirmar reserva",
    "admin_cancel_reservation": "Cancelar reserva",
    "admin_list_equines": "Listar equinos",
    "admin_get_equine": "Detalle equino",
    "admin_create_equine": "Crear equino",
    "admin_update_equine": "Actualizar equino",
    "admin_deactivate_equine": "Desactivar equino",
    "admin_get_participant": "Detalle participante",
    "admin_update_participant": "Actualizar participante",
    "schedule_birthday_automation": "Cumpleaños",
    "schedule_visit_anniversary_automation": "Aniversario",
    "admin_list_providers": "Listar proveedores",
    "admin_get_provider": "Detalle proveedor",
    "admin_create_provider": "Crear proveedor",
    "admin_update_provider": "Actualizar proveedor",
    "admin_deactivate_provider": "Desactivar proveedor",
    "admin_list_saddles": "Listar sillas",
    "admin_get_saddle": "Detalle silla",
    "admin_create_saddle": "Crear silla",
    "admin_update_saddle": "Actualizar silla",
    "admin_deactivate_saddle": "Desactivar silla",
    "admin_list_available_saddles_for_reservation": "Sillas disponibles reserva",
    "admin_get_assignment_board": "Tablero asignación",
    "admin_create_assignment": "Crear asignación",
    "admin_update_assignment": "Actualizar asignación",
    "admin_delete_assignment": "Eliminar asignación",
    "admin_finalize_assignment": "Finalizar asignación",
    "admin_finalize_all_assignments": "Finalizar todas asignaciones",
    "admin_list_equine_events": "Listar eventos equino",
    "admin_create_equine_event": "Crear evento equino",
    "admin_update_equine_event": "Actualizar evento equino",
    "admin_get_emergency_contacts": "Contactos emergencia",
}


def _detect_relevant_admin_tools(user_message: str) -> list[str] | None:
    """Detecta qué tools admin son relevantes según el mensaje del usuario.
    Retorna None si no hay match (mostrar todas)."""
    msg_lower = user_message.lower()
    matched_tools: set[str] = set()
    for keyword, tools in _ADMIN_TOOL_CATEGORIES.items():
        if keyword in msg_lower:
            matched_tools.update(tools)
    return sorted(matched_tools) if matched_tools else None


def _build_admin_tools_prompt(tools: list[str]) -> str:
    """Construye la sección de tools admin con descripciones breves."""
    lines = ["HERRAMIENTAS ADMINISTRATIVAS - CANAL ADMIN:", ""]
    for tool in tools:
        desc = _ADMIN_TOOL_DESCRIPTIONS.get(tool, tool)
        lines.append(f"- {tool}: {desc}")
    lines.append("")
    lines.append("Reglas: herramientas de lectura (listar/consultar) sin restricciones.")
    lines.append(
        "Herramientas de escritura (crear/actualizar/desactivar) requieren confirmación implícita."
    )
    return "\n".join(lines)


class GeminiPlanner:
    def __init__(self) -> None:
        self.last_token_usage: dict[str, int] | None = None

    async def plan(
        self,
        *,
        user_message: str,
        channel: str,
        conversation_context: str | None = None,
        conversation_id: str | None = None,
        language: str = "es",
    ) -> AssistantPlan:
        logger.info(
            "[conversation_id=%s] LLM receives message | channel=%s",
            conversation_id,
            channel,
        )

        started = time.perf_counter()

        now = now_colombia()
        today_formatted = format_colombia_today_es()

        admin_tools_section = ""
        if channel == "admin_api":
            relevant = _detect_relevant_admin_tools(user_message)
            if relevant:
                admin_tools_section = _build_admin_tools_prompt(relevant)
                logger.info(
                    "[conversation_id=%s] Contextual filter: %d/%d tools shown",
                    conversation_id,
                    len(relevant),
                    len(_ADMIN_TOOL_DESCRIPTIONS),
                )
            else:
                # Fallback: show all but grouped by category
                admin_tools_section = _build_admin_tools_prompt(
                    sorted(_ADMIN_TOOL_DESCRIPTIONS.keys())
                )
                logger.info(
                    "[conversation_id=%s] No keyword match, showing all %d tools",
                    conversation_id,
                    len(_ADMIN_TOOL_DESCRIPTIONS),
                )

        language_instruction = build_language_instruction(language)
        tools_section = render_tools_for_prompt(channel)

        if channel == "admin_api":
            system_prompt = ADMIN_PLANNER_SYSTEM_PROMPT.format(
                today_formatted=today_formatted,
                today_year=str(now.year),
                admin_tools_section=admin_tools_section,
                language_instruction=language_instruction,
            )
        else:
            system_prompt = PLANNER_SYSTEM_PROMPT.format(
                today_formatted=today_formatted,
                today_year=str(now.year),
                tools_section=tools_section,
                admin_tools_section=admin_tools_section,
                language_instruction=language_instruction,
            )

        context = {
            "today": now.date().isoformat(),
            "today_description": today_formatted,
            "current_time": now.strftime("%H:%M"),
            "timezone": "America/Bogota",
            "channel": channel,
            "conversation_context": conversation_context or "",
            "user_message": user_message,
        }

        provider_result = get_llm_provider()
        provider = (
            await provider_result if inspect.isawaitable(provider_result) else provider_result
        )
        result = await provider.generate_structured(
            system=system_prompt,
            user=str(context),
            response_model=AssistantPlan,
            temperature=0.1,
            telemetry_context={"channel": channel, "conversation_id": conversation_id},
        )

        # Capturar tokens del último request
        self.last_token_usage = getattr(provider, "last_token_usage", None)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "[conversation_id=%s] LLM response | elapsed_ms=%d | action=%s | tool=%s | audit=%s",
            conversation_id,
            elapsed_ms,
            result.action.value if result.action else "none",
            result.tool_name or "none",
            (result.audit_summary or "none")[:200],
        )

        return result
