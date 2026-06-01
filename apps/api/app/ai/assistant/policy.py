from dataclasses import dataclass

from app.core.config import settings
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    reason: str | None = None


class ToolPolicyEngine:
    CLIENT_TOOLS: set[str] = {
        "list_experiences",
        "get_experience_detail",
        "get_public_business_rules",
        "check_experience_availability",
        "list_available_schedules",
        "quote_experience",
        "suggest_alternative_dates",
        "get_reservation_public_summary",
        "get_reservation_status_by_phone",
        "create_reservation_draft",
        "attach_payment_proof_to_reservation",
        "request_human_review",
        "generate_participant_form_link",
        "get_participant_form_status",
        "send_post_service_message",
    }
    GUIDE_TOOLS: set[str] = {
        "guide_create_service_log",
        "guide_report_incident",
        "admin_get_equine_workload",
    }
    ADMIN_TOOLS: set[str] = {
        "admin_get_logistics_checklist",
        "admin_close_service_execution",
        "admin_add_equine_health_event",
        "admin_update_equine_availability",
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
        "admin_create_experience",
        "admin_update_experience",
        "admin_list_experiences_admin",
        "admin_deactivate_experience",
        "admin_list_users",
        "admin_create_user",
        "admin_update_user",
        "admin_deactivate_user",
        "admin_create_schedule",
        "admin_update_schedule",
        "admin_list_schedules_admin",
        "admin_deactivate_schedule",
        "admin_get_system_config",
        "admin_update_reservation_rules",
        "admin_get_payment_instructions",
        "schedule_birthday_automation",
        "schedule_visit_anniversary_automation",
        "admin_list_human_review_requests",
        "admin_get_payment_proof",
        "admin_approve_payment",
        "admin_reject_payment_proof",
        "admin_unverify_payment_proof",
        "admin_unreject_payment_proof",
        "admin_list_reservations",
        "admin_get_reservation_detail",
        "admin_confirm_reservation",
        "admin_cancel_reservation",
        "admin_list_equines",
        "admin_get_equine",
        "admin_create_equine",
        "admin_update_equine",
        "admin_deactivate_equine",
        "admin_get_participant",
        "admin_update_participant",
    }
    READ_TOOLS = {
        "list_experiences",
        "get_experience_detail",
        "get_public_business_rules",
        "check_experience_availability",
        "list_available_schedules",
        "quote_experience",
        "suggest_alternative_dates",
        "get_reservation_public_summary",
        "get_reservation_status_by_phone",
        "admin_get_logistics_checklist",
        "admin_get_equine_workload",
        "admin_get_sales_summary",
        "admin_get_reservation_funnel",
        "admin_get_channel_performance",
        "admin_get_occupancy_report",
        "admin_get_equine_workload_report",
        "admin_list_experiences_admin",
        "admin_list_users",
        "admin_list_schedules_admin",
        "admin_get_system_config",
        "admin_get_payment_instructions",
        "admin_list_human_review_requests",
        "admin_get_payment_proof",
        "admin_list_reservations",
        "admin_get_reservation_detail",
        "admin_list_equines",
        "admin_get_equine",
        "admin_get_participant",
    }
    LIMITED_WRITE_TOOLS = {
        "request_human_review",
        "create_reservation_draft",
        "attach_payment_proof_to_reservation",
        "guide_create_service_log",
        "admin_add_equine_health_event",
        "send_post_service_message",
        "generate_participant_form_link",
        "get_participant_form_status",
        "admin_create_user",
        "admin_update_user",
        "admin_update_equine",
        "admin_update_participant",
    }
    WRITE_TOOLS: set[str] = {
        "guide_report_incident",
        "admin_close_service_execution",
        "admin_update_equine_availability",
        "schedule_birthday_automation",
        "schedule_visit_anniversary_automation",
        "admin_create_experience",
        "admin_update_experience",
        "admin_deactivate_experience",
        "admin_deactivate_user",
        "admin_create_schedule",
        "admin_update_schedule",
        "admin_deactivate_schedule",
        "admin_update_reservation_rules",
        "admin_approve_payment",
        "admin_reject_payment_proof",
        "admin_unverify_payment_proof",
        "admin_unreject_payment_proof",
        "admin_confirm_reservation",
        "admin_cancel_reservation",
        "admin_create_equine",
        "admin_deactivate_equine",
    }
    CRITICAL_TOOLS: set[str] = {
        "confirm_reservation",
        "cancel_reservation",
        "mark_payment_verified",
        "change_schedule_capacity",
        "block_slots",
    }

    CHANNEL_ROLE_MAP: dict[str, str] = {
        "whatsapp": "client",
        "test": "client",
        "admin_api": "admin",
        "mobile_api": "guide",
    }

    def _get_role_for_channel(self, channel: str) -> str:
        return self.CHANNEL_ROLE_MAP.get(channel, "client")

    def _get_allowed_tools_for_role(self, role: str) -> set[str]:
        if role == "admin":
            return self.CLIENT_TOOLS | self.GUIDE_TOOLS | self.ADMIN_TOOLS
        if role == "guide":
            return self.CLIENT_TOOLS | self.GUIDE_TOOLS
        return self.CLIENT_TOOLS

    def validate(self, plan: AssistantPlan, channel: str = "whatsapp") -> ToolPolicyDecision:
        if plan.confidence < settings.assistant_min_plan_confidence:
            return ToolPolicyDecision(
                allowed=False,
                reason="low_confidence",
            )

        if plan.action != AssistantAction.TOOL_CALL:
            return ToolPolicyDecision(allowed=True)

        if not plan.tool_name:
            return ToolPolicyDecision(
                allowed=False,
                reason="missing_tool_name",
            )

        role = self._get_role_for_channel(channel)
        allowed = self._get_allowed_tools_for_role(role)

        if plan.tool_name not in allowed:
            return ToolPolicyDecision(
                allowed=False,
                reason="tool_not_allowed_for_channel",
            )

        if plan.tool_name in self.CRITICAL_TOOLS:
            return ToolPolicyDecision(
                allowed=False,
                reason="critical_tool_denied",
            )

        if plan.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            return ToolPolicyDecision(
                allowed=False,
                reason="high_risk_requires_human",
            )

        if plan.needs_human:
            return ToolPolicyDecision(
                allowed=False,
                reason="human_review_required",
            )

        is_unknown = (
            plan.tool_name not in self.READ_TOOLS
            and plan.tool_name not in self.LIMITED_WRITE_TOOLS
            and plan.tool_name not in self.WRITE_TOOLS
        )
        if is_unknown:
            return ToolPolicyDecision(
                allowed=False,
                reason="unknown_or_not_allowed_tool",
            )

        if plan.tool_name == "check_experience_availability":
            required = {"requested_date", "participant_count"}
            args = plan.arguments.model_dump()
            missing = [key for key in required if key not in args or args[key] in {None, ""}]
            if missing:
                return ToolPolicyDecision(
                    allowed=False,
                    reason=f"missing_required_arguments:{','.join(missing)}",
                )

        if plan.tool_name == "quote_experience":
            args = plan.arguments.model_dump()
            has_experience = args.get("experience_id") not in {None, ""} or args.get(
                "experience_query"
            ) not in {None, ""}
            has_participants = args.get("participant_count") not in {None, ""}
            if not has_experience:
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:experience_id_or_experience_query",
                )
            if not has_participants:
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:participant_count",
                )

        return ToolPolicyDecision(allowed=True)
