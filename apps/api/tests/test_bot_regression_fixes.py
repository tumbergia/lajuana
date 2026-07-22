"""Regression tests for WhatsApp bot fixes: list, languages, reserve flow."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.assistant.intent_router import _extract_experience_name, detect_and_build_plan
from app.ai.language.detector import RESPONSE_LANGUAGES, detect_explicit_language_request
from app.ai.language.messages import get_language_upper_token, t
from app.ai.mcp.tools.catalog import _build_list_response


def test_extract_hacer_una_reserva_para_experience() -> None:
    """User phrase that previously produced experience_query='quiero hacer una reserva'."""
    msg = "quiero hacer una reserva para la montaña de cristal 4 personas el 29 de agosto"
    name = _extract_experience_name(msg)
    assert name is not None
    assert "montaña" in name.lower() or "montana" in name.lower()
    assert "cristal" in name.lower()
    assert "quiero" not in name.lower()
    assert "reserva" not in name.lower()


def test_intent_router_hacer_una_reserva_uses_combined() -> None:
    plan = detect_and_build_plan(
        "quiero hacer una reserva para la montaña de cristal 4 personas el 29 de agosto"
    )
    assert plan is not None
    assert plan.tool_name == "check_availability_and_quote"
    assert plan.arguments.experience_query
    assert "cristal" in plan.arguments.experience_query.lower()
    assert plan.arguments.participant_count == 4
    assert plan.arguments.requested_date == "2026-08-29"


def test_intent_router_quiero_reservar_still_works() -> None:
    plan = detect_and_build_plan(
        "quiero reservar la montaña de cristal para el 5 de agosto 3 personas"
    )
    assert plan is not None
    assert plan.tool_name == "check_availability_and_quote"
    assert "cristal" in (plan.arguments.experience_query or "").lower()


def test_chinese_explicit_request_detected() -> None:
    assert detect_explicit_language_request("quiero continuar hablando en chino") == "zh"
    assert detect_explicit_language_request("háblame en chino") == "zh"


def test_language_upper_token_covers_eight_languages() -> None:
    expected = {
        "es": "ESPAÑOL",
        "en": "INGLÉS",
        "fr": "FRANCÉS",
        "de": "ALEMÁN",
        "it": "ITALIANO",
        "ru": "RUSO",
        "zh": "CHINO",
        "ja": "JAPONÉS",
    }
    for code, token in expected.items():
        assert get_language_upper_token(code) == token
    assert "zh" in RESPONSE_LANGUAGES
    assert RESPONSE_LANGUAGES >= {"es", "en", "fr", "de", "it", "ru", "zh", "ja"}


def test_quote_template_asks_name_email_not_soft_confirm() -> None:
    msg = t(
        "quote_experience_response",
        "es",
        experience_name="Montaña",
        participants=4,
        subtotal="1,000,000",
        unit_price="250,000",
    )
    assert "nombre" in msg.lower()
    assert "correo" in msg.lower()
    assert "¿te parece?" not in msg.lower()


def test_list_experiences_response_includes_all_items() -> None:
    items = [
        {"name": "Experiencia A", "starting_price": 100000},
        {"name": "Experiencia B", "starting_price": 200000},
        {"name": "Experiencia C", "starting_price": None},
    ]
    text = _build_list_response(items, "es")
    assert "Experiencia A" in text
    assert "Experiencia B" in text
    assert "Experiencia C" in text
    assert text.count("•") == 3


@pytest.mark.asyncio
async def test_list_experiences_tool_returns_response() -> None:
    from app.ai.mcp.tools import catalog as catalog_mod

    fake_exps = [
        SimpleNamespace(
            id="id-1",
            name="Fabrica",
            slug="fabrica",
            subtitle="Sub",
            description="Desc",
            pricing=SimpleNamespace(
                tiers=[SimpleNamespace(min_participants=1, max_participants=8, price_per_person=150000)]
            ),
            duration=SimpleNamespace(display_text="4h"),
            difficulty="EASY",
            level="EASY",
            duration_hours=4,
            duration_days=None,
            tags=[],
        ),
        SimpleNamespace(
            id="id-2",
            name="Montana",
            slug="montana",
            subtitle=None,
            description="Desc2",
            pricing=SimpleNamespace(
                tiers=[SimpleNamespace(min_participants=1, max_participants=8, price_per_person=250000)]
            ),
            duration=None,
            difficulty=None,
            level=None,
            duration_hours=None,
            duration_days=None,
            tags=[],
        ),
    ]
    query = SimpleNamespace(to_list=AsyncMock(return_value=fake_exps))
    with patch.object(catalog_mod.ExperienceDocument, "find", return_value=query):
        result = await catalog_mod.list_experiences(language="es", limit=20, trace_id="t1")
    assert result["total"] == 2
    assert result["response"]
    assert "Fabrica" in result["response"]
    assert "Montana" in result["response"]


def test_list_experiences_is_literal_tool() -> None:
    from app.ai.assistant.orchestrator import AssistantOrchestrator
    import inspect

    src = inspect.getsource(AssistantOrchestrator.ask)
    assert '"list_experiences"' in src
    assert '"quote_experience"' in src
    assert '"check_experience_availability"' in src
    assert '"get_all_experiences"' not in src
