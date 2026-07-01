import difflib
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import logger
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
        "cancel_reservation",
        "update_reservation_date",
        "update_reservation_participants",
        "get_payment_instructions",
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
        "admin_list_providers",
        "admin_get_provider",
        "admin_create_provider",
        "admin_update_provider",
        "admin_deactivate_provider",
        "admin_list_saddles",
        "admin_get_saddle",
        "admin_create_saddle",
        "admin_update_saddle",
        "admin_deactivate_saddle",
        "admin_list_available_saddles_for_reservation",
        "admin_get_assignment_board",
        "admin_create_assignment",
        "admin_update_assignment",
        "admin_delete_assignment",
        "admin_finalize_assignment",
        "admin_finalize_all_assignments",
        "admin_list_equine_events",
        "admin_create_equine_event",
        "admin_update_equine_event",
        "admin_get_emergency_contacts",
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
        "admin_get_system_config",
        "admin_get_payment_instructions",
        "admin_list_human_review_requests",
        "admin_get_payment_proof",
        "admin_list_reservations",
        "admin_get_reservation_detail",
        "admin_list_equines",
        "admin_get_equine",
        "admin_get_participant",
        "get_payment_instructions",
        "admin_list_providers",
        "admin_get_provider",
        "admin_list_saddles",
        "admin_get_saddle",
        "admin_list_available_saddles_for_reservation",
        "admin_get_assignment_board",
        "admin_list_equine_events",
        "admin_get_emergency_contacts",
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
        "admin_update_provider",
        "admin_update_saddle",
        "admin_update_assignment",
        "admin_update_equine_event",
        "cancel_reservation",
        "update_reservation_date",
        "update_reservation_participants",
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
        "admin_update_reservation_rules",
        "admin_approve_payment",
        "admin_reject_payment_proof",
        "admin_unverify_payment_proof",
        "admin_unreject_payment_proof",
        "admin_confirm_reservation",
        "admin_cancel_reservation",
        "admin_create_equine",
        "admin_deactivate_equine",
        "admin_create_provider",
        "admin_deactivate_provider",
        "admin_create_saddle",
        "admin_deactivate_saddle",
        "admin_create_assignment",
        "admin_delete_assignment",
        "admin_finalize_assignment",
        "admin_finalize_all_assignments",
        "admin_create_equine_event",
    }
    CRITICAL_TOOLS: set[str] = {
        "confirm_reservation",
        "mark_payment_verified",
    }
    ADMIN_BLOCKED_CLIENT_TOOLS: set[str] = {
        "get_reservation_status_by_phone",
        "get_reservation_public_summary",
        "cancel_reservation",
        "update_reservation_date",
        "update_reservation_participants",
        "create_reservation_draft",
        "attach_payment_proof_to_reservation",
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

    def _autocorrect_tool_name(self, tool_name: str, allowed: set[str]) -> str:
        """Autocorrege typos en el nombre de la tool usando difflib.
        
        Solo autocorrige si:
        1. La tool original no existe en ningún conjunto (typo real)
        2. La corrección está en el set de tools permitidas
        3. Nunca autocorrige CRITICAL_TOOLS
        """
        if tool_name in allowed:
            return tool_name
        
        # No autocorregir si la tool existe en CRITICAL_TOOLS
        all_known = self.CLIENT_TOOLS | self.GUIDE_TOOLS | self.ADMIN_TOOLS | self.CRITICAL_TOOLS
        if tool_name in all_known:
            return tool_name  # Es una tool conocida, no un typo
        
        # Solo autocorregir si la tool original parece un typo (no está en ningún set conocido)
        matches = difflib.get_close_matches(tool_name, allowed, n=1, cutoff=0.75)
        if matches:
            return matches[0]
        return tool_name

    def _validate_tool_args(self, plan: AssistantPlan) -> ToolPolicyDecision | None:
        """Valida argumentos específicos por tool. Retorna None si pasa, o ToolPolicyDecision si falla."""
        args = plan.arguments.model_dump() if plan.arguments else {}

        # Tools que requieren un ID específico
        id_required_tools = {
            "admin_update_experience": "experience_id",
            "admin_deactivate_experience": "experience_id",
            "admin_update_user": "user_id",
            "admin_deactivate_user": "user_id",
            "admin_update_equine": "equine_id",
            "admin_deactivate_equine": "equine_id",
            "admin_get_equine": "equine_id",
            "admin_add_equine_health_event": "equine_id",
            "admin_update_equine_availability": "equine_id",
            "admin_get_participant": "participant_id",
            "admin_update_participant": "participant_id",
            "admin_get_reservation_detail": "reservation_id",
            "admin_confirm_reservation": "reservation_id",
            "admin_cancel_reservation": "reservation_id",
            "admin_close_service_execution": "reservation_id",
            "admin_get_payment_proof": "payment_proof_id",
            "admin_approve_payment": "payment_proof_id",
            "admin_reject_payment_proof": "payment_proof_id",
            "admin_unverify_payment_proof": "payment_proof_id",
            "admin_unreject_payment_proof": "payment_proof_id",
        }
        if plan.tool_name in id_required_tools:
            required_field = id_required_tools[plan.tool_name]
            value = args.get(required_field)
            if not value or str(value).strip() == "":
                return ToolPolicyDecision(
                    allowed=False,
                    reason=f"missing_required_arguments:{required_field}",
                )

        # Tools que requieren datos de creación
        if plan.tool_name == "admin_create_experience":
            if not args.get("name") or not args.get("slug"):
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:name,slug",
                )

        if plan.tool_name == "admin_create_user":
            if not args.get("email") or not args.get("password"):
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:email,password",
                )

        if plan.tool_name == "admin_create_equine":
            if not args.get("name"):
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:name",
                )

        if plan.tool_name == "admin_update_reservation_rules":
            if not any(k in args for k in ("min_days_in_advance", "require_payment_proof_for_confirmation", "reservation_draft_ttl_minutes")):
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:min_days_in_advance_or_require_payment_proof_or_ttl",
                )

        return None

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

        # Autocorrección de typos en nombre de tool
        original_name = plan.tool_name
        plan.tool_name = self._autocorrect_tool_name(plan.tool_name, allowed)
        if original_name != plan.tool_name:
            logger.info("Tool name autocorrected: %s → %s", original_name, plan.tool_name)

        if plan.tool_name not in allowed:
            return ToolPolicyDecision(
                allowed=False,
                reason="tool_not_allowed_for_channel",
            )

        if channel == "admin_api" and plan.tool_name in self.ADMIN_BLOCKED_CLIENT_TOOLS:
            return ToolPolicyDecision(
                allowed=False,
                reason="admin_use_operational_tools",
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

        # Validación de argumentos específicos por tool
        args_validation = self._validate_tool_args(plan)
        if args_validation is not None:
            return args_validation

        return ToolPolicyDecision(allowed=True)
