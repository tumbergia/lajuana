from mcp.server.fastmcp import FastMCP

from app.ai.mcp.tools.availability import check_experience_availability
from app.ai.mcp.tools.quote import quote_experience

mcp = FastMCP("lajuana-mcp")

mcp.tool(
    name="check_experience_availability",
    description=(
        "Consulta disponibilidad operativa para una experiencia de La Juana en una fecha "
        "y cantidad de participantes. No crea reservas, no confirma pagos y no modifica cupos."
    ),
)(check_experience_availability)

mcp.tool(
    name="quote_experience",
    description=(
        "Cotiza una experiencia segun numero de participantes y tarifas configuradas. "
        "No crea reservas, no confirma disponibilidad y no modifica cupos."
    ),
)(quote_experience)


if __name__ == "__main__":
    mcp.run()
