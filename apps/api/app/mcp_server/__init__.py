from app.mcp_server.registry import registry
from app.mcp_server.tools.availability import check_experience_availability

registry.register("check_experience_availability", check_experience_availability)

__all__ = ["registry"]
