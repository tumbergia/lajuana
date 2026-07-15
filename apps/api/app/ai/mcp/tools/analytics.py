from __future__ import annotations

import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from bson.decimal128 import Decimal128

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
    ToolChartPoint,
    ToolChartSeries,
    ToolChartSpec,
    WorkloadSummaryItem,
)
from app.common.enums import ReservationStatus
from app.core.time import today_colombia
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ReservationDocument,
)
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.services.analytics_colors import CHANNEL_COLORS, series_color

RESERVATION_FUNNEL_ORDER = [
    ReservationStatus.CONTACT,
    ReservationStatus.QUOTED,
    ReservationStatus.PENDING_PAYMENT,
    ReservationStatus.PAYMENT_RECEIVED,
    ReservationStatus.CONFIRMED,
    ReservationStatus.COMPLETED,
]

_CONFIRMED_LIKE = [
    ReservationStatus.CONFIRMED.value,
    ReservationStatus.COMPLETED.value,
]

_CHANNEL_LABELS = {
    "whatsapp": "WhatsApp",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "email": "Email",
}

_FUNNEL_LABELS = {
    "contact": "Contacto",
    "quoted": "Cotizada",
    "pending_payment": "Pago pendiente",
    "payment_received": "Pago recibido",
    "confirmed": "Confirmada",
    "completed": "Completada",
}


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
        # Inclusive end-of-day when only a date is provided.
        end = datetime.fromisoformat(date_to)
        if end.hour == 0 and end.minute == 0 and end.second == 0 and "T" not in date_to:
            end = end.replace(hour=23, minute=59, second=59)
        f["$lte"] = end
    return f


def _period_subtitle(date_from: str | None, date_to: str | None) -> str | None:
    if date_from and date_to:
        return f"Del {date_from} al {date_to}"
    if date_from:
        return f"Desde {date_from}"
    if date_to:
        return f"Hasta {date_to}"
    return None


def _series_grain(date_from: str | None, date_to: str | None) -> str:
    """Match analytics dashboard grain: day ≤14d, week ≤90d, else month."""
    today = today_colombia()
    start = date.fromisoformat(date_from) if date_from else today
    end = date.fromisoformat(date_to) if date_to else today
    if end < start:
        start, end = end, start
    days = (end - start).days + 1
    if days <= 14:
        return "day"
    if days <= 90:
        return "week"
    return "month"


def _date_fmt_for_grain(grain: str) -> str:
    return {"day": "%Y-%m-%d", "week": "%G-W%V", "month": "%Y-%m"}[grain]


def _to_num(value: Any) -> float:
    """Convert Mongo aggregation numerics (incl. Decimal128) to float."""
    if value is None:
        return 0.0
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


