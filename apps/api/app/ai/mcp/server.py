from mcp.server.fastmcp import FastMCP

from app.ai.mcp.tools import (
    admin_add_equine_health_event,
    admin_close_service_execution,
    admin_get_channel_performance,
    admin_get_equine_workload,
    admin_get_equine_workload_report,
    admin_get_logistics_checklist,
    admin_get_occupancy_report,
    admin_get_reservation_funnel,
    admin_get_sales_summary,
    admin_update_equine_availability,
    attach_payment_proof_to_reservation,
    cancel_reservation,
    check_experience_availability,
    create_reservation_draft,
    generate_participant_form_link,
    get_experience_detail,
    get_participant_form_status,
    get_public_business_rules,
    search_company_knowledge,
    get_reservation_public_summary,
    get_reservation_status_by_phone,
    guide_create_service_log,
    guide_report_incident,
    list_available_schedules,
    list_experiences,
    quote_experience,
    request_human_review,
    schedule_birthday_automation,
    schedule_visit_anniversary_automation,
    send_post_service_message,
    suggest_alternative_dates,
    update_reservation_date,
    update_reservation_participants,
)

# NOTE: This standalone MCP server exposes ALL registered tools without any
# authentication or channel-based filtering. Admin tools (admin_*, guide_*)
# are available here. For production use, consider splitting this into:
#   - client_mcp.py: only client-safe tools (no admin_/guide_ prefix)
#   - admin_mcp.py: full tool set behind proper auth
# The FastAPI endpoint /admin/ask uses the orchestrator with channel="admin_api"
# and policy-based tool filtering, which is the recommended path for admin access.
mcp = FastMCP("lajuana-mcp")

mcp.tool(
    name="attach_payment_proof_to_reservation",
    description=(
        "Adjunta un comprobante de pago recibido por WhatsApp a una reserva existente. "
        "El comprobante queda en revision y la reserva NO queda confirmada automaticamente."
    ),
)(attach_payment_proof_to_reservation)

mcp.tool(
    name="check_experience_availability",
    description=(
        "Consulta disponibilidad operativa para una experiencia de La Juana en una fecha "
        "y cantidad de participantes. No crea reservas, no confirma pagos y no modifica cupos."
    ),
)(check_experience_availability)

mcp.tool(
    name="get_experience_detail",
    description=(
        "Obtiene informacion detallada de una experiencia por ID o texto de busqueda. "
        "No verifica disponibilidad ni cotiza."
    ),
)(get_experience_detail)

mcp.tool(
    name="get_public_business_rules",
    description=(
        "Devuelve las reglas de negocio publicas de La Juana: "
        "politica de alcohol, comportamiento, restricciones y disclaimer."
    ),
)(get_public_business_rules)

mcp.tool(
    name="search_company_knowledge",
    description=(
        "Busca en la base de conocimiento estatica de La Juana: "
        "historia, fundadores, cultura, UNESCO, sostenibilidad. "
        "No inventa precios ni datos operativos live."
    ),
)(search_company_knowledge)

mcp.tool(
    name="list_available_schedules",
    description=(
        "Lista fechas y horarios disponibles para una experiencia. "
        "No crea reservas ni modifica cupos."
    ),
)(list_available_schedules)

mcp.tool(
    name="list_experiences",
    description=(
        "Lista las experiencias disponibles en La Juana. "
        "No verifica disponibilidad, no cotiza y no modifica datos."
    ),
)(list_experiences)

mcp.tool(
    name="quote_experience",
    description=(
        "Cotiza una experiencia segun numero de participantes y tarifas configuradas. "
        "No crea reservas, no confirma disponibilidad y no modifica cupos."
    ),
)(quote_experience)

mcp.tool(
    name="suggest_alternative_dates",
    description=(
        "Sugiere fechas alternativas cuando no hay disponibilidad en la fecha solicitada. "
        "No crea reservas ni modifica cupos."
    ),
)(suggest_alternative_dates)

mcp.tool(
    name="request_human_review",
    description=(
        "Crea una solicitud trazable de revision humana. "
        "No modifica reservas, no confirma pagos, no bloquea cupos."
    ),
)(request_human_review)

mcp.tool(
    name="create_reservation_draft",
    description=(
        "Crea una pre-reserva temporal con TTL configurable. "
        "No confirma la reserva ni el pago. Requiere quote_snapshot."
    ),
)(create_reservation_draft)

mcp.tool(
    name="generate_participant_form_link",
    description=(
        "Genera un enlace de formulario de participantes para una reserva confirmada. "
        "Retorna la URL que el titular debe reenviar a cada participante. "
        "No envia automaticamente el enlace. No recolecta datos por chat."
    ),
)(generate_participant_form_link)

mcp.tool(
    name="get_participant_form_status",
    description=(
        "Consulta el estado del formulario de participantes: "
        "cuantos han registrado sus datos, cuantos faltan y si esta completo o expirado. "
        "No expone datos personales ni medicos de los participantes."
    ),
)(get_participant_form_status)

mcp.tool(
    name="get_reservation_public_summary",
    description=(
        "Consulta el resumen publico de un borrador de reserva por su codigo. "
        "No modifica ningun dato."
    ),
)(get_reservation_public_summary)

