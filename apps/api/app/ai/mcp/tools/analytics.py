from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId

from app.ai.mcp.tool_contracts import (
    ChannelPerformanceInput,
    ChannelPerformanceItem,
    ChannelPerformanceOutput,
    EquineWorkloadReportInput,
    EquineWorkloadReportOutput,
    FunnelStageItem,
    OccupancyItem,
    OccupancyReportInput,
    OccupancyReportOutput,
    ReservationFunnelInput,
    ReservationFunnelOutput,
    SalesSummaryInput,
    SalesSummaryOutput,
    StatusSalesItem,
    ToolBlockingReason,
    WorkloadSummaryItem,
)
from app.common.enums import ReservationStatus
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ReservationDocument,
)
from app.documents.tool_call_log_document import ToolCallLogDocument

RESERVATION_FUNNEL_ORDER = [
    ReservationStatus.CONTACT,
    ReservationStatus.QUOTED,
    ReservationStatus.PENDING_PAYMENT,
    ReservationStatus.PAYMENT_RECEIVED,
    ReservationStatus.CONFIRMED,
    ReservationStatus.COMPLETED,
]


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


def _parse_date_range(
    date_from: str | None,
    date_to: str | None,
) -> tuple[datetime | None, datetime | None]:
    dt_from: datetime | None = None
    dt_to: datetime | None = None
    if date_from:
        dt_from = datetime.fromisoformat(date_from)
    if date_to:
        dt_to = datetime.fromisoformat(date_to)
    return dt_from, dt_to


def _date_from_kwargs(**kwargs: Any) -> tuple[str | None, str | None]:
    return kwargs.get("date_from"), kwargs.get("date_to")


def _build_created_at_filter(
    date_from: str | None,
    date_to: str | None,
) -> dict:
    f: dict[str, Any] = {}
    if date_from:
        f["$gte"] = datetime.fromisoformat(date_from)
    if date_to:
        f["$lte"] = datetime.fromisoformat(date_to)
    return f


