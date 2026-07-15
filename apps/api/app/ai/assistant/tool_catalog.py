"""Catálogo compacto de tools para el system prompt del planner.

Cada tool se describe con el mínimo texto necesario para que el LLM elija
la herramienta correcta y complete sus argumentos. La descripción completa
vive en la tool misma; aquí solo va lo que el LLM debe saber para decidir.

Ahorro esperado frente al catálogo hardcodeado en el prompt:
~6.800 tokens de prompt -> ~2.500-3.000 tokens por turno del planner.
"""

from __future__ import annotations

from typing import Literal

ToolRole = Literal["client", "guide", "admin"]


_TOOL_CATALOG: dict[str, dict[str, object]] = {
    "list_experiences": {
        "role": "client",
        "desc": "Lista experiencias del catálogo (CRÍTICO: única fuente para saber qué se ofrece).",
        "args": ["is_active?:bool", "limit?:int"],
    },
    "get_experience_detail": {
        "role": "client",
        "desc": "Detalle de una experiencia: descripcion, duracion, incluye, precio desde.",
        "args": ["experience_id?", "experience_query?"],
    },
    "get_all_experiences": {
        "role": "client",
        "desc": "Lista TODAS las experiencias activas con TODOS sus campos (descripcion, pricing, inclusiones, etc). Usar cuando el usuario pide info de todas o lista completa.",
        "args": ["is_active?:bool=true", "limit?:int<=200=50"],
    },
    "get_public_business_rules": {
        "role": "client",
        "desc": "Ubicación, edades, anticipación, vencimiento de pre-reserva, comprobante obligatorio.",
        "args": [],
    },
    "check_experience_availability": {
        "role": "client",
        "desc": "Consulta disponibilidad para experiencia + fecha + participantes.",
        "args": ["experience_id|experience_query", "requested_date:YYYY-MM-DD", "participant_count:int"],
    },
    "check_availability_and_quote": {
        "role": "client",
        "desc": "Versión combinada: consulta disponibilidad Y cotiza en una sola llamada. Devuelve el `quote_snapshot` listo para `create_reservation_draft` y pregunta al usuario por nombre y correo. USAR cuando el usuario entrega experiencia + fecha + personas en un solo mensaje y quiere reservar (es el camino rápido, ahorra un turno).",
        "args": ["experience_id|experience_query", "requested_date:YYYY-MM-DD", "participant_count:int"],
    },
    "list_available_schedules": {
        "role": "client",
        "desc": "Lista fechas y horarios disponibles para una experiencia.",
        "args": ["experience_id|experience_query", "date_from?:YYYY-MM-DD", "date_to?:YYYY-MM-DD", "participant_count?:int", "limit?:int=10"],
    },
    "quote_experience": {
        "role": "client",
        "desc": "Cotiza experiencia según número de participantes y tarifas. No crea reservas.",
        "args": ["experience_id|experience_query", "participant_count:int", "requested_date?:YYYY-MM-DD", "notes?"],
    },
    "suggest_alternative_dates": {
        "role": "client",
        "desc": "Sugiere fechas alternativas cuando no hay disponibilidad.",
        "args": ["experience_id|experience_query", "requested_date:YYYY-MM-DD", "participant_count:int", "search_days_before?:int=15", "search_days_after?:int=30", "limit?:int=5"],
    },
    "create_reservation_draft": {
        "role": "client",
        "desc": "Crea pre-reserva con TTL. REQUIERE haber llamado antes check_experience_availability Y quote_experience.",
        "args": ["experience_id", "schedule_id?", "participant_count:int<=8", "holder_phone", "holder_name", "holder_email", "requested_date:YYYY-MM-DD", "quote_snapshot:object", "conversation_id"],
    },
    "get_reservation_public_summary": {
        "role": "client",
        "desc": "Estado de reserva por código + teléfono del titular.",
        "args": ["code", "holder_phone"],
    },
    "get_reservation_status_by_phone": {
        "role": "client",
        "desc": "Estado de reserva por teléfono del titular.",
        "args": ["holder_phone"],
    },
    "cancel_reservation": {
        "role": "client",
        "desc": "Cancela reserva del titular si aún no ha pagado.",
        "args": ["reservation_code", "holder_phone"],
    },
    "update_reservation_date": {
        "role": "client",
        "desc": "Cambia fecha de reserva del titular si aún no ha pagado.",
        "args": ["reservation_code", "holder_phone", "new_date:YYYY-MM-DD"],
    },
    "update_reservation_participants": {
        "role": "client",
        "desc": "Cambia número de participantes (1-8) de reserva del titular si aún no ha pagado.",
        "args": ["reservation_code", "holder_phone", "new_participant_count:int"],
    },
    "attach_payment_proof_to_reservation": {
        "role": "client",
        "desc": "Adjunta comprobante de pago (imagen/PDF) a una reserva.",
        "args": ["reservation_id", "whatsapp_message_id", "media_id", "media_mime_type", "filename?", "caption?", "from_phone", "public_reservation_code?"],
    },
    "get_payment_instructions": {
        "role": "client",
        "desc": "Entrega medios de pago configurados (Bancolombia o link Bold).",
        "args": ["bold_requested?:bool=false"],
    },
    "request_human_review": {
        "role": "client",
        "desc": "Crea solicitud trazable de revisión humana. No modifica reservas.",
        "args": ["conversation_id", "reason_code", "summary", "priority:low|normal|high|urgent"],
    },
    "generate_participant_form_link": {
        "role": "client",
        "desc": "Genera enlace de formulario de registro de participantes.",
        "args": ["reservation_id", "expires_in_hours?:int"],
    },
    "get_participant_form_status": {
        "role": "client",
        "desc": "Estado de un formulario de participantes.",
        "args": ["form_id"],
    },
    "send_post_service_message": {
        "role": "client",
        "desc": "Envía mensaje post-servicio al titular.",
        "args": ["reservation_id", "message", "template_key?"],
    },
    "guide_create_service_log": {
        "role": "guide",
        "desc": "Guía: crea bitácora de servicio.",
        "args": ["reservation_id", "log_type", "notes"],
    },
    "guide_report_incident": {
        "role": "guide",
        "desc": "Guía: reporta incidente en servicio.",
        "args": ["reservation_id", "incident_type", "severity", "description"],
    },
    "admin_get_equine_workload": {
        "role": "guide",
        "desc": "Carga de trabajo de equinos para una fecha.",
        "args": ["requested_date:YYYY-MM-DD"],
    },
    "admin_list_users": {
        "role": "admin",
        "desc": "Lista usuarios del sistema.",
        "args": ["role?", "status?", "limit?:int"],
    },
    "admin_create_user": {
        "role": "admin",
        "desc": "Crea usuario (email, password, role, datos personales).",
        "args": ["email", "password", "role:admin|guide|client", "name?", "phone?"],
    },
    "admin_update_user": {
        "role": "admin",
        "desc": "Actualiza datos de un usuario.",
        "args": ["user_id", "name?", "phone?", "role?", "status?"],
    },
    "admin_deactivate_user": {
        "role": "admin",
        "desc": "Desactiva un usuario (soft delete).",
        "args": ["user_id"],
    },
    "admin_list_experiences_admin": {
        "role": "admin",
        "desc": "Lista todas las experiencias (incluye inactivas).",
        "args": ["is_active?:bool", "limit?:int"],
    },
    "admin_create_experience": {
        "role": "admin",
        "desc": "Crea experiencia nueva.",
        "args": ["name", "slug", "description?", "duration_hours?:int", "difficulty?", "min_participants?:int", "max_participants?:int", "pricing?"],
    },
    "admin_update_experience": {
        "role": "admin",
        "desc": "Actualiza experiencia existente.",
        "args": ["experience_id", "name?", "description?", "duration_hours?", "max_participants?", "pricing?"],
    },
    "admin_deactivate_experience": {
        "role": "admin",
        "desc": "Desactiva experiencia.",
        "args": ["experience_id"],
    },
    "admin_list_equines": {
        "role": "admin",
        "desc": "Lista equinos del negocio.",
        "args": ["status?", "limit?:int"],
    },
    "admin_get_equine": {
        "role": "admin",
        "desc": "Detalle de un equino.",
        "args": ["equine_id"],
    },
    "admin_create_equine": {
        "role": "admin",
        "desc": "Crea equino nuevo.",
        "args": ["name", "breed?", "age?:int", "temperament?"],
    },
    "admin_update_equine": {
        "role": "admin",
        "desc": "Actualiza equino.",
        "args": ["equine_id", "name?", "status?", "temperament?"],
    },
    "admin_deactivate_equine": {
        "role": "admin",
        "desc": "Desactiva equino.",
        "args": ["equine_id"],
    },
    "admin_add_equine_health_event": {
        "role": "admin",
        "desc": "Registra evento de salud de un equino.",
        "args": ["equine_id", "event_type", "description", "severity?", "date?:YYYY-MM-DD"],
    },
    "admin_update_equine_availability": {
        "role": "admin",
        "desc": "Cambia disponibilidad de un equino para una fecha.",
        "args": ["equine_id", "requested_date:YYYY-MM-DD", "is_available:bool"],
    },
    "admin_list_reservations": {
        "role": "admin",
        "desc": "Lista reservas con filtros (fecha, estado, etc).",
        "args": ["date_from?:YYYY-MM-DD", "date_to?:YYYY-MM-DD", "status?", "limit?:int=50"],
    },
    "admin_get_reservation_detail": {
        "role": "admin",
        "desc": "Detalle completo de una reserva.",
        "args": ["reservation_id|code"],
    },
    "admin_confirm_reservation": {
        "role": "admin",
        "desc": "Confirma reserva (generalmente tras verificar pago).",
        "args": ["reservation_id", "notes?"],
    },
    "admin_cancel_reservation": {
        "role": "admin",
        "desc": "Cancela reserva desde admin.",
        "args": ["reservation_id", "reason"],
    },
    "admin_get_payment_proof": {
        "role": "admin",
        "desc": "Detalle de comprobante de pago.",
        "args": ["payment_proof_id"],
    },
    "admin_approve_payment": {
        "role": "admin",
        "desc": "Aprueba comprobante de pago.",
        "args": ["payment_proof_id", "notes?"],
    },
    "admin_reject_payment_proof": {
        "role": "admin",
        "desc": "Rechaza comprobante de pago.",
        "args": ["payment_proof_id", "reason"],
    },
    "admin_unverify_payment_proof": {
        "role": "admin",
        "desc": "Quita verificación a un comprobante aprobado.",
        "args": ["payment_proof_id", "reason"],
    },
    "admin_unreject_payment_proof": {
        "role": "admin",
        "desc": "Quita rechazo a un comprobante.",
        "args": ["payment_proof_id", "reason"],
    },
    "admin_get_sales_summary": {
        "role": "admin",
        "desc": "Reporte de ventas agregado.",
        "args": ["date_from?:YYYY-MM-DD", "date_to?:YYYY-MM-DD"],
    },
    "admin_get_reservation_funnel": {
        "role": "admin",
        "desc": "Embudo de conversión de reservas.",
        "args": ["date_from?:YYYY-MM-DD", "date_to?:YYYY-MM-DD"],
    },
    "admin_get_channel_performance": {
        "role": "admin",
        "desc": "Rendimiento por canal de venta.",
        "args": ["date_from?:YYYY-MM-DD", "date_to?:YYYY-MM-DD"],
    },
    "admin_get_occupancy_report": {
        "role": "admin",
        "desc": "Reporte de ocupación por experiencia y fecha.",
        "args": ["date_from?:YYYY-MM-DD", "date_to?:YYYY-MM-DD"],
    },
    "admin_get_equine_workload_report": {
        "role": "admin",
        "desc": "Reporte de carga de trabajo equina.",
        "args": ["date_from?:YYYY-MM-DD", "date_to?:YYYY-MM-DD"],
    },
    "admin_get_system_config": {
        "role": "admin",
        "desc": "Lee configuración actual del sistema.",
        "args": [],
    },
    "admin_update_reservation_rules": {
        "role": "admin",
        "desc": "Actualiza reglas de reserva (anticipación, comprobante, TTL).",
        "args": ["min_days_in_advance?:int", "require_payment_proof_for_confirmation?:bool", "reservation_draft_ttl_minutes?:int"],
    },
    "admin_get_payment_instructions": {
        "role": "admin",
        "desc": "Lee instrucciones de pago configuradas.",
        "args": [],
    },
    "admin_list_human_review_requests": {
        "role": "admin",
        "desc": "Lista solicitudes de revisión humana pendientes.",
        "args": ["status?:open|closed", "limit?:int"],
    },
    "admin_get_logistics_checklist": {
        "role": "admin",
        "desc": "Checklist logístico para una reserva.",
        "args": ["reservation_id"],
    },
    "admin_close_service_execution": {
        "role": "admin",
        "desc": "Cierra ejecución de un servicio realizado.",
        "args": ["reservation_id", "notes", "issues_encountered?"],
    },
    "admin_get_participant": {
        "role": "admin",
        "desc": "Detalle de un participante.",
        "args": ["participant_id"],
    },
    "admin_update_participant": {
        "role": "admin",
        "desc": "Actualiza datos de un participante.",
        "args": ["participant_id", "name?", "age?:int", "restrictions?"],
    },
    "admin_list_providers": {
        "role": "admin",
        "desc": "Lista proveedores.",
        "args": ["is_active?:bool", "limit?:int"],
    },
    "admin_get_provider": {
        "role": "admin",
        "desc": "Detalle de un proveedor.",
        "args": ["provider_id"],
    },
    "admin_create_provider": {
        "role": "admin",
        "desc": "Crea proveedor nuevo.",
        "args": ["name", "service_type", "phone?", "email?"],
    },
    "admin_update_provider": {
        "role": "admin",
        "desc": "Actualiza proveedor.",
        "args": ["provider_id", "name?", "phone?", "email?"],
    },
    "admin_deactivate_provider": {
        "role": "admin",
        "desc": "Desactiva proveedor.",
        "args": ["provider_id"],
    },
    "admin_list_saddles": {
        "role": "admin",
        "desc": "Lista sillas/monturas.",
        "args": ["is_active?:bool", "limit?:int"],
    },
    "admin_get_saddle": {
        "role": "admin",
        "desc": "Detalle de una silla/montura.",
        "args": ["saddle_id"],
    },
    "admin_create_saddle": {
        "role": "admin",
        "desc": "Crea silla/montura nueva.",
        "args": ["name", "type", "size?", "restrictions?"],
    },
    "admin_update_saddle": {
        "role": "admin",
        "desc": "Actualiza silla/montura.",
        "args": ["saddle_id", "name?", "size?", "restrictions?"],
    },
    "admin_deactivate_saddle": {
        "role": "admin",
        "desc": "Desactiva silla/montura.",
        "args": ["saddle_id"],
    },
    "admin_list_available_saddles_for_reservation": {
        "role": "admin",
        "desc": "Lista sillas disponibles para una reserva.",
        "args": ["reservation_id", "requested_date:YYYY-MM-DD"],
    },
    "admin_get_assignment_board": {
        "role": "admin",
        "desc": "Tablero de asignaciones equino-silla para una reserva.",
        "args": ["reservation_id", "reservation_code?"],
    },
    "admin_create_assignment": {
        "role": "admin",
        "desc": "Crea asignación equino-silla-participante.",
        "args": ["reservation_id", "equine_id", "saddle_id", "participant_id"],
    },
    "admin_update_assignment": {
        "role": "admin",
        "desc": "Actualiza asignación.",
        "args": ["assignment_id", "equine_id?", "saddle_id?", "participant_id?"],
    },
    "admin_delete_assignment": {
        "role": "admin",
        "desc": "Elimina asignación.",
        "args": ["assignment_id"],
    },
    "admin_finalize_assignment": {
        "role": "admin",
        "desc": "Finaliza una asignación individual.",
        "args": ["assignment_id"],
    },
    "admin_finalize_all_assignments": {
        "role": "admin",
        "desc": "Finaliza todas las asignaciones de una reserva.",
        "args": ["reservation_id"],
    },
    "admin_list_equine_events": {
        "role": "admin",
        "desc": "Lista eventos de equinos (salud, operación).",
        "args": ["equine_id?", "event_type?", "limit?:int"],
    },
    "admin_create_equine_event": {
        "role": "admin",
        "desc": "Crea evento de equino.",
        "args": ["equine_id", "event_type", "description", "date?:YYYY-MM-DD"],
    },
    "admin_update_equine_event": {
        "role": "admin",
        "desc": "Actualiza evento de equino.",
        "args": ["event_id", "description?", "date?"],
    },
    "admin_get_emergency_contacts": {
        "role": "admin",
        "desc": "Lista contactos de emergencia configurados.",
        "args": [],
    },
    "schedule_birthday_automation": {
        "role": "admin",
        "desc": "Programa automatización de cumpleaños.",
        "args": ["contact_phone", "birth_date:YYYY-MM-DD", "name"],
    },
    "schedule_visit_anniversary_automation": {
        "role": "admin",
        "desc": "Programa automatización de aniversario de visita.",
        "args": ["contact_phone", "visit_date:YYYY-MM-DD", "name"],
    },
}


