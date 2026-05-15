from mcp.server.fastmcp import FastMCP

from app.ai.mcp.tools import (
    attach_payment_proof_to_reservation,
    check_experience_availability,
    create_reservation_draft,
    get_experience_detail,
    get_public_business_rules,
    get_reservation_public_summary,
    get_reservation_status_by_phone,
    list_available_schedules,
    list_experiences,
    quote_experience,
    request_human_review,
    suggest_alternative_dates,
)

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
    name="get_reservation_public_summary",
    description=(
        "Consulta el resumen publico de un borrador de reserva por su codigo. "
        "No modifica ningun dato."
    ),
)(get_reservation_public_summary)

mcp.tool(
    name="get_reservation_status_by_phone",
    description=(
        "Consulta el estado de una reserva por telefono del titular. "
        "No modifica ningun dato."
    ),
)(get_reservation_status_by_phone)

if __name__ == "__main__":
    mcp.run()
