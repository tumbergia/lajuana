from dataclasses import dataclass

from app.core.config import settings
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    reason: str | None = None


class ToolPolicyEngine:
    READ_TOOLS = {"check_experience_availability", "list_experiences", "quote_experience"}
    WRITE_TOOLS: set[str] = set()
    CRITICAL_TOOLS: set[str] = {
        "confirm_reservation",
        "cancel_reservation",
        "mark_payment_verified",
        "change_schedule_capacity",
        "block_slots",
    }

    def validate(self, plan: AssistantPlan) -> ToolPolicyDecision:
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

        if plan.tool_name not in self.READ_TOOLS and plan.tool_name not in self.WRITE_TOOLS:
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
            has_experience = (
                args.get("experience_id") not in {None, ""}
                or args.get("experience_query") not in {None, ""}
            )
            has_participants = (
                args.get("participant_count") not in {None, ""}
                or args.get("participants_count") not in {None, ""}
            )
            if not has_experience:
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:experience_id_or_experience_query",
                )
            if not has_participants:
                return ToolPolicyDecision(
                    allowed=False,
                    reason="missing_required_arguments:participant_count_or_participants_count",
                )

        return ToolPolicyDecision(allowed=True)
