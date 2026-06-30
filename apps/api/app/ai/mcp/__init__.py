"""MCP tool registry — auto-registered from a single dict.

Convention: tool names and function references live in one place
so adding a tool is a single-line change in _TOOLS.
"""

from app.ai.mcp import tools
from app.ai.mcp.registry import registry

_TOOLS: dict[str, object] = {
    # ── Admin: equine health & service ──
    "admin_add_equine_health_event": tools.admin_add_equine_health_event,
    "admin_close_service_execution": tools.admin_close_service_execution,
    # ── Admin: reports & analytics ──
    "admin_get_channel_performance": tools.admin_get_channel_performance,
    "admin_get_equine_workload": tools.admin_get_equine_workload,
    "admin_get_equine_workload_report": tools.admin_get_equine_workload_report,
    "admin_get_logistics_checklist": tools.admin_get_logistics_checklist,
    "admin_get_occupancy_report": tools.admin_get_occupancy_report,
    "admin_get_reservation_funnel": tools.admin_get_reservation_funnel,
    "admin_get_sales_summary": tools.admin_get_sales_summary,
    # ── Admin: equine availability ──
    "admin_update_equine_availability": tools.admin_update_equine_availability,
    # ── Admin: experiences ──
    "admin_create_experience": tools.admin_create_experience,
    "admin_update_experience": tools.admin_update_experience,
    "admin_list_experiences_admin": tools.admin_list_experiences_admin,
    "admin_deactivate_experience": tools.admin_deactivate_experience,
    # ── Admin: users ──
    "admin_list_users": tools.admin_list_users,
    "admin_create_user": tools.admin_create_user,
    "admin_update_user": tools.admin_update_user,
    "admin_deactivate_user": tools.admin_deactivate_user,
    # ── Admin: system ──
    "admin_get_system_config": tools.admin_get_system_config,
    "admin_update_reservation_rules": tools.admin_update_reservation_rules,
    "admin_get_payment_instructions": tools.admin_get_payment_instructions,
    "admin_list_human_review_requests": tools.admin_list_human_review_requests,
    # ── Client: availability & detail ──
    "check_experience_availability": tools.check_experience_availability,
    "get_experience_detail": tools.get_experience_detail,
    "get_public_business_rules": tools.get_public_business_rules,
    "list_available_schedules": tools.list_available_schedules,
    "list_experiences": tools.list_experiences,
    "quote_experience": tools.quote_experience,
    "suggest_alternative_dates": tools.suggest_alternative_dates,
    # ── Client: reservations ──
    "create_reservation_draft": tools.create_reservation_draft,
    "attach_payment_proof_to_reservation": tools.attach_payment_proof_to_reservation,
    "get_payment_instructions": tools.get_payment_instructions,
    "get_reservation_public_summary": tools.get_reservation_public_summary,
    "get_reservation_status_by_phone": tools.get_reservation_status_by_phone,
    "cancel_reservation": tools.cancel_reservation,
    "update_reservation_date": tools.update_reservation_date,
    "update_reservation_participants": tools.update_reservation_participants,
    "request_human_review": tools.request_human_review,
    "generate_participant_form_link": tools.generate_participant_form_link,
    "get_participant_form_status": tools.get_participant_form_status,
    # ── Guide ──
    "guide_create_service_log": tools.guide_create_service_log,
    "guide_report_incident": tools.guide_report_incident,
    "send_post_service_message": tools.send_post_service_message,
    # ── Automation ──
    "schedule_birthday_automation": tools.schedule_birthday_automation,
    "schedule_visit_anniversary_automation": tools.schedule_visit_anniversary_automation,
    # ── Admin CRUD: equines ──
    "admin_list_equines": tools.admin_list_equines,
    "admin_create_equine": tools.admin_create_equine,
    "admin_update_equine": tools.admin_update_equine,
    "admin_get_equine": tools.admin_get_equine,
    "admin_deactivate_equine": tools.admin_deactivate_equine,
    # ── Admin CRUD: reservations ──
    "admin_list_reservations": tools.admin_list_reservations,
    "admin_get_reservation_detail": tools.admin_get_reservation_detail,
    "admin_confirm_reservation": tools.admin_confirm_reservation,
    "admin_cancel_reservation": tools.admin_cancel_reservation,
    # ── Admin CRUD: participants ──
    "admin_get_participant": tools.admin_get_participant,
    "admin_update_participant": tools.admin_update_participant,
    # ── Admin CRUD: payment proofs ──
    "admin_approve_payment": tools.admin_approve_payment,
    "admin_get_payment_proof": tools.admin_get_payment_proof,
    "admin_reject_payment_proof": tools.admin_reject_payment_proof,
    "admin_unreject_payment_proof": tools.admin_unreject_payment_proof,
    "admin_unverify_payment_proof": tools.admin_unverify_payment_proof,
}

for name, fn in _TOOLS.items():
    registry.register(name, fn)

__all__ = ["registry"]
