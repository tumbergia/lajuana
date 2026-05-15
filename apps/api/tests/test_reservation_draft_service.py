import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from beanie import PydanticObjectId

from app.ai.assistant.policy import ToolPolicyEngine
from app.common.enums import ReservationStatus, ScheduleStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument, ReservationDocument
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs
from app.services.config_service import ConfigService
from app.services.reservation_draft_service import ReservationDraftService
from app.services.reservation_service import ReservationService
from app.services.schedule_service import ScheduleService


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
    available_slots: int = 10,
    experience_is_active: bool = True,
    schedule_is_active: bool = True,
    schedule_status: ScheduleStatus = ScheduleStatus.OPEN,
    min_days_in_advance: int = 0,
) -> tuple[ReservationDraftService, PydanticObjectId, PydanticObjectId]:
    service = ReservationDraftService()
    exp_id = PydanticObjectId()
    sched_id = PydanticObjectId()

    async def fake_experience_get(_):
        return SimpleNamespace(id=exp_id, is_active=experience_is_active)

    monkeypatch.setattr(ExperienceDocument, "get", fake_experience_get)

    async def fake_schedule_get(self, _):
        return SimpleNamespace(
            is_active=schedule_is_active,
            status=schedule_status,
            available_slots=available_slots,
        )

    monkeypatch.setattr(ScheduleService, "get", fake_schedule_get)

    async def fake_hold_slots(self, _sid, _count):
        return {"held": _count}

    monkeypatch.setattr(ScheduleService, "hold_slots", fake_hold_slots)

    async def fake_release_held_slots(self, _sid, _count):
        return {"released": _count}

    monkeypatch.setattr(ScheduleService, "release_held_slots", fake_release_held_slots)

    async def fake_get_rules(self):
        return SimpleNamespace(
            min_days_in_advance=min_days_in_advance,
            reservation_draft_ttl_minutes=30,
        )

    monkeypatch.setattr(ConfigService, "get_reservation_rules", fake_get_rules)

    async def fake_reservation_create(self, payload, **kwargs):
        return SimpleNamespace(id="fake-id")

    monkeypatch.setattr(ReservationService, "create", fake_reservation_create)

    async def fake_transition_status(self, reservation, target):
        reservation.status = target

    monkeypatch.setattr(ReservationService, "transition_status", fake_transition_status)

    return service, exp_id, sched_id


# ---------------------------------------------------------------------------
# create_reservation_draft
# ---------------------------------------------------------------------------


async def _run_create_sets_status_pre_reserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id, sched_id = _patch_base_deps(monkeypatch)

    result = await service.create_reservation_draft(
        experience_id=str(exp_id),
        schedule_id=str(sched_id),
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


async def _run_create_guards_quote_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id, sched_id = _patch_base_deps(monkeypatch)

    with pytest.raises(ApiError) as exc:
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(sched_id),
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


async def _run_create_increments_held_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id, sched_id = _patch_base_deps(monkeypatch)

    held_calls: list[int] = []

    async def tracking_hold(self, _sid, count):
        held_calls.append(count)
        return {"held": count}

    monkeypatch.setattr(ScheduleService, "hold_slots", tracking_hold)

    await service.create_reservation_draft(
        experience_id=str(exp_id),
        schedule_id=str(sched_id),
        participant_count=3,
        holder_phone="+573001234567",
        holder_name="Test User",
        requested_date="2026-07-15",
        quote_snapshot={"total": 100000},
    )

    assert len(held_calls) == 1
    assert held_calls[0] == 3


def test_create_increments_held_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_increments_held_slots(monkeypatch))


async def _run_create_does_not_modify_reserved_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id, sched_id = _patch_base_deps(monkeypatch)

    hold_calls: list[int] = []
    convert_calls: list[Any] = []

    async def tracking_hold(self, _sid, count):
        hold_calls.append(count)
        return {"held": count}

    async def tracking_convert(self, *args):
        convert_calls.append(args)

    monkeypatch.setattr(ScheduleService, "hold_slots", tracking_hold)
    monkeypatch.setattr(ScheduleService, "convert_hold_to_reserved", tracking_convert)

    await service.create_reservation_draft(
        experience_id=str(exp_id),
        schedule_id=str(sched_id),
        participant_count=2,
        holder_phone="+573001234567",
        holder_name="Test User",
        requested_date="2026-07-15",
        quote_snapshot={"total": 100000},
    )

    assert len(hold_calls) == 1
    assert len(convert_calls) == 0


