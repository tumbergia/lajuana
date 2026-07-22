"""Tests for get_experience_detail end-to-end with mocked catalog.

Validates:
- Returns all fields from the document (not just a subset)
- Fuzzy matching finds experiences by partial name / typos
- Singular/plural variants work
- Multi-experience queries return all matches
- Returns 'not found' for non-existent experiences
- Aliases and tags are searched as fallback
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_exp(
    *,
    exp_id: str = "exp-001",
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
        id=exp_id,
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


def _patch_catalog(experiences: list) -> tuple:
    """Patch catalog load + ToolCallLogDocument.insert."""
    from app.documents import tool_call_log_document

    mock_log_doc_class = MagicMock()
    mock_instance = MagicMock()
    mock_instance.insert = AsyncMock()
    mock_log_doc_class.return_value = mock_instance

    return (
        patch(
            "app.services.experience_catalog_resolver.ExperienceCatalogResolver._load_active",
            new=AsyncMock(return_value=experiences),
        ),
        patch(
            "app.ai.mcp.tools.experience_detail.ExperienceCatalogResolver._load_active",
            new=AsyncMock(return_value=experiences),
        ),
        patch.object(tool_call_log_document, "ToolCallLogDocument", mock_log_doc_class),
        patch(
            "app.ai.mcp.tools.experience_detail.ToolCallLogDocument",
            mock_log_doc_class,
        ),
    )


@pytest.mark.asyncio
async def test_get_experience_detail_returns_all_fields() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp()
    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
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
    assert result["response"] is None
    assert len(result["experiences"]) == 1

    assert result["pricing"] is not None
    assert result["pricing"]["currency"] == "COP"
    assert result["pricing"]["prices_are_net"] is True
    assert result["pricing"]["pricing_notes"] == "Incluye refrigerio"
    assert len(result["pricing"]["tiers"]) == 2
    assert result["pricing"]["tiers"][0]["min_participants"] == 1
    assert result["pricing"]["tiers"][0]["max_participants"] == 2
    assert result["pricing"]["tiers"][0]["price_per_person"] == 150000

    assert result["route_details"] is not None
    assert result["route_details"]["distance_km"] == 12.5
    assert result["route_details"]["terrain"] == "Mixto"
    assert result["route_details"]["terrain_notes"] == "Sendero con pendientes"


@pytest.mark.asyncio
async def test_get_experience_detail_singular_plural() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(name="Fabrica de Cemento")
    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
        result = await get_experience_detail(
            experience_query="Fabrica de Cementos",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "Fabrica de Cemento"


@pytest.mark.asyncio
async def test_get_experience_detail_with_accents() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(name="Fabrica de Cemento")
    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
        result = await get_experience_detail(
            experience_query="Fábrica de cemento",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "Fabrica de Cemento"


@pytest.mark.asyncio
async def test_get_experience_detail_typo_fabrca() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(name="Fábrica de Cementos", aliases=["Fabrica", "Cementos"])
    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
        result = await get_experience_detail(
            experience_query="dima acerca de fabrca",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert "Fabrica" in (result["name"] or "") or "Fábrica" in (result["name"] or "")


@pytest.mark.asyncio
async def test_get_experience_detail_multi_experiences() -> None:
    from app.ai.mcp.tools import get_experience_detail

    catalog = [
        _make_exp(
            exp_id="1",
            name="Cabalgata Básica",
            slug="cabalgata-basica",
            aliases=["cabalgata", "basica"],
            tags=["caballo"],
        ),
        _make_exp(
            exp_id="2",
            name="Los Chorros",
            slug="los-chorros",
            aliases=["chorros"],
            tags=["agua"],
        ),
        _make_exp(
            exp_id="3",
            name="Fábrica de Cementos",
            slug="fabrica-cementos",
            aliases=["fabrica", "cementos"],
            tags=["industrial"],
        ),
        _make_exp(
            exp_id="4",
            name="Recorrido de medio día",
            slug="medio-dia",
            aliases=["medio dia"],
            tags=["corto"],
        ),
    ]
    query = (
        "dima acerca de la cabalgata basica\n"
        "y sobre los chorros\n"
        "no y también de fabrca"
    )
    patches = _patch_catalog(catalog)
    with patches[0], patches[1], patches[2], patches[3]:
        result = await get_experience_detail(
            experience_query=query,
            trace_id="trace-multi",
        )

    assert result["found"] is True
    names = {e["name"] for e in result["experiences"]}
    assert "Cabalgata Básica" in names
    assert "Los Chorros" in names
    assert "Fábrica de Cementos" in names
    assert "Recorrido de medio día" not in names
    assert result["response"] is None
    # Structured payload for the composer (not a WhatsApp template).
    assert all(e.get("description") for e in result["experiences"])


@pytest.mark.asyncio
async def test_get_experience_detail_not_found() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(name="Fabrica de Cemento")
    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
        result = await get_experience_detail(
            experience_query="experiencia inexistente xyz",
            trace_id="trace-1",
        )

    assert result["found"] is False
    assert result["blocking_reasons"][0]["code"] == "experience.not_found"
    assert result["response"] is None


@pytest.mark.asyncio
async def test_get_experience_detail_finds_via_alias() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(
        name="La Montana de Cristal",
        aliases=["Montana de Cristal", "Cristal"],
    )
    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
        result = await get_experience_detail(
            experience_query="Cristal",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "La Montana de Cristal"


@pytest.mark.asyncio
async def test_get_experience_detail_finds_via_tag() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp(
        name="Recorrido de los Chorros",
        aliases=[],
        tags=["agua", "naturaleza", "rio"],
    )
    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
        result = await get_experience_detail(
            experience_query="naturaleza",
            trace_id="trace-1",
        )

    assert result["found"] is True
    assert result["name"] == "Recorrido de los Chorros"


@pytest.mark.asyncio
async def test_get_experience_detail_handles_missing_pricing() -> None:
    from app.ai.mcp.tools import get_experience_detail

    exp = _make_exp()
    exp.pricing = None
    exp.inclusions = None
    exp.route_details = None
    exp.duration = None
    exp.duration_hours = None
    exp.duration_days = None

    patches = _patch_catalog([exp])
    with patches[0], patches[1], patches[2], patches[3]:
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
