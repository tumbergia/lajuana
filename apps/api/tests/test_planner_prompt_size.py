"""Guards against prompt token regression for the WhatsApp planner."""

from __future__ import annotations

from app.ai.assistant.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.ai.assistant.tool_catalog import estimate_catalog_size_chars, render_tools_for_prompt
from app.ai.language.messages import build_language_instruction


def _render_whatsapp_planner_prompt() -> str:
    return PLANNER_SYSTEM_PROMPT.format(
        today_formatted="jueves 16 de julio de 2026",
        today_year="2026",
        tools_section=render_tools_for_prompt("whatsapp"),
        admin_tools_section="",
        language_instruction=build_language_instruction("es"),
    )


def test_whatsapp_tool_catalog_is_compact() -> None:
    assert estimate_catalog_size_chars("whatsapp") < 4500


def test_rendered_whatsapp_planner_prompt_stays_under_size_budget() -> None:
    """System prompt must stay compact (~8–10k chars) to keep ~2.5k prompt tokens."""
    rendered = _render_whatsapp_planner_prompt()
    assert len(rendered) < 12_000, f"planner prompt grew to {len(rendered)} chars"
    assert "{tools_section}" not in rendered
    assert "list_experiences" in rendered
    assert "check_availability_and_quote" in rendered


def test_planner_prompt_uses_tools_section_placeholder() -> None:
    assert "{tools_section}" in PLANNER_SYSTEM_PROMPT