def test_create_does_not_modify_reserved_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_does_not_modify_reserved_slots(monkeypatch))


async def _run_create_does_not_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id, sched_id = _patch_base_deps(monkeypatch)

    captured_status: list[ReservationStatus | None] = []

    async def capturing_create(self, payload, **kwargs):
        captured_status.append(kwargs.get("initial_status"))
        return SimpleNamespace(id="fake-id")

    monkeypatch.setattr(ReservationService, "create", capturing_create)

    await service.create_reservation_draft(
        experience_id=str(exp_id),
        schedule_id=str(sched_id),
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


async def _run_create_rolls_back_hold_when_create_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, exp_id, sched_id = _patch_base_deps(monkeypatch)

    release_calls: list[tuple[str, int]] = []

    async def failing_create(self, payload, **kwargs):
        raise RuntimeError("db insert failed")

    async def tracking_release(self, sid, count):
        release_calls.append((sid, count))
        return {"released": count}

    monkeypatch.setattr(ReservationService, "create", failing_create)
    monkeypatch.setattr(ScheduleService, "release_held_slots", tracking_release)

    with pytest.raises(RuntimeError):
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(sched_id),
            participant_count=4,
            holder_phone="+573001234567",
            holder_name="Test User",
            requested_date="2026-07-15",
            quote_snapshot={"total": 100000},
        )

    assert release_calls == [(str(sched_id), 4)]


def test_create_rolls_back_hold_when_create_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_rolls_back_hold_when_create_fails(monkeypatch))


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
        schedule_id=PydanticObjectId(),
        participant_count=2,
        holder_phone="+573001234567",
    )

    def fake_find(*args, **kwargs):
        return FakeFindQuery([expiring_doc])

    monkeypatch.setattr(ReservationDocument, "find", fake_find)

    async def fake_transition(self, reservation, target):
        reservation.status = target

    monkeypatch.setattr(ReservationService, "transition_status", fake_transition)

    async def fake_release(self, _sid, _count):
        return {"released": _count}

    monkeypatch.setattr(ScheduleService, "release_held_slots", fake_release)

    count = await service.expire_reservation_drafts()

    assert count == 1
    assert expiring_doc.status == ReservationStatus.EXPIRED


def test_expire_changes_to_expired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_expire_changes_to_expired(monkeypatch))


async def _run_expire_releases_held_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ReservationDraftService()

    expiring_doc = FakeReservationDoc(
        code="PR-EXP",
        status=ReservationStatus.PRE_RESERVED,
        expire_at=datetime.now(UTC) - timedelta(minutes=5),
        schedule_id=PydanticObjectId(),
        participant_count=2,
        holder_phone="+573001234567",
    )

    release_calls: list[int] = []

    def fake_find(*args, **kwargs):
        return FakeFindQuery([expiring_doc])

    monkeypatch.setattr(ReservationDocument, "find", fake_find)

    async def fake_transition(self, reservation, target):
        reservation.status = target

    monkeypatch.setattr(ReservationService, "transition_status", fake_transition)

    async def fake_release(self, _sid, count):
        release_calls.append(count)
        return {"released": count}

    monkeypatch.setattr(ScheduleService, "release_held_slots", fake_release)

    count = await service.expire_reservation_drafts()

    assert count == 1
    assert len(release_calls) == 1
    assert release_calls[0] == 2


def test_expire_releases_held_slots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_expire_releases_held_slots(monkeypatch))


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
    assert decision.reason == "critical_tool_denied"


def test_policy_blocks_confirm_from_whatsapp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_policy_blocks_confirm_from_whatsapp(monkeypatch))


# ---------------------------------------------------------------------------
# Concurrent holds — no oversell
# ---------------------------------------------------------------------------


async def _run_concurrent_holds_no_oversell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # available_slots passes the pre-check, but atomic hold fails (race)
    service, exp_id, sched_id = _patch_base_deps(monkeypatch, available_slots=10)

    async def failing_hold(self, _sid, _count):
        return None

    monkeypatch.setattr(ScheduleService, "hold_slots", failing_hold)

    with pytest.raises(ApiError) as exc:
        await service.create_reservation_draft(
            experience_id=str(exp_id),
            schedule_id=str(sched_id),
            participant_count=5,
            holder_phone="+573001234567",
            holder_name="Test User",
            requested_date="2026-07-15",
            quote_snapshot={"total": 100000},
        )

    assert exc.value.code == ErrorCode.SCHEDULE_HOLD_FAILED


def test_concurrent_holds_no_oversell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_concurrent_holds_no_oversell(monkeypatch))
