from mcp.server.fastmcp import FastMCP

from app.mcp_server.tools.availability import check_experience_availability

mcp = FastMCP("lajuana-mcp")

mcp.tool(
    name="check_experience_availability",
    description=(
        "Consulta disponibilidad operativa para una experiencia de La Juana en una fecha "
        "y cantidad de participantes. No crea reservas, no confirma pagos y no modifica cupos."
    ),
)(check_experience_availability)


if __name__ == "__main__":
    mcp.run()
