from app.ai.mcp.registry import registry
from app.ai.mcp.tools.availability import check_experience_availability
from app.ai.mcp.tools.catalog import list_experiences
from app.ai.mcp.tools.quote import quote_experience

registry.register("check_experience_availability", check_experience_availability)
registry.register("list_experiences", list_experiences)
registry.register("quote_experience", quote_experience)

__all__ = ["registry"]
