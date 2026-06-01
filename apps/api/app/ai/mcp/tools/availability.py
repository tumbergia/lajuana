from __future__ import annotations

import time
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    CheckExperienceAvailabilityInput,
    CheckExperienceAvailabilityOutput,
    ToolBlockingReason,
)
from app.core.config import settings
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


def _status_text(obj: Any) -> str:
    value = _field(obj, "status", default="")
    raw = getattr(value, "value", value)
    return str(raw).lower()


async def _find_experience(
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
    **kwargs: Any,
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

        reservation_service = Container.get_instance().reservation_service
        has_active = await reservation_service.has_active_reservation_for_date(
            payload.requested_date
        )
        if has_active:
            reasons.append(
                ToolBlockingReason(
                    code="reservation.date_already_booked",
                    message="Ya existe una reserva activa para esa fecha.",
                )
            )

        output = CheckExperienceAvailabilityOutput(
            available=len(reasons) == 0,
            trace_id=trace_id,
            experience_id=_safe_str(getattr(experience, "id", None)),
            experience_name=_safe_str(_field(experience, "name", "title", "label")),
            schedule_id=None,
            requested_date=payload.requested_date,
            participant_count=payload.participant_count,
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
