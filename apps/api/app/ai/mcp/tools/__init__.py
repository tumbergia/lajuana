from __future__ import annotations

from typing import Any

from app.ai.mcp.tools.availability import check_experience_availability
from app.ai.mcp.tools.catalog import list_experiences
from app.ai.mcp.tools.reservation_draft import (
    attach_payment_proof_to_reservation,
    create_reservation_draft,
    get_reservation_public_summary,
    get_reservation_status_by_phone,
)
from app.ai.mcp.tools.quote import quote_experience
from app.ai.mcp.tools.schedules import list_available_schedules, suggest_alternative_dates


# ── Stubs for tools not yet implemented ──────────────────────
async def get_experience_detail(**kwargs: Any) -> dict[str, Any]:
    from app.ai.mcp.tool_contracts import ExperienceDetailOutput

    return ExperienceDetailOutput(
        found=False,
        trace_id=kwargs.get("trace_id", ""),
    ).model_dump(mode="json")


async def get_public_business_rules(**kwargs: Any) -> dict[str, Any]:
    from app.ai.mcp.tool_contracts import PublicBusinessRulesOutput

    return PublicBusinessRulesOutput(
        trace_id=kwargs.get("trace_id", ""),
        family_focus="",
        alcohol_policy="",
        behavior_policy="",
        disclaimer="",
    ).model_dump(mode="json")


async def request_human_review(**kwargs: Any) -> dict[str, Any]:
    from uuid import uuid4

    from app.ai.mcp.tool_contracts import RequestHumanReviewOutput

    return RequestHumanReviewOutput(
        trace_id=kwargs.get("trace_id", ""),
        requested=True,
        review_id=str(uuid4()),
        status="open",
        message="Solicitud de revisión humana creada. Un asesor revisará tu caso.",
    ).model_dump(mode="json")


__all__ = [
    "check_experience_availability",
    "get_experience_detail",
    "get_public_business_rules",
    "list_available_schedules",
    "list_experiences",
    "quote_experience",
    "suggest_alternative_dates",
    "create_reservation_draft",
    "attach_payment_proof_to_reservation",
    "get_reservation_public_summary",
    "get_reservation_status_by_phone",
    "request_human_review",
]
