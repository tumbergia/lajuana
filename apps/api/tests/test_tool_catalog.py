"""Tests for the compact tool catalog used by the planner prompt.

Validates:
- Catalog renders for each channel
- Channel-specific tool filtering (whatsapp/test only see client tools)
- Admin channel sees all tools
- Catalog stays under the size target
- All client tools previously hardcoded in the prompt remain available
"""

from __future__ import annotations

from app.ai.assistant.tool_catalog import (
    CHANNEL_ROLES,
    estimate_catalog_size_chars,
    get_tools_for_channel,
    render_tools_for_prompt,
)


def test_whatsapp_channel_sees_only_client_tools() -> None:
    tools = {t["name"] for t in get_tools_for_channel("whatsapp")}
    assert "list_experiences" in tools
    assert "get_experience_detail" in tools
    assert "get_all_experiences" in tools
    assert "check_experience_availability" in tools
    assert "quote_experience" in tools
    assert "create_reservation_draft" in tools
    assert "get_payment_instructions" in tools
    assert "request_human_review" in tools

    assert "admin_list_users" not in tools
    assert "admin_get_sales_summary" not in tools
    assert "guide_create_service_log" not in tools


def test_test_channel_matches_whatsapp() -> None:
    whatsapp_tools = {t["name"] for t in get_tools_for_channel("whatsapp")}
    test_tools = {t["name"] for t in get_tools_for_channel("test")}
    assert whatsapp_tools == test_tools


def test_mobile_api_includes_guide_tools() -> None:
    tools = {t["name"] for t in get_tools_for_channel("mobile_api")}
    assert "guide_create_service_log" in tools
    assert "guide_report_incident" in tools
    assert "admin_get_equine_workload" in tools
    assert "list_experiences" in tools
    assert "admin_list_users" not in tools


def test_admin_api_sees_all_tools() -> None:
    tools = {t["name"] for t in get_tools_for_channel("admin_api")}
    assert "admin_list_users" in tools
    assert "admin_get_sales_summary" in tools
    assert "guide_create_service_log" in tools
    assert "list_experiences" in tools


def test_unknown_channel_falls_back_to_client_only() -> None:
    tools = {t["name"] for t in get_tools_for_channel("unknown_channel")}
    assert "list_experiences" in tools
    assert "admin_list_users" not in tools


def test_catalog_includes_critical_client_tools() -> None:
    """Make sure the most-used WhatsApp tools remain in the catalog."""
    tools = {t["name"] for t in get_tools_for_channel("whatsapp")}
    expected = {
        "list_experiences",
        "get_experience_detail",
        "get_public_business_rules",
        "check_experience_availability",
        "list_available_schedules",
        "quote_experience",
        "suggest_alternative_dates",
        "create_reservation_draft",
        "get_reservation_public_summary",
        "get_reservation_status_by_phone",
        "cancel_reservation",
        "update_reservation_date",
        "update_reservation_participants",
        "attach_payment_proof_to_reservation",
        "get_payment_instructions",
        "request_human_review",
        "generate_participant_form_link",
        "get_participant_form_status",
        "send_post_service_message",
    }
    missing = expected - tools
    assert not missing, f"Missing client tools: {missing}"


def test_whatsapp_catalog_under_size_target() -> None:
    """Target: < 4000 chars of catalog (≈ 1000 tokens)."""
    size = estimate_catalog_size_chars("whatsapp")
    assert size < 4000, f"Catalog too large: {size} chars"


def test_admin_catalog_under_size_target() -> None:
    """Target: < 12000 chars even with all admin tools."""
    size = estimate_catalog_size_chars("admin_api")
    assert size < 12000, f"Catalog too large: {size} chars"


def test_rendered_catalog_mentions_header() -> None:
    rendered = render_tools_for_prompt("whatsapp")
    assert "TOOLS DISPONIBLES" in rendered
    assert "canal=whatsapp" in rendered


def test_channel_roles_canonical_set() -> None:
    assert "whatsapp" in CHANNEL_ROLES
    assert "test" in CHANNEL_ROLES
    assert "mobile_api" in CHANNEL_ROLES
    assert "admin_api" in CHANNEL_ROLES
    assert "client" in CHANNEL_ROLES["whatsapp"]
    assert "admin" in CHANNEL_ROLES["admin_api"]


def test_all_tools_have_required_metadata() -> None:
    """Sanity check: every tool must have a role, desc, and args (list)."""
    from app.ai.assistant.tool_catalog import _TOOL_CATALOG

    for name, meta in _TOOL_CATALOG.items():
        assert "role" in meta, f"{name} missing role"
        assert "desc" in meta, f"{name} missing desc"
        assert "args" in meta, f"{name} missing args"
        assert isinstance(meta["args"], list), f"{name} args must be a list"
        assert meta["role"] in {"client", "guide", "admin"}, f"{name} has invalid role"