mcp.tool(
    name="get_reservation_status_by_phone",
    description=(
        "Consulta el estado de una reserva por telefono del titular. No modifica ningun dato."
    ),
)(get_reservation_status_by_phone)

mcp.tool(
    name="cancel_reservation",
    description=(
        "Permite al titular de una reserva cancelarla por su propia cuenta. "
        "Solo funciona si la reserva aun no tiene pago registrado (estado pendiente). "
        "Requiere codigo de reserva y telefono del titular."
    ),
)(cancel_reservation)

mcp.tool(
    name="update_reservation_date",
    description=(
        "Permite al titular de una reserva cambiar la fecha si aun no ha pagado. "
        "Requiere codigo de reserva, telefono del titular y la nueva fecha. "
        "Verifica disponibilidad antes de actualizar."
    ),
)(update_reservation_date)

mcp.tool(
    name="update_reservation_participants",
    description=(
        "Permite al titular de una reserva cambiar la cantidad de participantes si aun no ha pagado. "
        "Requiere codigo de reserva, telefono del titular y nueva cantidad (1 a 8)."
    ),
)(update_reservation_participants)

mcp.tool(
    name="admin_get_logistics_checklist",
    description=(
        "Obtiene el checklist logistico para una reserva confirmada: "
        "estado, participantes, asignaciones, polizas y registro de llegada. "
        "No modifica datos."
    ),
)(admin_get_logistics_checklist)

mcp.tool(
    name="guide_create_service_log",
    description=(
        "Registra una entrada de bitacora de servicio para una reserva. "
        "Tipos: arrival, departure, checkpoint, closure, note. "
        "No modifica reservas, no confirma pagos."
    ),
)(guide_create_service_log)

mcp.tool(
    name="guide_report_incident",
    description=(
        "Reporta un incidente durante la ejecucion del servicio. "
        "Severidades: low, medium, high, critical. "
        "Queda asociado a la reserva, participante o equino."
    ),
)(guide_report_incident)

mcp.tool(
    name="admin_close_service_execution",
    description=(
        "Cierra operativamente una reserva confirmada. "
        "Transiciona el estado a COMPLETED y registra el cierre en bitacora. "
        "Accion critica: solo administradores."
    ),
)(admin_close_service_execution)

mcp.tool(
    name="admin_add_equine_health_event",
    description=(
        "Registra un evento de salud o bienestar para un equino. "
        "Tipos: health_check, injury, treatment, medication, rest, note. "
        "No modifica la disponibilidad del equino."
    ),
)(admin_add_equine_health_event)

mcp.tool(
    name="admin_get_equine_workload",
    description=(
        "Consulta la carga de trabajo de los equinos: "
        "asignaciones proximas, proxima fecha y disponibilidad actual. "
        "No modifica datos."
    ),
)(admin_get_equine_workload)

mcp.tool(
    name="admin_update_equine_availability",
    description=(
        "Actualiza la disponibilidad operacional de un equino. "
        "Requiere motivo. Accion critica: solo administradores."
    ),
)(admin_update_equine_availability)

mcp.tool(
    name="admin_get_sales_summary",
    description=(
        "Obtiene resumen de ventas: total de reservas, desglose por estado "
        "e ingreso total estimado. No modifica datos."
    ),
)(admin_get_sales_summary)

mcp.tool(
    name="admin_get_reservation_funnel",
    description=(
        "Obtiene el embudo de conversión de reservas: "
        "cantidad de reservas en cada estado y porcentaje de conversión. "
        "No modifica datos."
    ),
)(admin_get_reservation_funnel)

mcp.tool(
    name="admin_get_channel_performance",
    description=(
        "Obtiene rendimiento por canal de entrada: "
        "cantidad de reservas y confirmaciones por canal (WhatsApp, Instagram, etc.). "
        "No modifica datos."
    ),
)(admin_get_channel_performance)

mcp.tool(
    name="admin_get_occupancy_report",
    description=(
        "Obtiene reporte de ocupación: capacidad, reservas y porcentaje "
        "de ocupación por fecha y experiencia. No modifica datos."
    ),
)(admin_get_occupancy_report)

mcp.tool(
    name="admin_get_equine_workload_report",
    description=(
        "Obtiene reporte de carga de trabajo equina: "
        "asignaciones en un rango de fechas por equino. No modifica datos."
    ),
)(admin_get_equine_workload_report)

mcp.tool(
    name="send_post_service_message",
    description=(
        "Registra el envío de un mensaje post-servicio para una reserva completada. "
        "Requiere que la reserva esté en estado completada o confirmada."
    ),
)(send_post_service_message)

mcp.tool(
    name="schedule_birthday_automation",
    description=(
        "Activa o desactiva el envío automático de mensajes de cumpleaños. "
        "Consulta el estado actual si no se envía el parámetro enabled."
    ),
)(schedule_birthday_automation)

mcp.tool(
    name="schedule_visit_anniversary_automation",
    description=(
        "Activa o desactiva el envío automático de mensajes de aniversario de visita. "
        "Consulta el estado actual si no se envía el parámetro enabled."
    ),
)(schedule_visit_anniversary_automation)

if __name__ == "__main__":
    mcp.run()
