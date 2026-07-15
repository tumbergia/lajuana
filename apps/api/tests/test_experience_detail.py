"""Tests for get_experience_detail end-to-end with mocked ExperienceDocument.

Validates:
- Returns all fields from the document (not just a subset)
- Fuzzy matching finds experiences by partial name
- Singular/plural variants work
- Returns 'not found' for non-existent experiences
- Aliases are searched as fallback
- Tags are searched as fallback
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


def _make_exp(
    name: str = "Fabrica de Cemento",
    slug: str = "fabrica-de-cemento",
    description: str = "Recorrido por la antigua fabrica de cementos.",
    subtitle: str | None = "Cementos Caldas",
    aliases: list[str] | None = None,
    tags: list[str] | None = None,
    pricing_currency: str = "COP",
    pricing_tiers: list | None = None,
    inclusions_items: list | None = None,
    duration_hours: int | None = 4,
    duration_minutes: int | None = 240,
) -> SimpleNamespace:
    return SimpleNamespace(
        id="exp-001",
        name=name,
        slug=slug,
        subtitle=subtitle,
        description=description,
        image_url="https://example.com/img.jpg",
        level="INTERMEDIATE",
        difficulty="INTERMEDIATE",
        category="EXPERIENCE",
        status="PUBLISHED",
        is_active=True,
        duration=SimpleNamespace(
            activity_minutes=duration_minutes,
            route_minutes=60,
            display_text="4 horas",
        ),
        route_details=SimpleNamespace(
            distance_km=12.5,
            terrain="Mixto",
            terrain_notes="Sendero con pendientes",
        ),
        pricing=SimpleNamespace(
            currency=pricing_currency,
            prices_are_net=True,
            pricing_notes="Incluye refrigerio",
            tiers=pricing_tiers
            or [
                SimpleNamespace(min_participants=1, max_participants=2, price_per_person=150000),
                SimpleNamespace(min_participants=3, max_participants=8, price_per_person=120000),
            ],
        ),
        inclusions=SimpleNamespace(
            items=inclusions_items or ["Guia", "Refrigerio", "Seguro"],
            display_text="Incluye guia, refrigerio y seguro",
        ),
        standard_max_participants=8,
        min_participants=1,
        base_capacity=8,
        duration_hours=duration_hours,
        duration_days=None,
        tags=tags or ["cemento", "industrial"],
        aliases=aliases or ["Fabrica de Cementos", "Cementos Caldas"],
    )


def _patch_experience_and_log(exp):
    """Patch ExperienceDocument.find_all and ToolCallLogDocument.insert for a test.

    In Beanie, `find_all()` is sync and returns a query object.
    The query's `.to_list()` is async and returns the list of docs.
    """
    from unittest.mock import MagicMock

    from app.documents import tool_call_log_document

    query_mock = SimpleNamespace(to_list=AsyncMock(return_value=[exp]))

    # Build a mock class that accepts any kwargs and has an async insert method
    mock_log_doc_class = MagicMock()
    mock_instance = MagicMock()
    mock_instance.insert = AsyncMock()
    mock_log_doc_class.return_value = mock_instance

    return (
        patch("app.documents.ExperienceDocument.find_all", return_value=query_mock),
        patch.object(tool_call_log_document, "ToolCallLogDocument", mock_log_doc_class),
    )


@pytest.mark.asyncio
async def test_get_experience_detail_returns_all_fields() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp()

    exp_patch, log_patch = _patch_experience_and_log(exp)
    with exp_patch, log_patch:
        result = await get_experience_detail(
            experience_query="Fabrica de Cementos",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "Fabrica de Cemento"
    assert result["slug"] == "fabrica-de-cemento"
    assert result["subtitle"] == "Cementos Caldas"
    assert result["description"] == "Recorrido por la antigua fabrica de cementos."
    assert result["image_url"] == "https://example.com/img.jpg"
    assert result["level"] == "INTERMEDIATE"
    assert result["difficulty"] == "INTERMEDIATE"
    assert result["category"] == "EXPERIENCE"
    assert result["status"] == "PUBLISHED"
    assert result["is_active"] is True
    assert result["duration_hours"] == 4
    assert result["base_capacity"] == 8
    assert result["min_participants"] == 1
    assert result["standard_max_participants"] == 8
    assert result["duration"] == "4 horas"
    assert result["includes"] == ["Guia", "Refrigerio", "Seguro"]
    assert result["inclusions_display_text"] == "Incluye guia, refrigerio y seguro"
    assert result["tags"] == ["cemento", "industrial"]
    assert result["aliases"] == ["Fabrica de Cementos", "Cementos Caldas"]
    assert result["currency"] == "COP"
    assert result["starting_price"] == 120000

    # Pricing details
    assert result["pricing"] is not None
    assert result["pricing"]["currency"] == "COP"
    assert result["pricing"]["prices_are_net"] is True
    assert result["pricing"]["pricing_notes"] == "Incluye refrigerio"
    assert len(result["pricing"]["tiers"]) == 2
    assert result["pricing"]["tiers"][0]["min_participants"] == 1
    assert result["pricing"]["tiers"][0]["max_participants"] == 2
    assert result["pricing"]["tiers"][0]["price_per_person"] == 150000

    # Route details
    assert result["route_details"] is not None
    assert result["route_details"]["distance_km"] == 12.5
    assert result["route_details"]["terrain"] == "Mixto"
    assert result["route_details"]["terrain_notes"] == "Sendero con pendientes"


@pytest.mark.asyncio
async def test_get_experience_detail_singular_plural() -> None:
    """The bug from the user: searching 'Fábrica de Cementos' must find 'Fábrica de Cemento'."""
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(name="Fabrica de Cemento")

    exp_patch, log_patch = _patch_experience_and_log(exp)
    with exp_patch, log_patch:
        result = await get_experience_detail(
            experience_query="Fabrica de Cementos",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "Fabrica de Cemento"


@pytest.mark.asyncio
async def test_get_experience_detail_with_accents() -> None:
    """Searches with accents must find experiences without accents in the DB."""
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(name="Fabrica de Cemento")

    exp_patch, log_patch = _patch_experience_and_log(exp)
    with exp_patch, log_patch:
        result = await get_experience_detail(
            experience_query="Fábrica de cemento",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "Fabrica de Cemento"


@pytest.mark.asyncio
async def test_get_experience_detail_not_found() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(name="Fabrica de Cemento")

    exp_patch, log_patch = _patch_experience_and_log(exp)
    with exp_patch, log_patch:
        result = await get_experience_detail(
            experience_query="experiencia inexistente xyz",
            trace_id="trace-1",
        )

    assert result["found"] is False
    assert result["blocking_reasons"][0]["code"] == "experience.not_found"


@pytest.mark.asyncio
async def test_get_experience_detail_finds_via_alias() -> None:
    """If name doesn't match but an alias does, return the experience."""
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(
        name="La Montana de Cristal",
        aliases=["Montana de Cristal", "Cristal"],
    )

    exp_patch, log_patch = _patch_experience_and_log(exp)
    with exp_patch, log_patch:
        result = await get_experience_detail(
            experience_query="Cristal",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "La Montana de Cristal"


@pytest.mark.asyncio
async def test_get_experience_detail_finds_via_tag() -> None:
    """If name and alias don't match but a tag does, return the experience."""
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(
        name="Recorrido de los Chorros",
        aliases=[],
        tags=["agua", "naturaleza", "rio"],
    )

    exp_patch, log_patch = _patch_experience_and_log(exp)
    with exp_patch, log_patch:
        result = await get_experience_detail(
            experience_query="naturaleza",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "Recorrido de los Chorros"


@pytest.mark.asyncio
async def test_get_experience_detail_handles_missing_pricing() -> None:
    """Experiences without pricing should not crash and should return null fields."""
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp()
    exp.pricing = None
    exp.inclusions = None
    exp.route_details = None
    exp.duration = None
    exp.duration_hours = None
    exp.duration_days = None

    exp_patch, log_patch = _patch_experience_and_log(exp)
    with exp_patch, log_patch:
        result = await get_experience_detail(
            experience_query="Fabrica de Cemento",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["pricing"] is None
    assert result["includes"] == []
    assert result["inclusions_display_text"] is None
    assert result["route_details"] is None
    assert result["starting_price"] is None
    assert result["duration"] is None
    assert result["duration_hours"] is None
    assert result["currency"] == "COP"
