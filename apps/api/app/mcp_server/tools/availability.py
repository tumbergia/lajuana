from __future__ import annotations

import time
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId

from app.core.config import settings
from app.documents.experience_document import ExperienceDocument
from app.documents.schedule_document import ScheduleDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.mcp_server.tool_contracts import (
    CheckExperienceAvailabilityInput,
    CheckExperienceAvailabilityOutput,
    ToolBlockingReason,
)


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _safe_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _field(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def _status_text(obj: Any) -> str:
    value = _field(obj, "status", default="")
    raw = getattr(value, "value", value)
    return str(raw).lower()


async def _find_experience(
    experience_id: str | None,
    experience_query: str | None,
) -> ExperienceDocument | None:
    if experience_id:
        try:
            return await ExperienceDocument.get(PydanticObjectId(experience_id))
        except Exception:
            return None

    if not experience_query:
        return None

    query = experience_query.strip().lower()
    if not query:
        return None

    experiences = await ExperienceDocument.find_all().to_list()
    for experience in experiences:
        name = str(_field(experience, "name", "title", "label", default="")).lower()
        description = str(_field(experience, "description", "summary", default="")).lower()
        haystack = f"{name} {description}"
        if query in haystack or any(
            token in haystack for token in query.split() if len(token) >= 4
        ):
            return experience

    return None


async def _find_schedule(
    experience: ExperienceDocument,
    requested_date: date,
) -> ScheduleDocument | None:
    experience_id = getattr(experience, "id", None)
    if experience_id is None:
        return None

    try:
        return await ScheduleDocument.find_one(
            ScheduleDocument.experience_id == experience_id,
            ScheduleDocument.date == requested_date,
        )
    except Exception:
        schedules = await ScheduleDocument.find_all().to_list()
        for schedule in schedules:
            same_experience = _safe_str(_field(schedule, "experience_id")) == _safe_str(
                experience_id
            )
            same_date = (
                _field(schedule, "date", "scheduled_date", "requested_date") == requested_date
            )
            if same_experience and same_date:
                return schedule
        return None


def _is_schedule_available(
    schedule: ScheduleDocument, participant_count: int
) -> tuple[bool, list[ToolBlockingReason]]:
    reasons: list[ToolBlockingReason] = []

    status = _status_text(schedule)
    if status in {"closed", "cerrada", "full", "complete", "completa", "cancelled", "cancelada"}:
        reasons.append(
            ToolBlockingReason(
                code="schedule.not_open",
                message="La fecha operativa no está abierta para reservas.",
            )
        )

    capacity_available = _safe_int(
        _field(
            schedule,
            "capacity_available",
            "available_capacity",
            "available_slots",
            "available_spots",
            "cupos_disponibles",
        ),
        default=0,
    )

    if capacity_available is None or capacity_available < participant_count:
        reasons.append(
            ToolBlockingReason(
                code="schedule.no_availability",
                message="No hay cupos suficientes para esa fecha.",
            )
        )

    return len(reasons) == 0, reasons


def _violates_min_notice(requested_date: date, min_notice_days: int) -> bool:
    today = datetime.now(UTC).date()
    delta_days = (requested_date - today).days
    return delta_days < min_notice_days


async def check_experience_availability(
    experience_id: str | None = None,
    experience_query: str | None = None,
    requested_date: str | date | None = None,
    participant_count: int = 1,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    if requested_date is None:
        requested_date_obj = datetime.now(UTC).date()
    elif isinstance(requested_date, date):
        requested_date_obj = requested_date
    else:
        requested_date_obj = date.fromisoformat(requested_date)

    payload = CheckExperienceAvailabilityInput(
        experience_id=experience_id,
        experience_query=experience_query,
        requested_date=requested_date_obj,
        participant_count=participant_count,
    )

    output: CheckExperienceAvailabilityOutput | None = None
    error_code: str | None = None

    try:
        min_notice_days = settings.assistant_default_min_notice_days
        reasons: list[ToolBlockingReason] = []

        experience = await _find_experience(payload.experience_id, payload.experience_query)
        if experience is None:
            reasons.append(
                ToolBlockingReason(
                    code="experience.not_found",
                    message="No encontré una experiencia que coincida con la solicitud.",
                )
            )
            output = CheckExperienceAvailabilityOutput(
                available=False,
                trace_id=trace_id,
                experience_id=None,
                experience_name=None,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                min_notice_days=min_notice_days,
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        if _violates_min_notice(payload.requested_date, min_notice_days):
            reasons.append(
                ToolBlockingReason(
                    code="reservation.min_notice_violation",
                    message=f"La reserva requiere mínimo {min_notice_days} días de anticipación.",
                )
            )

        schedule = await _find_schedule(experience, payload.requested_date)
        if schedule is None:
            reasons.append(
                ToolBlockingReason(
                    code="schedule.not_found",
                    message=(
                        "No hay una fecha operativa programada para esa"
                        " experiencia en la fecha solicitada."
                    ),
                )
            )

            output = CheckExperienceAvailabilityOutput(
                available=False,
                trace_id=trace_id,
                experience_id=_safe_str(getattr(experience, "id", None)),
                experience_name=_safe_str(_field(experience, "name", "title", "label")),
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                min_notice_days=min_notice_days,
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        schedule_available, schedule_reasons = _is_schedule_available(
            schedule, payload.participant_count
        )
        reasons.extend(schedule_reasons)

        capacity_total = _safe_int(
            _field(schedule, "capacity_total", "total_capacity", "capacity", "capacidad_total")
        )
        capacity_available = _safe_int(
            _field(
                schedule,
                "capacity_available",
                "available_capacity",
                "available_slots",
                "available_spots",
                "cupos_disponibles",
            )
        )

        output = CheckExperienceAvailabilityOutput(
            available=schedule_available and len(reasons) == 0,
            trace_id=trace_id,
            experience_id=_safe_str(getattr(experience, "id", None)),
            experience_name=_safe_str(_field(experience, "name", "title", "label")),
            schedule_id=_safe_str(getattr(schedule, "id", None)),
            requested_date=payload.requested_date,
            participant_count=payload.participant_count,
            capacity_total=capacity_total,
            capacity_available=capacity_available,
            min_notice_days=min_notice_days,
            blocking_reasons=reasons,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output_dict = {
            "available": False,
            "trace_id": trace_id,
            "tool_name": "check_experience_availability",
            "requested_date": requested_date_obj.isoformat(),
            "participant_count": participant_count,
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
            tool_name="check_experience_availability",
            input=payload.model_dump(mode="json") if "payload" in locals() else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
