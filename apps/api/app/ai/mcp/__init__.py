from app.ai.mcp import tools
from app.ai.mcp.registry import registry

registry.register("check_experience_availability", tools.check_experience_availability)
registry.register("get_experience_detail", tools.get_experience_detail)
registry.register("get_public_business_rules", tools.get_public_business_rules)
registry.register("list_available_schedules", tools.list_available_schedules)
registry.register("list_experiences", tools.list_experiences)
registry.register("quote_experience", tools.quote_experience)
registry.register("suggest_alternative_dates", tools.suggest_alternative_dates)
registry.register("create_reservation_draft", tools.create_reservation_draft)
registry.register("attach_payment_proof_to_reservation", tools.attach_payment_proof_to_reservation)
registry.register("get_reservation_public_summary", tools.get_reservation_public_summary)
registry.register("get_reservation_status_by_phone", tools.get_reservation_status_by_phone)
registry.register("request_human_review", tools.request_human_review)

__all__ = ["registry"]
