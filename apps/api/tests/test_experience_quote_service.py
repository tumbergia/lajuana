import asyncio

import pytest
from beanie import PydanticObjectId

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents.experience_document import ExperienceDocument as RealExperienceDoc
from app.schemas.experience import (
    ExperiencePricingSchema,
    ExperiencePricingTierSchema,
    ExperienceQuoteRequestSchema,
)
from app.services.experience_service import ExperienceService


def _fake_doc(**kwargs):
    from types import SimpleNamespace

    return SimpleNamespace(**kwargs)


def _mock_experience_get(monkeypatch, fake_doc):
    async def _get(_):
        return fake_doc

    monkeypatch.setattr(RealExperienceDoc, "get", _get)


async def _run_quote_returns_correct_tier_and_subtotal(monkeypatch):
    doc_id = PydanticObjectId()
    fake = _fake_doc(
        id=doc_id,
        is_active=True,
        pricing=ExperiencePricingSchema(
            currency="COP",
            tiers=[
                ExperiencePricingTierSchema(
                    min_participants=1, max_participants=6, price_per_person=150000
                ),
                ExperiencePricingTierSchema(
                    min_participants=7, max_participants=12, price_per_person=120000
                ),
            ],
        ),
    )
    _mock_experience_get(monkeypatch, fake)

    service = ExperienceService()
    result = await service.quote(str(doc_id), ExperienceQuoteRequestSchema(participant_count=4))

    assert result.participant_count == 4
    assert result.unit_price == 150000
    assert result.subtotal == 600000
    assert result.currency == "COP"
    assert result.pricing_tier.min_participants == 1
    assert result.pricing_tier.max_participants == 6
    assert result.pricing_tier.price_per_person == 150000
    assert result.notes is None


async def _run_quote_uses_first_matching_tier(monkeypatch):
    doc_id = PydanticObjectId()
    fake = _fake_doc(
        id=doc_id,
        is_active=True,
        pricing=ExperiencePricingSchema(
            currency="COP",
            tiers=[
                ExperiencePricingTierSchema(
                    min_participants=1, max_participants=3, price_per_person=100000
                ),
                ExperiencePricingTierSchema(
                    min_participants=4, max_participants=7, price_per_person=80000
                ),
                ExperiencePricingTierSchema(
                    min_participants=8, max_participants=12, price_per_person=60000
                ),
            ],
        ),
    )
    _mock_experience_get(monkeypatch, fake)

    service = ExperienceService()
    result = await service.quote(str(doc_id), ExperienceQuoteRequestSchema(participant_count=4))

    assert result.unit_price == 80000
    assert result.subtotal == 320000
    assert result.pricing_tier.min_participants == 4
    assert result.pricing_tier.max_participants == 7


async def _run_quote_raises_validation_error_for_invalid_id(
    monkeypatch,
) -> None:
    service = ExperienceService()
    payload = ExperienceQuoteRequestSchema(participant_count=2)

    with pytest.raises(ApiError) as exc_info:
        await service.quote("not-a-valid-id", payload)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


async def _run_quote_raises_not_found_for_missing_doc(monkeypatch) -> None:
    async def _get(_):
        return None

    monkeypatch.setattr(RealExperienceDoc, "get", _get)

    service = ExperienceService()
    payload = ExperienceQuoteRequestSchema(participant_count=2)

    with pytest.raises(ApiError) as exc_info:
        await service.quote("660000000000000000000001", payload)

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == ErrorCode.EXPERIENCE_NOT_FOUND


async def _run_quote_raises_inactive(monkeypatch) -> None:
    doc_id = PydanticObjectId()
    fake = _fake_doc(id=doc_id, is_active=False, pricing=None)
    _mock_experience_get(monkeypatch, fake)

    service = ExperienceService()
    payload = ExperienceQuoteRequestSchema(participant_count=2)

    with pytest.raises(ApiError) as exc_info:
        await service.quote(str(doc_id), payload)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == ErrorCode.EXPERIENCE_INACTIVE


async def _run_quote_raises_pricing_missing(monkeypatch) -> None:
    doc_id = PydanticObjectId()
    fake = _fake_doc(id=doc_id, is_active=True, pricing=None)
    _mock_experience_get(monkeypatch, fake)

    service = ExperienceService()
    payload = ExperienceQuoteRequestSchema(participant_count=2)

    with pytest.raises(ApiError) as exc_info:
        await service.quote(str(doc_id), payload)

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == ErrorCode.EXPERIENCE_PRICING_MISSING


async def _run_quote_raises_pricing_missing_when_tiers_empty(
    monkeypatch,
) -> None:
    doc_id = PydanticObjectId()
    fake = _fake_doc(
        id=doc_id,
        is_active=True,
        pricing=ExperiencePricingSchema(currency="COP", tiers=[]),
    )
    _mock_experience_get(monkeypatch, fake)

    service = ExperienceService()
    payload = ExperienceQuoteRequestSchema(participant_count=2)

    with pytest.raises(ApiError) as exc_info:
        await service.quote(str(doc_id), payload)

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == ErrorCode.EXPERIENCE_PRICING_MISSING


async def _run_quote_raises_tier_not_found(monkeypatch) -> None:
    doc_id = PydanticObjectId()
    fake = _fake_doc(
        id=doc_id,
        is_active=True,
        pricing=ExperiencePricingSchema(
            currency="COP",
            tiers=[
                ExperiencePricingTierSchema(
                    min_participants=1, max_participants=6, price_per_person=150000
                ),
            ],
        ),
    )
    _mock_experience_get(monkeypatch, fake)

    service = ExperienceService()
    payload = ExperienceQuoteRequestSchema(participant_count=10)

    with pytest.raises(ApiError) as exc_info:
        await service.quote(str(doc_id), payload)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == ErrorCode.EXPERIENCE_PRICING_TIER_NOT_FOUND


# ── Sync test wrappers ────────────────────────────────────────────────


def test_quote_returns_correct_tier_and_subtotal(monkeypatch) -> None:
    asyncio.run(_run_quote_returns_correct_tier_and_subtotal(monkeypatch))


def test_quote_uses_first_matching_tier(monkeypatch) -> None:
    asyncio.run(_run_quote_uses_first_matching_tier(monkeypatch))


def test_quote_raises_validation_error_for_invalid_id(monkeypatch) -> None:
    asyncio.run(_run_quote_raises_validation_error_for_invalid_id(monkeypatch))


def test_quote_raises_not_found_for_missing_doc(monkeypatch) -> None:
    asyncio.run(_run_quote_raises_not_found_for_missing_doc(monkeypatch))


def test_quote_raises_inactive(monkeypatch) -> None:
    asyncio.run(_run_quote_raises_inactive(monkeypatch))


def test_quote_raises_pricing_missing(monkeypatch) -> None:
    asyncio.run(_run_quote_raises_pricing_missing(monkeypatch))


def test_quote_raises_pricing_missing_when_tiers_empty(monkeypatch) -> None:
    asyncio.run(_run_quote_raises_pricing_missing_when_tiers_empty(monkeypatch))


def test_quote_raises_tier_not_found(monkeypatch) -> None:
    asyncio.run(_run_quote_raises_tier_not_found(monkeypatch))
