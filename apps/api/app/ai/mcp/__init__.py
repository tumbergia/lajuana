from app.ai.mcp.registry import registry
from app.ai.mcp.tools.availability import check_experience_availability
from app.ai.mcp.tools.catalog import list_experiences

registry.register("check_experience_availability", check_experience_availability)
registry.register("list_experiences", list_experiences)

__all__ = ["registry"]
