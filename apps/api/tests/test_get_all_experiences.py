"""Tests for get_all_experiences — tool that returns full details for all active experiences."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_exp(
    name: str = "Fabrica de Cemento",
    slug: str = "fabrica-de-cemento",
    is_active: bool = True,
    with_pricing: bool = True,
    with_inclusions: bool = True,
) -> SimpleNamespace:
    pricing = None
    if with_pricing:
        pricing = SimpleNamespace(
            currency="COP",
            prices_are_net=True,
            pricing_notes="Incluye refrigerio",
            tiers=[
                SimpleNamespace(min_participants=1, max_participants=2, price_per_person=150000),
                SimpleNamespace(min_participants=3, max_participants=8, price_per_person=120000),
            ],
        )
    inclusions = None
    if with_inclusions:
        inclusions = SimpleNamespace(
            items=["Guia", "Refrigerio"],
            display_text="Incluye guia y refrigerio",
        )
    return SimpleNamespace(
        id=f"id-{slug}",
        name=name,
        slug=slug,
        subtitle=f"Sub {name}",
        description=f"Description of {name}",
        image_url="https://example.com/img.jpg",
        level="INTERMEDIATE",
        difficulty="INTERMEDIATE",
        category="EXPERIENCE",
        status="PUBLISHED",
        is_active=is_active,
        duration=SimpleNamespace(activity_minutes=240, route_minutes=60, display_text="4 horas"),
        route_details=SimpleNamespace(
            distance_km=12.5,
            terrain="Mixto",
            terrain_notes="Pendientes",
        ),
        pricing=pricing,
        inclusions=inclusions,
        standard_max_participants=8,
        min_participants=1,
        base_capacity=8,
        duration_hours=4,
        duration_days=None,
        tags=["naturaleza"],
        aliases=["alias1"],
    )


def _patch_query(experiences: list, log_mock_class: MagicMock | None = None):
    """Patch ExperienceDocument.find(...).to_list() and ToolCallLogDocument."""
    from app.documents import tool_call_log_document

    query_mock = SimpleNamespace(to_list=AsyncMock(return_value=experiences))

    if log_mock_class is None:
        mock_log_doc_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.insert = AsyncMock()
        mock_log_doc_class.return_value = mock_instance
        log_mock_class = mock_log_doc_class

    return (
        patch("app.documents.ExperienceDocument.find", return_value=query_mock),
        patch.object(tool_call_log_document, "ToolCallLogDocument", log_mock_class),
    )


@pytest.mark.asyncio
async def test_get_all_experiences_returns_all_with_full_fields() -> None:
    from app.ai.mcp.tools import get_all_experiences

    exps = [
        _make_exp(name="Fabrica de Cemento", slug="fabrica"),
        _make_exp(name="La Montana de Cristal", slug="montana"),
        _make_exp(name="Los Chorros", slug="chorros"),
    ]

    exp_patch, log_patch = _patch_query(exps)
    with exp_patch, log_patch:
        result = await get_all_experiences(trace_id="trace-1")

    assert result["total"] == 3
    assert len(result["experiences"]) == 3
    assert result["blocking_reasons"] == []

    for exp_out in result["experiences"]:
        assert exp_out["found"] is True
        assert exp_out["name"]
        assert exp_out["slug"]
        assert exp_out["description"]
        assert exp_out["subtitle"]
        assert exp_out["image_url"]
        assert exp_out["level"] == "INTERMEDIATE"
        assert exp_out["difficulty"] == "INTERMEDIATE"
        assert exp_out["category"] == "EXPERIENCE"
        assert exp_out["is_active"] is True
        assert exp_out["duration"] == "4 horas"
        assert exp_out["duration_hours"] == 4
        assert exp_out["standard_max_participants"] == 8
        assert exp_out["min_participants"] == 1
        assert exp_out["includes"] == ["Guia", "Refrigerio"]
        assert exp_out["inclusions_display_text"] == "Incluye guia y refrigerio"
        assert exp_out["tags"] == ["naturaleza"]
        assert exp_out["aliases"] == ["alias1"]
        assert exp_out["pricing"] is not None
        assert exp_out["pricing"]["currency"] == "COP"
        assert len(exp_out["pricing"]["tiers"]) == 2
        assert exp_out["starting_price"] == 120000
        assert exp_out["route_details"] is not None
        assert exp_out["route_details"]["distance_km"] == 12.5


@pytest.mark.asyncio
async def test_get_all_experiences_filters_inactive_by_default() -> None:
    """Default is_active=True should add a Mongo filter to the query."""
    from app.ai.mcp.tools import get_all_experiences

    exps = [_make_exp(name="A"), _make_exp(name="B")]
    captured: dict = {}

    def _capture_query(query_dict: dict) -> SimpleNamespace:
        captured["query"] = query_dict
        return SimpleNamespace(to_list=AsyncMock(return_value=exps))

    with patch("app.documents.ExperienceDocument.find", side_effect=_capture_query) as find_patch, \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        await get_all_experiences(trace_id="t1")

    assert captured.get("query") == {"is_active": True}
    assert find_patch.called


@pytest.mark.asyncio
async def test_get_all_experiences_includes_inactive_when_requested() -> None:
    """is_active=None (or False) means include all, even inactive."""
    from app.ai.mcp.tools import get_all_experiences

    exps = [_make_exp(name="A", is_active=False)]
    captured: dict = {}

    def _capture_query(query_dict: dict) -> SimpleNamespace:
        captured["query"] = query_dict
        return SimpleNamespace(to_list=AsyncMock(return_value=exps))

    with patch("app.documents.ExperienceDocument.find", side_effect=_capture_query), \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        await get_all_experiences(trace_id="t1", is_active=False)

    assert captured.get("query") == {"is_active": False}


@pytest.mark.asyncio
async def test_get_all_experiences_empty_returns_blocking_reason() -> None:
    from app.ai.mcp.tools import get_all_experiences

    with patch("app.documents.ExperienceDocument.find", return_value=SimpleNamespace(to_list=AsyncMock(return_value=[]))), \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        result = await get_all_experiences(trace_id="t1")

    assert result["total"] == 0
    assert result["experiences"] == []
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "experience.none_available"


@pytest.mark.asyncio
async def test_get_all_experiences_respects_limit() -> None:
    from app.ai.mcp.tools import get_all_experiences

    exps = [_make_exp(name=f"Exp{i}", slug=f"exp{i}") for i in range(5)]
    returned: list = exps[:3]

    with patch("app.documents.ExperienceDocument.find", return_value=SimpleNamespace(to_list=AsyncMock(return_value=returned))), \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        result = await get_all_experiences(trace_id="t1", limit=3)

    assert result["total"] == 3
    assert len(result["experiences"]) == 3


@pytest.mark.asyncio
async def test_get_all_experiences_handles_missing_pricing_and_inclusions() -> None:
    """Experiences with no pricing/inclusions/route must not crash."""
    from app.ai.mcp.tools import get_all_experiences

    exp = _make_exp(with_pricing=False, with_inclusions=False)
    exp.pricing = None
    exp.inclusions = None
    exp.route_details = None
    exp.duration = None
    exp.duration_hours = None
    exp.duration_days = None

    with patch("app.documents.ExperienceDocument.find", return_value=SimpleNamespace(to_list=AsyncMock(return_value=[exp]))), \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        result = await get_all_experiences(trace_id="t1")

    assert result["total"] == 1
    out = result["experiences"][0]
    assert out["pricing"] is None
    assert out["starting_price"] is None
    assert out["includes"] == []
    assert out["inclusions_display_text"] is None
    assert out["route_details"] is None
    assert out["duration"] is None
    assert out["currency"] == "COP"


@pytest.mark.asyncio
async def test_get_all_experiences_response_includes_all_experiences() -> None:
    """Regresion: el LLM truncaba la lista a 4. La respuesta formateada debe
    incluir TODAS las experiencias devueltas por la DB."""
    from app.ai.mcp.tools import get_all_experiences

    exps = [
        _make_exp(name="Fabrica de Cemento", slug="fabrica"),
        _make_exp(name="La Montana de Cristal", slug="montana"),
        _make_exp(name="Los Chorros", slug="chorros"),
        _make_exp(name="Cabalgata Basica", slug="cabalgata"),
        _make_exp(name="Cabalgata Premium", slug="premium"),
        _make_exp(name="Tour del Cafe", slug="cafe"),
        _make_exp(name="Experiencia Solar", slug="solar"),
    ]

    with patch("app.documents.ExperienceDocument.find", return_value=SimpleNamespace(to_list=AsyncMock(return_value=exps))), \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        result = await get_all_experiences(trace_id="t1")

    assert result["total"] == 7
    assert "response" in result, "Falta la respuesta formateada para envio literal"

    formatted = result["response"]
    for exp in exps:
        assert exp.name in formatted, f"Falta {exp.name} en la respuesta formateada"
    assert "Tenemos 7 experiencias" in formatted
    # Cada experiencia debe tener su entrada numerada
    for i in range(1, 8):
        assert f"{i}. " in formatted, f"Falta la entrada numerada {i}"


@pytest.mark.asyncio
async def test_get_all_experiences_response_handles_empty() -> None:
    """Cuando no hay experiencias, la respuesta debe tener un mensaje amable."""
    from app.ai.mcp.tools import get_all_experiences

    with patch("app.documents.ExperienceDocument.find", return_value=SimpleNamespace(to_list=AsyncMock(return_value=[]))), \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        result = await get_all_experiences(trace_id="t1")

    assert result["total"] == 0
    assert "response" in result
    assert "no tenemos experiencias" in result["response"].lower() or "no hay" in result["response"].lower()


@pytest.mark.asyncio
async def test_get_all_experiences_response_includes_duration_and_price() -> None:
    """La respuesta formateada debe incluir duracion y precio cuando esten disponibles."""
    from app.ai.mcp.tools import get_all_experiences

    exp = _make_exp()

    with patch("app.documents.ExperienceDocument.find", return_value=SimpleNamespace(to_list=AsyncMock(return_value=[exp]))), \
         patch("app.documents.tool_call_log_document.ToolCallLogDocument") as mock_log:
        mock_log.return_value = MagicMock(insert=AsyncMock())
        result = await get_all_experiences(trace_id="t1")

    formatted = result["response"]
    assert "4 horas" in formatted
    assert "120,000" in formatted  # starting_price formateado con separador de miles
    assert "Guia" in formatted  # primer item de includes
