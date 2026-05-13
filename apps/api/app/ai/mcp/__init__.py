from app.ai.mcp.registry import registry
from app.ai.mcp import tools

registry.register("check_experience_availability", tools.check_experience_availability)
registry.register("get_experience_detail", tools.get_experience_detail)
registry.register("get_public_business_rules", tools.get_public_business_rules)
registry.register("list_available_schedules", tools.list_available_schedules)
registry.register("list_experiences", tools.list_experiences)
registry.register("quote_experience", tools.quote_experience)
registry.register("suggest_alternative_dates", tools.suggest_alternative_dates)
registry.register("request_human_review", tools.request_human_review)

__all__ = ["registry"]
