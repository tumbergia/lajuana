from mcp.server.fastmcp import FastMCP

from app.ai.mcp.tools import (
    check_experience_availability,
    get_experience_detail,
    get_public_business_rules,
    list_available_schedules,
    list_experiences,
    quote_experience,
    suggest_alternative_dates,
    request_human_review,
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

if __name__ == "__main__":
    mcp.run()
