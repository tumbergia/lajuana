import asyncio

import pytest
from pymongo.errors import DuplicateKeyError

from app.common.enums import ExperienceLevel
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.schemas.experience import (
    ExperienceCreateSchema,
    ExperienceUpdateSchema,
)
from app.services.experience_service import ExperienceService


async def _run_create_maps_duplicate_slug_to_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeExperienceDocument:
        def __init__(self, **_: object) -> None:
            pass

        async def insert(self) -> None:
            raise DuplicateKeyError(
                "E11000 duplicate key error collection: lajuana.experiences index: slug_1 dup key",
                11000,
                {"keyPattern": {"slug": 1}, "keyValue": {"slug": "string"}},
            )

    monkeypatch.setattr(
        "app.services.experience_service.ExperienceDocument",
        FakeExperienceDocument,
    )

    service = ExperienceService()
    payload = ExperienceCreateSchema(
        name="Cabalgata",
        slug="string",
        description="Ruta corta",
        level=ExperienceLevel.BASIC,
        duration_hours=2,
    )

    with pytest.raises(ApiError) as exc_info:
        await service.create(payload)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == ErrorCode.EXPERIENCE_SLUG_ALREADY_EXISTS


async def _run_update_maps_duplicate_slug_to_conflict(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDoc:
        duration_hours = 2
        duration_days = None

        async def save(self) -> None:
            raise DuplicateKeyError(
                "E11000 duplicate key error collection: lajuana.experiences index: slug_1 dup key",
                11000,
                {"keyPattern": {"slug": 1}, "keyValue": {"slug": "string"}},
            )

    async def fake_get(_: str) -> FakeDoc:
        return FakeDoc()

    service = ExperienceService()
    monkeypatch.setattr(service, "get", fake_get)

    with pytest.raises(ApiError) as exc_info:
        await service.update(
            "660000000000000000000001",
            ExperienceUpdateSchema(name="Nuevo nombre"),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == ErrorCode.EXPERIENCE_SLUG_ALREADY_EXISTS


async def _run_purge_rejects_active_experience(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDoc:
        id = "660000000000000000000001"
        is_active = True

    async def fake_get(_: str) -> FakeDoc:
        return FakeDoc()

    service = ExperienceService()
    monkeypatch.setattr(service, "get", fake_get)

    with pytest.raises(ApiError) as exc_info:
        await service.purge("660000000000000000000001")

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == ErrorCode.EXPERIENCE_STILL_ACTIVE


async def _run_purge_rejects_when_has_reservations(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDoc:
        id = "660000000000000000000001"
        is_active = False

        async def delete(self) -> None:
            raise AssertionError("delete no debe ejecutarse")

    class FakeFind:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def count(self) -> int:
            return 2

    async def fake_get(_: str) -> FakeDoc:
        return FakeDoc()

    async def fake_record_change(**_: object) -> None:
        return None

    monkeypatch.setattr(
        "app.services.experience_service.ReservationDocument.find",
        FakeFind,
    )
    monkeypatch.setattr(
        "app.services.experience_service.record_change",
        fake_record_change,
    )

    service = ExperienceService()
    monkeypatch.setattr(service, "get", fake_get)

    with pytest.raises(ApiError) as exc_info:
        await service.purge("660000000000000000000001")

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == ErrorCode.EXPERIENCE_HAS_RESERVATIONS


def test_create_maps_duplicate_slug_to_conflict_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_create_maps_duplicate_slug_to_conflict(monkeypatch))


def test_update_maps_duplicate_slug_to_conflict_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_update_maps_duplicate_slug_to_conflict(monkeypatch))


def test_purge_rejects_active_experience(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_purge_rejects_active_experience(monkeypatch))


def test_purge_rejects_when_has_reservations(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_purge_rejects_when_has_reservations(monkeypatch))


def test_resolve_experience_reference_unique_name_match(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeExperience:
        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

    fake_docs = [
        FakeExperience(
            id="660000000000000000000204",
            name="Medio Dia",
            slug="medio-dia",
            aliases=["medio día"],
            is_active=True,
        ),
        FakeExperience(
            id="660000000000000000000205",
            name="Dia Completo",
            slug="dia-completo",
            aliases=[],
            is_active=True,
        ),
    ]

    async def fake_list(self: ExperienceService, **kwargs: object) -> list[FakeExperience]:
        return fake_docs

    monkeypatch.setattr(ExperienceService, "list", fake_list)
    service = ExperienceService()

    async def run() -> None:
        result = await service.resolve_experience_reference("medio dia")
        assert result["status"] == "resolved"
        assert result["experience_id"] == "660000000000000000000204"

    asyncio.run(run())


def test_resolve_experience_reference_ambiguous_prefix_match(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeExperience:
        def __init__(self, **kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)

    fake_docs = [
        FakeExperience(
            id="660000000000000000000204",
            name="Medio Dia Familiar",
            slug="medio-dia-familiar",
            aliases=[],
            is_active=True,
        ),
        FakeExperience(
            id="660000000000000000000205",
            name="Medio Dia Premium",
            slug="medio-dia-premium",
            aliases=[],
            is_active=True,
        ),
    ]

    async def fake_list(self: ExperienceService, **kwargs: object) -> list[FakeExperience]:
        return fake_docs

    monkeypatch.setattr(ExperienceService, "list", fake_list)
    service = ExperienceService()

    async def run() -> None:
        result = await service.resolve_experience_reference("medio dia")
        assert result["status"] == "ambiguous"
        assert len(result["matches"]) == 2

    asyncio.run(run())
