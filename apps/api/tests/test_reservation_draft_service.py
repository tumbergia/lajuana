import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from beanie import PydanticObjectId

from app.ai.assistant.policy import ToolPolicyEngine
from app.common.enums import ReservationStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument, ReservationDocument
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs
from app.services.config_service import ConfigService
from app.services.reservation_draft_service import ReservationDraftService
from app.services.reservation_service import ReservationService


class FakeReservationDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def save(self) -> None:
        pass


class FakeFindQuery:
    def __init__(self, items: list) -> None:
        self._items = items

    async def to_list(self) -> list:
        return self._items


def _patch_base_deps(
    monkeypatch: pytest.MonkeyPatch,
    *,
    experience_is_active: bool = True,
    min_days_in_advance: int = 0,
) -> tuple[ReservationDraftService, PydanticObjectId]:
    service = ReservationDraftService()
    exp_id = PydanticObjectId()

    async def fake_experience_get(_):
        return SimpleNamespace(id=exp_id, is_active=experience_is_active)

    monkeypatch.setattr(ExperienceDocument, "get", fake_experience_get)

    async def fake_get_rules(self):
        return SimpleNamespace(
            min_days_in_advance=min_days_in_advance,
            reservation_draft_ttl_minutes=30,
        )

    monkeypatch.setattr(ConfigService, "get_reservation_rules", fake_get_rules)

    async def fake_ensure_date_available(self, requested_date):
        pass

    monkeypatch.setattr(ReservationService, "ensure_date_available", fake_ensure_date_available)

    async def fake_reservation_create(self, payload, **kwargs):
        return SimpleNamespace(id="fake-id")

    monkeypatch.setattr(ReservationService, "create", fake_reservation_create)

    async def fake_transition_status(self, reservation, target):
        reservation.status = target

    monkeypatch.setattr(ReservationService, "transition_status", fake_transition_status)

    return service, exp_id


# ---------------------------------------------------------------------------
# create_reservation_draft
# ---------------------------------------------------------------------------


async def _run_create_sets_status_pre_reserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id = _patch_base_deps(monkeypatch)

    result = await service.create_reservation_draft(
        experience_id=str(exp_id),
        schedule_id=str(PydanticObjectId()),
        participant_count=2,
        holder_phone="+573001234567",
        holder_name="Test User",
        requested_date="2026-07-15",
        quote_snapshot={"total": 100000},
    )

    assert result["created"] is True
    assert result["status"] == ReservationStatus.PRE_RESERVED.value
    assert "PR-" in result["code"]


def test_create_sets_status_pre_reserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_sets_status_pre_reserved(monkeypatch))


async def _run_create_experience_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ReservationDraftService()
    exp_id = PydanticObjectId()

    async def fake_get(_):
        return None

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    with pytest.raises(ApiError) as exc:
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(PydanticObjectId()),
            participant_count=2,
            holder_phone="+573001234567",
            holder_name="Test User",
            requested_date="2026-07-15",
            quote_snapshot={"total": 100000},
        )

    assert exc.value.code == ErrorCode.EXPERIENCE_NOT_FOUND


def test_create_experience_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_experience_not_found(monkeypatch))


async def _run_create_min_notice_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id = _patch_base_deps(monkeypatch, min_days_in_advance=10)

    with pytest.raises(ApiError) as exc:
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(PydanticObjectId()),
            participant_count=2,
            holder_phone="+573001234567",
            holder_name="Test User",
            requested_date=(datetime.now(UTC).date() + timedelta(days=3)).isoformat(),
            quote_snapshot={"total": 100000},
        )

    assert exc.value.code == ErrorCode.RESERVATION_MIN_NOTICE_VIOLATION


def test_create_min_notice_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_min_notice_violation(monkeypatch))


async def _run_create_rejects_more_than_8_participants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id = _patch_base_deps(monkeypatch)

    with pytest.raises(ApiError) as exc:
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(PydanticObjectId()),
            participant_count=9,
            holder_phone="+573001234567",
            holder_name="Test User",
            requested_date="2026-07-15",
            quote_snapshot={"total": 100000},
        )

    assert exc.value.code == ErrorCode.RESERVATION_INVALID_PARTICIPANT_COUNT


def test_create_rejects_more_than_8_participants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_rejects_more_than_8_participants(monkeypatch))


