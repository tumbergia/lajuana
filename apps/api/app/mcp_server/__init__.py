from app.mcp_server.registry import registry
from app.mcp_server.tools.availability import check_experience_availability
from app.mcp_server.tools.catalog import list_experiences

registry.register("check_experience_availability", check_experience_availability)
registry.register("list_experiences", list_experiences)

__all__ = ["registry"]
