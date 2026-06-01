from __future__ import annotations

import time
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AvailableScheduleItem,
    ListAvailableSchedulesOutput,
    SuggestAlternativeDatesOutput,
    ToolBlockingReason,
)
from app.documents.experience_document import ExperienceDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionStatus,
)
from app.core.di import Container


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _field(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


async def _resolve_experience(
    experience_id: str | None,
    experience_query: str | None,
) -> ExperienceDocument | None:
    resolver = ExperienceCatalogResolver()

    if experience_id:
        result = await resolver.resolve(experience_id)
        if result.status == ExperienceResolutionStatus.FOUND:
            return await ExperienceDocument.get(result.experience_id)
        return None

    if not experience_query:
        return None

    result = await resolver.resolve(experience_query)
    if result.status == ExperienceResolutionStatus.FOUND:
        return await ExperienceDocument.get(result.experience_id)

    return None


def _generate_date_range(
    date_from: date,
    date_to: date,
    min_notice_days: int = 7,
) -> list[date]:
    today = datetime.now(UTC).date()
    min_date = today + timedelta(days=min_notice_days)
    start = max(date_from, min_date)
    dates: list[date] = []
    current = start
    while current <= date_to:
        dates.append(current)
        current += timedelta(days=1)
    return dates


async def list_available_schedules(
    experience_id: str | None = None,
    experience_query: str | None = None,
    requested_date: str | date | None = None,
    participant_count: int | None = None,
    limit: int = 10,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    if requested_date is None:
        date_from = datetime.now(UTC).date() + timedelta(days=7)
    elif isinstance(requested_date, date):
        date_from = requested_date
    else:
        date_from = date.fromisoformat(requested_date)

    date_to = date_from + timedelta(days=60)

    payload = dict(
        experience_id=experience_id,
        experience_query=experience_query,
        date_from=date_from,
        date_to=date_to,
        participant_count=participant_count,
        limit=limit,
    )

    output: ListAvailableSchedulesOutput | None = None
    error_code: str | None = None

    try:
        reasons: list[ToolBlockingReason] = []

        experience = await _resolve_experience(experience_id, experience_query)
        if experience is None:
            reasons.append(
                ToolBlockingReason(
                    code="experience.not_found",
                    message="No encontré una experiencia que coincida con la solicitud.",
                )
            )
            output = ListAvailableSchedulesOutput(
                trace_id=trace_id,
                date_from=date_from,
                date_to=date_to,
                participant_count=participant_count,
                schedules=[],
                total=0,
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        experience_id_obj = getattr(experience, "id", None)
        experience_name = _safe_str(_field(experience, "name", "title", "label"))

        candidate_dates = _generate_date_range(date_from, date_to, min_notice_days=7)

        reservation_service = Container.get_instance().reservation_service
        schedule_items: list[AvailableScheduleItem] = []
        for d in candidate_dates:
            if len(schedule_items) >= limit:
                break
            has_active = await reservation_service.has_active_reservation_for_date(d)
            if not has_active:
                schedule_items.append(
                    AvailableScheduleItem(
                        schedule_id="",
                        experience_id=_safe_str(experience_id_obj) or "",
                        experience_name=experience_name or "",
                        scheduled_date=d,
                        start_time=None,
                        capacity_total=8,
                        capacity_available=8,
                        status="open",
                    )
                )

        output = ListAvailableSchedulesOutput(
            trace_id=trace_id,
            date_from=date_from,
            date_to=date_to,
            participant_count=participant_count,
            schedules=schedule_items,
            total=len(schedule_items),
            blocking_reasons=reasons,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output_dict: dict[str, Any] = {
            "trace_id": trace_id,
            "tool_name": "list_available_schedules",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "participant_count": participant_count,
            "schedules": [],
            "total": 0,
            "blocking_reasons": [
                {
                    "code": error_code,
                    "message": str(exc),
                }
            ],
        }
        return output_dict

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="list_available_schedules",
            input=payload if "payload" in locals() else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def suggest_alternative_dates(
    experience_id: str | None = None,
    experience_query: str | None = None,
    requested_date: str | date | None = None,
    participant_count: int | None = None,
    search_days_before: int = 15,
    search_days_after: int = 30,
    exclude_dates: list[date] | None = None,
    limit: int = 5,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    today = datetime.now(UTC).date()

    if requested_date is None:
        requested_date = today + timedelta(days=60)
    elif isinstance(requested_date, date):
        requested_date = requested_date
    else:
        requested_date = date.fromisoformat(requested_date)

    date_from = requested_date - timedelta(days=search_days_before)
    if date_from < today:
        date_from = today

    date_to = requested_date + timedelta(days=search_days_after)

    exclude: list[date] = []
    if exclude_dates:
        for d in exclude_dates:
            if isinstance(d, date):
                exclude.append(d)
            elif isinstance(d, str):
                exclude.append(date.fromisoformat(d))

    payload = dict(
        experience_id=experience_id,
        experience_query=experience_query,
        requested_date=requested_date,
        date_from=date_from,
        date_to=date_to,
        participant_count=participant_count,
        search_days_before=search_days_before,
        search_days_after=search_days_after,
        limit=limit,
    )

    output: SuggestAlternativeDatesOutput | None = None
    error_code: str | None = None

    try:
        reasons: list[ToolBlockingReason] = []

        experience = await _resolve_experience(experience_id, experience_query)
        if experience is None:
            reasons.append(
                ToolBlockingReason(
                    code="experience.not_found",
                    message="No encontré una experiencia que coincida con la solicitud.",
                )
            )
            output = SuggestAlternativeDatesOutput(
                trace_id=trace_id,
                requested_date=requested_date,
                participant_count=participant_count or 1,
                alternatives=[],
                total=0,
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        experience_id_obj = getattr(experience, "id", None)
        experience_name = _safe_str(_field(experience, "name", "title", "label"))

        candidate_dates = _generate_date_range(date_from, date_to, min_notice_days=7)

        reservation_service = Container.get_instance().reservation_service
        schedule_items: list[AvailableScheduleItem] = []
        for d in candidate_dates:
            if len(schedule_items) >= limit:
                break
            if d in exclude:
                continue
            has_active = await reservation_service.has_active_reservation_for_date(d)
            if not has_active:
                schedule_items.append(
                    AvailableScheduleItem(
                        schedule_id="",
                        experience_id=_safe_str(experience_id_obj) or "",
                        experience_name=experience_name or "",
                        scheduled_date=d,
                        start_time=None,
                        capacity_total=8,
                        capacity_available=8,
                        status="open",
                    )
                )

        output = SuggestAlternativeDatesOutput(
            trace_id=trace_id,
            requested_date=requested_date,
            participant_count=participant_count or 1,
            alternatives=schedule_items,
            total=len(schedule_items),
            blocking_reasons=reasons,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output_dict: dict[str, Any] = {
            "trace_id": trace_id,
            "tool_name": "suggest_alternative_dates",
            "requested_date": requested_date.isoformat(),
            "participant_count": participant_count or 1,
            "alternatives": [],
            "total": 0,
            "blocking_reasons": [
                {
                    "code": error_code,
                    "message": str(exc),
                }
            ],
        }
        return output_dict

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="suggest_alternative_dates",
            input=payload if "payload" in locals() else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