async def _aggregate(pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run a Mongo aggregation via Motor (Beanie's Document.aggregate can leave
    AsyncCollection.aggregate unawaited on this Motor version)."""
    collection = ReservationDocument.get_motor_collection()
    cursor = await collection.aggregate(pipeline)
    return await cursor.to_list(length=None)


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

        status_pipeline: list[dict] = []
        if created_filter:
            status_pipeline.append({"$match": {"created_at": created_filter}})
        status_pipeline.append({
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_amount": {"$sum": {"$ifNull": ["$quoted_total_amount", 0]}},
            }
        })
        results = await _aggregate(status_pipeline)

        total = sum(r["count"] for r in results)
        status_counts = {r["_id"]: r["count"] for r in results}
        by_status = [
            StatusSalesItem(status=s, count=c)
            for s, c in sorted(status_counts.items(), key=lambda x: str(x[0]))
        ]
        # Committed revenue = quoted amount of confirmed/completed only.
        total_revenue = int(
            round(
                sum(
                    _to_num(r.get("total_amount"))
                    for r in results
                    if str(r.get("_id")) in _CONFIRMED_LIKE
                )
            )
        )

        # Temporal series of committed revenue (confirmed/completed only).
        grain = _series_grain(payload.date_from, payload.date_to)
        date_fmt = _date_fmt_for_grain(grain)
        series_match: dict[str, Any] = {
            "status": {"$in": _CONFIRMED_LIKE},
            "quoted_total_amount": {"$ne": None},
        }
        if created_filter:
            series_match["created_at"] = created_filter
        series_pipeline: list[dict] = [
            {"$match": series_match},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": date_fmt, "date": "$created_at"}},
                    "total": {"$sum": "$quoted_total_amount"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        series_raw = await _aggregate(series_pipeline)
        series_points = [
            ToolChartPoint(label=str(r["_id"]), value=_to_num(r.get("total")))
            for r in series_raw
            if "total" in r
        ]
        chart = ToolChartSpec(
            type="line",
            value_type="currency",
            title="Ingresos comprometidos",
            subtitle=_period_subtitle(payload.date_from, payload.date_to),
            series=[
                ToolChartSeries(
                    label="Ingresos comprometidos",
                    points=series_points,
                    color=series_color(0),
                )
            ],
        )

        output = SalesSummaryOutput(
            trace_id=trace_id,
            total_reservations=total,
            by_status=by_status,
            total_revenue=total_revenue,
            date_from=payload.date_from,
            date_to=payload.date_to,
            chart=chart,
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
        results = await _aggregate(pipeline)
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
            chart=ToolChartSpec(
                type="bar",
                value_type="count",
                title="Embudo de reservas",
                subtitle=_period_subtitle(payload.date_from, payload.date_to),
                points=[
                    ToolChartPoint(
                        label=_FUNNEL_LABELS.get(s.stage, s.stage),
                        value=float(s.count),
                        secondary_label=f"{s.conversion_pct}%",
                        color=series_color(i),
                    )
                    for i, s in enumerate(stages)
                ],
            ),
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
        results = await _aggregate(pipeline)

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
            chart=ToolChartSpec(
                type="donut",
                value_type="count",
                title="Origen por canal",
                subtitle=_period_subtitle(payload.date_from, payload.date_to),
                points=[
                    ToolChartPoint(
                        label=_CHANNEL_LABELS.get(c.channel, c.channel),
                        value=float(c.count),
                        secondary_label=f"{c.confirmed} confirmadas",
                        color=CHANNEL_COLORS.get(c.channel, series_color(i)),
                    )
                    for i, c in enumerate(channels)
                ],
            ),
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

        # Aggregate occupancy by experience for a compact bar chart.
        by_experience: dict[str, dict[str, float]] = {}
        for item in occupancy:
            bucket = by_experience.setdefault(
                item.experience_name or "Sin experiencia",
                {"reserved": 0.0, "capacity": 0.0},
            )
            bucket["reserved"] += item.reserved
            bucket["capacity"] += item.capacity_total
        chart_points = [
            ToolChartPoint(
                label=name,
                value=round(
                    (vals["reserved"] / vals["capacity"] * 100)
                    if vals["capacity"] > 0
                    else 0.0,
                    1,
                ),
                secondary_label=f"{int(vals['reserved'])}/{int(vals['capacity'])}",
                color=series_color(i),
            )
            for i, (name, vals) in enumerate(by_experience.items())
        ]
        if not chart_points:
            chart_points = [
                ToolChartPoint(
                    label="Ocupación promedio",
                    value=avg_pct,
                    color=series_color(0),
                )
            ]

        output = OccupancyReportOutput(
            trace_id=trace_id,
            occupancy=occupancy,
            total_schedules=len(reservations),
            avg_occupancy_pct=avg_pct,
            date_from=payload.date_from,
            date_to=payload.date_to,
            chart=ToolChartSpec(
                type="bar",
                value_type="percent",
                title="Ocupación por experiencia",
                subtitle=_period_subtitle(payload.date_from, payload.date_to),
                points=chart_points,
            ),
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
            chart=ToolChartSpec(
                type="bar",
                value_type="count",
                title="Carga equina",
                subtitle=_period_subtitle(payload.date_from, payload.date_to),
                points=[
                    ToolChartPoint(
                        label=w.name,
                        value=float(w.total_assignments_in_range),
                        secondary_label="disponible" if w.is_available else "no disponible",
                        color=series_color(i),
                    )
                    for i, w in enumerate(workload[:12])
                ],
            ),
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
