from mcp.server.fastmcp import FastMCP

from app.ai.mcp.tools import (
    admin_add_equine_health_event,
    admin_close_service_execution,
    admin_get_equine_workload,
    admin_get_logistics_checklist,
    admin_update_equine_availability,
    check_experience_availability,
    get_experience_detail,
    get_public_business_rules,
    guide_create_service_log,
    guide_report_incident,
    list_available_schedules,
    list_experiences,
    quote_experience,
    request_human_review,
    suggest_alternative_dates,
)

mcp = FastMCP("lajuana-mcp")

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

if __name__ == "__main__":
    mcp.run()
