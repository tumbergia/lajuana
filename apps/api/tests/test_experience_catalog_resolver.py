import asyncio

from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionResult,
    ExperienceResolutionStatus,
)


def test_resolver_imports() -> None:
    resolver = ExperienceCatalogResolver()
    assert resolver is not None


def test_resolution_result_model() -> None:
    result = ExperienceResolutionResult(
        status=ExperienceResolutionStatus.FOUND,
        experience_id="507f1f77bcf86cd799439011",
        experience_name="Los Chorros",
        slug="los-chorros",
        confidence=1.0,
    )
    assert result.status == ExperienceResolutionStatus.FOUND
    assert result.experience_id == "507f1f77bcf86cd799439011"
    assert result.experience_name == "Los Chorros"
    assert result.slug == "los-chorros"
    assert result.confidence == 1.0
    assert result.candidates == []


def test_resolution_result_ambiguous() -> None:
    result = ExperienceResolutionResult(
        status=ExperienceResolutionStatus.AMBIGUOUS,
        candidates=[
            {"experience_id": "aaa", "name": "A"},
            {"experience_id": "bbb", "name": "B"},
        ],
    )
    assert result.status == ExperienceResolutionStatus.AMBIGUOUS
    assert len(result.candidates) == 2


def test_resolution_result_not_found() -> None:
    result = ExperienceResolutionResult(
        status=ExperienceResolutionStatus.NOT_FOUND,
    )
    assert result.status == ExperienceResolutionStatus.NOT_FOUND
    assert result.experience_id is None


def test_resolve_empty_query() -> None:
    resolver = ExperienceCatalogResolver()

    result = asyncio.run(resolver.resolve(""))
    assert result.status == ExperienceResolutionStatus.NOT_FOUND

    result = asyncio.run(resolver.resolve("   "))
    assert result.status == ExperienceResolutionStatus.NOT_FOUND


def test_resolve_none_query() -> None:
    resolver = ExperienceCatalogResolver()

    result = asyncio.run(resolver.resolve(None))  # type: ignore[arg-type]
    assert result.status == ExperienceResolutionStatus.NOT_FOUND
