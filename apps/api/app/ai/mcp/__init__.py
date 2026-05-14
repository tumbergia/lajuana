from app.ai.mcp import tools
from app.ai.mcp.registry import registry

registry.register("admin_add_equine_health_event", tools.admin_add_equine_health_event)
registry.register("admin_close_service_execution", tools.admin_close_service_execution)
registry.register("admin_get_equine_workload", tools.admin_get_equine_workload)
registry.register("admin_get_logistics_checklist", tools.admin_get_logistics_checklist)
registry.register("admin_update_equine_availability", tools.admin_update_equine_availability)
registry.register("check_experience_availability", tools.check_experience_availability)
registry.register("get_experience_detail", tools.get_experience_detail)
registry.register("get_public_business_rules", tools.get_public_business_rules)
registry.register("guide_create_service_log", tools.guide_create_service_log)
registry.register("guide_report_incident", tools.guide_report_incident)
registry.register("list_available_schedules", tools.list_available_schedules)
registry.register("list_experiences", tools.list_experiences)
registry.register("quote_experience", tools.quote_experience)
registry.register("suggest_alternative_dates", tools.suggest_alternative_dates)
registry.register("request_human_review", tools.request_human_review)

__all__ = ["registry"]