async def admin_get_sales_summary(
    date_from: str | None = None,
    date_to: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: SalesSummaryInput | None = None
    output: SalesSummaryOutput | None = None
    error_code: str | None = None

    try:
        payload = SalesSummaryInput(date_from=date_from, date_to=date_to)

        created_filter = _build_created_at_filter(payload.date_from, payload.date_to)

        pipeline: list[dict] = []
        if created_filter:
            pipeline.append({"$match": {"created_at": created_filter}})
        pipeline.append({
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_amount": {"$sum": {"$ifNull": ["$quoted_total_amount", 0]}},
            }
        })
        results = await ReservationDocument.aggregate(pipeline).to_list()

        total = sum(r["count"] for r in results)
        total_revenue = sum(int(r["total_amount"]) for r in results)
        status_counts = {r["_id"]: r["count"] for r in results}
        by_status = [
            StatusSalesItem(status=s, count=c)
            for s, c in sorted(status_counts.items(), key=lambda x: str(x[0]))
        ]

        output = SalesSummaryOutput(
            trace_id=trace_id,
            total_reservations=total,
            by_status=by_status,
            total_revenue=total_revenue,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = SalesSummaryOutput(
            trace_id=trace_id,
            total_reservations=0,
            by_status=[],
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_sales_summary",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_reservation_funnel(
    date_from: str | None = None,
    date_to: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: ReservationFunnelInput | None = None
    output: ReservationFunnelOutput | None = None
    error_code: str | None = None

    try:
        payload = ReservationFunnelInput(date_from=date_from, date_to=date_to)

        created_filter = _build_created_at_filter(payload.date_from, payload.date_to)

        pipeline: list[dict] = []
        if created_filter:
            pipeline.append({"$match": {"created_at": created_filter}})
        pipeline.append({"$group": {"_id": "$status", "count": {"$sum": 1}}})
        results = await ReservationDocument.aggregate(pipeline).to_list()
        total = sum(r["count"] for r in results)
        status_counts = {r["_id"]: r["count"] for r in results}
        stages: list[FunnelStageItem] = []
        prev_count = total

        for status_enum in RESERVATION_FUNNEL_ORDER:
            count = status_counts.get(status_enum.value, 0)
            pct = (count / prev_count * 100) if prev_count > 0 else 0.0
            stages.append(
                FunnelStageItem(
                    stage=status_enum.value,
                    count=count,
                    conversion_pct=round(pct, 1),
                )
            )
            prev_count = count

        confirmed_or_completed = status_counts.get(
            ReservationStatus.CONFIRMED.value, 0
        ) + status_counts.get(ReservationStatus.COMPLETED.value, 0)

        output = ReservationFunnelOutput(
            trace_id=trace_id,
            stages=stages,
            total_start=total,
            total_converted=confirmed_or_completed,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = ReservationFunnelOutput(
            trace_id=trace_id,
            stages=[],
            total_start=0,
            total_converted=0,
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_reservation_funnel",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_channel_performance(
    date_from: str | None = None,
    date_to: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: ChannelPerformanceInput | None = None
    output: ChannelPerformanceOutput | None = None
    error_code: str | None = None

    try:
        payload = ChannelPerformanceInput(date_from=date_from, date_to=date_to)

        created_filter = _build_created_at_filter(payload.date_from, payload.date_to)

        pipeline: list[dict] = []
        if created_filter:
            pipeline.append({"$match": {"created_at": created_filter}})
        pipeline.append({
            "$group": {
                "_id": "$channel",
                "count": {"$sum": 1},
                "confirmed": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$status", ["confirmed", "completed"]]},
                            1,
                            0,
                        ]
                    }
                },
            }
        })
        results = await ReservationDocument.aggregate(pipeline).to_list()

        channels = [
            ChannelPerformanceItem(
                channel=r["_id"],
                count=r["count"],
                confirmed=r["confirmed"],
            )
            for r in sorted(results, key=lambda x: -x["count"])
        ]

        total = sum(r["count"] for r in results)

        output = ChannelPerformanceOutput(
            trace_id=trace_id,
            channels=channels,
            total=total,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = ChannelPerformanceOutput(
            trace_id=trace_id,
            channels=[],
            total=0,
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_channel_performance",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_occupancy_report(
    date_from: str | None = None,
    date_to: str | None = None,
    experience_id: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: OccupancyReportInput | None = None
    output: OccupancyReportOutput | None = None
    error_code: str | None = None

    try:
        payload = OccupancyReportInput(
            date_from=date_from,
            date_to=date_to,
            experience_id=experience_id,
        )

        query: dict[str, Any] = {
            "status": {
                "$in": [
                    ReservationStatus.CONFIRMED.value,
                    ReservationStatus.PAYMENT_RECEIVED.value,
                    ReservationStatus.PRE_RESERVED.value,
                ]
            },
            "requested_date": {"$ne": None},
        }
        if payload.date_from:
            query["requested_date"] = query.get("requested_date", {})
            if not isinstance(query["requested_date"], dict):
                query["requested_date"] = {}
            query["requested_date"]["$gte"] = date.fromisoformat(payload.date_from)
        if payload.date_to:
            if not isinstance(query.get("requested_date"), dict):
                query["requested_date"] = {}
            query["requested_date"]["$lte"] = date.fromisoformat(payload.date_to)
        if payload.experience_id:
            query["experience_id"] = PydanticObjectId(payload.experience_id)

        reservations = await ReservationDocument.find(query).to_list()

        occupancy: list[OccupancyItem] = []
        total_pct = 0.0

        for reservation in reservations:
            experience_name = ""
            if reservation.experience_id:
                exp_doc = await ExperienceDocument.get(reservation.experience_id)
                if exp_doc:
                    experience_name = getattr(exp_doc, "name", "") or ""

            r_date = reservation.requested_date
            participant_count = reservation.participant_count or 0
            pct = 100.0 if reservation.status == ReservationStatus.CONFIRMED else 50.0
            occupancy.append(
                OccupancyItem(
                    date=r_date.isoformat() if r_date else "",
                    experience_name=experience_name,
                    capacity_total=participant_count,
                    reserved=participant_count if reservation.status == ReservationStatus.CONFIRMED else 0,
                    available=0 if reservation.status == ReservationStatus.CONFIRMED else participant_count,
                    occupancy_pct=round(pct, 1),
                )
            )
            total_pct += pct

        avg_pct = round(total_pct / len(reservations), 1) if reservations else 0.0

        output = OccupancyReportOutput(
            trace_id=trace_id,
            occupancy=occupancy,
            total_schedules=len(reservations),
            avg_occupancy_pct=avg_pct,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = OccupancyReportOutput(
            trace_id=trace_id,
            occupancy=[],
            total_schedules=0,
            avg_occupancy_pct=0.0,
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_occupancy_report",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_equine_workload_report(
    date_from: str | None = None,
    date_to: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: EquineWorkloadReportInput | None = None
    output: EquineWorkloadReportOutput | None = None
    error_code: str | None = None

    try:
        payload = EquineWorkloadReportInput(date_from=date_from, date_to=date_to)

        equines = await EquineDocument.find_all().to_list()  # known-small: < 200 equines
        total_assignments = 0
        workload: list[WorkloadSummaryItem] = []

        for equine in equines:
            all_assignments = await AssignmentDocument.find(
                {"equine_id": equine.id, "is_active": True}
            ).to_list()
            # Excluir canceladas y reemplazadas del cómputo de carga
            assignments = [
                a for a in all_assignments
                if a.status not in ("cancelled", "replaced")
            ]

            count_in_range = 0
            for a in assignments:
                reservation = await ReservationDocument.get(a.reservation_id)
                if reservation is None:
                    continue
                if payload.date_from:
                    rd = reservation.requested_date
                    if rd and rd < date.fromisoformat(payload.date_from):
                        continue
                if payload.date_to:
                    rd = reservation.requested_date
                    if rd and rd > date.fromisoformat(payload.date_to):
                        continue
                count_in_range += 1

            total_assignments += count_in_range
            workload.append(
                WorkloadSummaryItem(
                    equine_id=_safe_str(equine.id) or "",
                    name=equine.name,
                    is_available=equine.is_available,
                    total_assignments_in_range=count_in_range,
                )
            )

        workload.sort(key=lambda x: -x.total_assignments_in_range)

        output = EquineWorkloadReportOutput(
            trace_id=trace_id,
            workload=workload,
            total_equines=len(equines),
            total_assignments=total_assignments,
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = EquineWorkloadReportOutput(
            trace_id=trace_id,
            workload=[],
            total_equines=0,
            total_assignments=0,
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_equine_workload_report",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