async def _run_create_guards_duplicate_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id = _patch_base_deps(monkeypatch)

    async def fake_ensure_date_available(self, requested_date):
        raise ApiError(
            status_code=409,
            code=ErrorCode.RESERVATION_NO_AVAILABILITY,
            message="La fecha ya tiene una reserva activa.",
        )

    monkeypatch.setattr(ReservationService, "ensure_date_available", fake_ensure_date_available)

    with pytest.raises(ApiError) as exc:
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(PydanticObjectId()),
            participant_count=2,
            holder_phone="+573001234567",
            holder_name="Test User",
            requested_date="2026-07-15",
            quote_snapshot={"total": 100000},
        )

    assert exc.value.code == ErrorCode.RESERVATION_NO_AVAILABILITY


def test_create_guards_duplicate_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_guards_duplicate_date(monkeypatch))


async def _run_create_guards_quote_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id = _patch_base_deps(monkeypatch)

    with pytest.raises(ApiError) as exc:
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(PydanticObjectId()),
            participant_count=2,
            holder_phone="+573001234567",
            holder_name="Test User",
            requested_date="2026-07-15",
            quote_snapshot={},
        )

    assert exc.value.code == ErrorCode.RESERVATION_QUOTE_SNAPSHOT_REQUIRED


def test_create_guards_quote_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_guards_quote_snapshot(monkeypatch))


async def _run_create_does_not_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id = _patch_base_deps(monkeypatch)

    captured_status: list[ReservationStatus | None] = []

    async def capturing_create(self, payload, **kwargs):
        captured_status.append(kwargs.get("initial_status"))
        return SimpleNamespace(id="fake-id")

    monkeypatch.setattr(ReservationService, "create", capturing_create)

    await service.create_reservation_draft(
        experience_id=str(exp_id),
        schedule_id=str(PydanticObjectId()),
        participant_count=2,
        holder_phone="+573001234567",
        holder_name="Test User",
        requested_date="2026-07-15",
        quote_snapshot={"total": 100000},
    )

    assert len(captured_status) == 1
    assert captured_status[0] == ReservationStatus.PRE_RESERVED
    assert captured_status[0] != ReservationStatus.CONFIRMED


def test_create_does_not_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_does_not_confirm(monkeypatch))


async def _run_create_schedule_id_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id = _patch_base_deps(monkeypatch)

    captured_payload: dict = {}

    async def capturing_create(self, payload, **kwargs):
        captured_payload.update(payload)
        return SimpleNamespace(id="fake-id")

    monkeypatch.setattr(ReservationService, "create", capturing_create)

    await service.create_reservation_draft(
        experience_id=str(exp_id),
        schedule_id=None,
        participant_count=2,
        holder_phone="+573001234567",
        holder_name="Test User",
        requested_date="2026-07-15",
        quote_snapshot={"total": 100000},
    )

    assert "schedule_id" not in captured_payload


def test_create_schedule_id_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_schedule_id_optional(monkeypatch))


# ---------------------------------------------------------------------------
# expire_reservation_drafts
# ---------------------------------------------------------------------------


async def _run_expire_changes_to_expired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ReservationDraftService()

    expiring_doc = FakeReservationDoc(
        code="PR-EXP",
        status=ReservationStatus.PRE_RESERVED,
        expire_at=datetime.now(UTC) - timedelta(minutes=5),
        participant_count=2,
        holder_phone="+573001234567",
    )

    def fake_find(*args, **kwargs):
        return FakeFindQuery([expiring_doc])

    monkeypatch.setattr(ReservationDocument, "find", fake_find)

    async def fake_transition(self, reservation, target):
        reservation.status = target

    monkeypatch.setattr(ReservationService, "transition_status", fake_transition)

    count = await service.expire_reservation_drafts()

    assert count == 1
    assert expiring_doc.status == ReservationStatus.EXPIRED


def test_expire_changes_to_expired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_expire_changes_to_expired(monkeypatch))


# ---------------------------------------------------------------------------
# ToolPolicyEngine — confirm_reservation blocked from WhatsApp
# ---------------------------------------------------------------------------


async def _run_policy_blocks_confirm_from_whatsapp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        tool_name="confirm_reservation",
        arguments=ToolArgs(),
        confidence=0.9,
        user_goal="confirm reservation",
        audit_summary="test",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert not decision.allowed
    assert decision.reason == "tool_not_allowed_for_channel"


def test_policy_blocks_confirm_from_whatsapp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_policy_blocks_confirm_from_whatsapp(monkeypatch))