CHANNEL_ROLES: dict[str, set[ToolRole]] = {
    "whatsapp": {"client"},
    "test": {"client"},
    "mobile_api": {"client", "guide"},
    "admin_api": {"client", "guide", "admin"},
}


def get_tools_for_channel(channel: str) -> list[dict[str, object]]:
    """Devuelve el catálogo de tools visibles para un canal dado."""
    roles = CHANNEL_ROLES.get(channel, {"client"})
    return [
        {"name": name, **meta}
        for name, meta in _TOOL_CATALOG.items()
        if meta.get("role") in roles
    ]


def render_tools_for_prompt(channel: str) -> str:
    """Renderiza el catálogo en texto compacto para inyectar en el system prompt."""
    tools = get_tools_for_channel(channel)
    if not tools:
        return ""

    lines = ["TOOLS DISPONIBLES (canal=" + channel + "):", ""]
    for tool in tools:
        name = tool["name"]
        desc = tool["desc"]
        args = tool.get("args", [])
        if args:
            arg_str = ", ".join(str(a) for a in args)
            lines.append(f"- {name}({arg_str}): {desc}")
        else:
            lines.append(f"- {name}(): {desc}")
    return "\n".join(lines)


def estimate_catalog_size_chars(channel: str) -> int:
    """Helper para tests: tamaño aproximado del catálogo renderizado."""
    return len(render_tools_for_prompt(channel))
