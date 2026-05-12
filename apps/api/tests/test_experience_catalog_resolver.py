from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionStatus,
)


def _fake_exp(**overrides: Any) -> SimpleNamespace:
    data = {
        "id": "507f1f77bcf86cd799439011",
        "name": "Los Chorros",
        "slug": "los-chorros",
        "description": "Ruta de un d\u00eda por senderos y cascadas.",
        "aliases": ["chorros", "los chorros", "recorrido los chorros"],
        "tags": ["cafe", "naturaleza"],
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def _experiences() -> list[SimpleNamespace]:
    return [
        _fake_exp(
            id="507f1f77bcf86cd799439011",
            name="Los Chorros",
            slug="los-chorros",
            description="Ruta de un d\u00eda por senderos y cascadas.",
            aliases=["chorros", "los chorros", "recorrido los chorros"],
            tags=["cafe", "naturaleza"],
        ),
        _fake_exp(
            id="507f1f77bcf86cd799439012",
            name="Recorrido de medio d\u00eda",
            slug="recorrido-medio-dia",
            description="Experiencia corta ideal para quienes tienen poco tiempo.",
            aliases=[
                "medio d\u00eda",
                "medio dia",
                "recorrido de medio d\u00eda",
                "plan corto",
                "cafe",
                "caf\u00e9",
            ],
            tags=["cafe", "senderismo"],
        ),
        _fake_exp(
            id="507f1f77bcf86cd799439013",
            name="La Monta\u00f1a de Cristal",
            slug="montana-cristal",
            description="Ruta t\u00e9cnica de ascenso de un d\u00eda.",
            aliases=["monta\u00f1a cristal", "cristal"],
            tags=["aventura"],
        ),
    ]


def test_resolves_exact_slug() -> None:
    result = _run(ExperienceCatalogResolver().resolve("los-chorros", experiences=_experiences()))
    assert result.status == ExperienceResolutionStatus.FOUND
    assert result.slug == "los-chorros"
    assert result.confidence == 1.0


def test_resolves_alias() -> None:
    result = _run(ExperienceCatalogResolver().resolve("chorros", experiences=_experiences()))
    assert result.status == ExperienceResolutionStatus.FOUND
    assert result.slug == "los-chorros"


def test_resolves_alias_with_spaces() -> None:
    result = _run(
        ExperienceCatalogResolver().resolve("recorrido los chorros", experiences=_experiences())
    )
    assert result.status == ExperienceResolutionStatus.FOUND
    assert result.slug == "los-chorros"


def test_resolves_without_accents() -> None:
    result = _run(ExperienceCatalogResolver().resolve("medio dia", experiences=_experiences()))
    assert result.status == ExperienceResolutionStatus.FOUND
    assert result.slug == "recorrido-medio-dia"


def test_resolves_without_accents_cafe() -> None:
    result = _run(ExperienceCatalogResolver().resolve("cafe", experiences=_experiences()))
    assert result.status == ExperienceResolutionStatus.FOUND


def test_resolves_case_insensitive() -> None:
    result = _run(ExperienceCatalogResolver().resolve("LOS CHORROS", experiences=_experiences()))
    assert result.status == ExperienceResolutionStatus.FOUND
    assert result.slug == "los-chorros"


def test_resolves_partial_token_match() -> None:
    result = _run(ExperienceCatalogResolver().resolve("plan corto", experiences=_experiences()))
    assert result.status == ExperienceResolutionStatus.FOUND
    assert result.slug == "recorrido-medio-dia"


def test_returns_ambiguous_when_multiple_candidates() -> None:
    result = _run(ExperienceCatalogResolver().resolve("ruta", experiences=_experiences()))
    assert result.status == ExperienceResolutionStatus.AMBIGUOUS
    assert len(result.candidates) >= 2


def test_returns_not_found_when_no_match() -> None:
    result = _run(
        ExperienceCatalogResolver().resolve("xyzzy no existe", experiences=_experiences())
    )
    assert result.status == ExperienceResolutionStatus.NOT_FOUND


def test_resolve_empty_query() -> None:
    result = _run(ExperienceCatalogResolver().resolve("", experiences=[]))
    assert result.status == ExperienceResolutionStatus.NOT_FOUND
    result = _run(ExperienceCatalogResolver().resolve("   ", experiences=[]))
    assert result.status == ExperienceResolutionStatus.NOT_FOUND


def test_resolve_none_query() -> None:
    result = _run(ExperienceCatalogResolver().resolve(None, experiences=[]))  # type: ignore[arg-type]
    assert result.status == ExperienceResolutionStatus.NOT_FOUND
