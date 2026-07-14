"""Deterministic analytics query engine — single source of truth for calculations."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from bson.decimal128 import Decimal128

from app.common.enums import (
    Permission,
    ROLE_PERMISSIONS,
    ReservationStatus,
    UserRole,
)
from app.core.time import APP_TIMEZONE, today_colombia
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    EquineEventDocument,
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    ReservationDocument,
)
from app.documents.equine_event_document import EquineEventType
from app.schemas.analytics_v2 import (
    ANALYTICS_SCHEMA_VERSION,
    AnalyticsModule,
    BreakdownItem,
    Comparison,
    DashboardQuery,
    DashboardResponse,
    DateRangePreset,
    Freshness,
    ModuleAction,
    ModuleCategory,
    ModuleStatus,
    Period,
    PrimaryValue,
    RankingItem,
    Series,
    SeriesPoint,
    ValueType,
    VisualizationType,
    build_comparison,
    format_count,
    format_currency_cop,
    freshness_label,
)
from app.services.analytics_catalog_service import AnalyticsCatalogService
from app.services.analytics_country_normalizer import AnalyticsCountryNormalizer

TTL_SECONDS = 120

_STATUS_LABELS = {
    "contact": "Contacto",
    "quoted": "Cotizada",
    "pending_payment": "Pendiente de pago",
    "payment_received": "Pago recibido",
    "confirmed": "Confirmada",
    "pre_reserved": "Pre-reservada",
    "cancelled": "Cancelada",
    "completed": "Completada",
    "expired": "Expirada",
}

_PAY_LABELS = {
    "pending": "Pendiente",
    "received": "Por revisar",
    "verified": "Verificado",
    "rejected": "Rechazado",
}

_EQ_STATUS_LABELS = {
    "available": "Disponibles",
    "resting": "En descanso",
    "in_service": "En servicio",
    "injured": "Lesionados",
    "retired": "Retirados",
    "unavailable": "No disponibles",
    "restricted": "Restringidos",
}

_CONFIRMED_LIKE = [
    ReservationStatus.CONFIRMED.value,
    ReservationStatus.COMPLETED.value,
]

_HEALTH_EVENT_TYPES = [
    EquineEventType.HEALTH_CHECK.value,
    EquineEventType.INJURY.value,
    EquineEventType.TREATMENT.value,
    EquineEventType.MEDICATION.value,
    EquineEventType.VACCINATION.value,
    EquineEventType.FARRIER.value,
    EquineEventType.HOOF_CARE.value,
    EquineEventType.DENTISTRY.value,
    EquineEventType.LAB_TEST.value,
]


def _to_num(value: Any) -> float:
    if isinstance(value, Decimal128):
        return float(value.to_decimal())
    if isinstance(value, int):
        return float(value)
    if value is None:
        return 0.0
    return float(value)


def _count_by_field(results: list[dict[str, Any]], field: str = "_id") -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        out[str(r.get(field, "unknown"))] = int(r.get("count", 0))
    return out


def resolve_period(
    query: DashboardQuery,
    *,
    today: date | None = None,
) -> tuple[Period, Period]:
    """Return (current_period, previous_period of equal length)."""
    today = today or today_colombia()
    preset = query.range
    if preset == DateRangePreset.CUSTOM and query.date_from and query.date_to:
        start, end = query.date_from, query.date_to
        if end < start:
            start, end = end, start
        label = f"Del {start.isoformat()} al {end.isoformat()}"
    elif preset == DateRangePreset.LAST_7_DAYS:
        end = today
        start = today - timedelta(days=6)
        label = "Últimos 7 días"
        preset = DateRangePreset.LAST_7_DAYS
    elif preset == DateRangePreset.LAST_3_MONTHS:
        end = today
        start = today - timedelta(days=89)
        label = "Últimos 3 meses"
    elif preset == DateRangePreset.THIS_YEAR:
        # Rolling ~12 months so the chart X axis has a full year of monthly ticks
        # (≈13 labels: start + 11 months + end), not sparse YTD.
        end = today
        start = today - timedelta(days=364)
        label = "Últimos 12 meses"
    else:
        end = today
        start = today - timedelta(days=29)
        label = "Últimos 30 días"
        preset = DateRangePreset.LAST_30_DAYS

    days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    current = Period(start=start, end=end, label=label, preset=preset)
    previous = Period(
        start=prev_start,
        end=prev_end,
        label="el periodo anterior",
        preset=None,
    )
    return current, previous


def aggregation_grain(period: Period) -> str:
    days = (period.end - period.start).days + 1
    if days <= 14:
        return "day"
    if days <= 90:
        return "week"
    return "month"


class AnalyticsQueryService:
    def __init__(
        self,
        catalog: AnalyticsCatalogService | None = None,
        country_normalizer: AnalyticsCountryNormalizer | None = None,
    ) -> None:
        self._catalog = catalog or AnalyticsCatalogService()
        self._countries = country_normalizer or AnalyticsCountryNormalizer()
        self._cache: dict[str, Any] = {}

    @staticmethod
    async def _aggregate(model_class: Any, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        collection = model_class.get_motor_collection()
        cursor = await collection.aggregate(pipeline)
        return await cursor.to_list(length=None)

    def _cache_key(
        self,
        *,
        role: UserRole,
        query: DashboardQuery,
        module_ids: list[str],
        period: Period,
    ) -> str:
        payload = {
            "sv": ANALYTICS_SCHEMA_VERSION,
            "role": role.value,
            "modules": module_ids,
            "from": period.start.isoformat(),
            "to": period.end.isoformat(),
            "comparison": query.comparison,
            "experience_id": query.experience_id,
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get_dashboard(
        self,
        *,
        role: UserRole,
        query: DashboardQuery,
        force_refresh: bool = False,
    ) -> DashboardResponse:
        period, previous = resolve_period(query)
        allowed = self._catalog.allowed_module_ids(role)
        requested = query.module_ids or list(allowed)
        module_ids = [m for m in requested if m in allowed]
        # Always include action_center when computing full dashboard if permitted
        if "action_center" in allowed and "action_center" not in module_ids:
            module_ids = ["action_center", *module_ids]

        key = self._cache_key(role=role, query=query, module_ids=module_ids, period=period)
        now_mono = time.monotonic()
        cached = self._cache.get(key)
        if not force_refresh and cached and (now_mono - cached["t"]) < TTL_SECONDS:
            return DashboardResponse(**cached["response"])

        now = datetime.now(timezone.utc)
        fresh = Freshness(
            generated_at=now,
            label=freshness_label(now, now=now),
            is_stale=False,
            is_local=False,
        )

        builders = {
            "action_center": self._module_action_center,
            "reservation_trend": self._module_reservation_trend,
            "reservation_status": self._module_reservation_status,
            "confirmed_value_trend": self._module_confirmed_value,
            "payment_status": self._module_payment_status,
            "top_experiences": self._module_top_experiences,
            "occupancy": self._module_occupancy,
            "top_countries": self._module_top_countries,
            "participant_readiness": self._module_participant_readiness,
            "equine_availability": self._module_equine_availability,
            "equine_workload": self._module_equine_workload,
            "equine_care_alerts": self._module_equine_care_alerts,
        }

        tasks = []
        ids_to_build = []
        for mid in module_ids:
            fn = builders.get(mid)
            if fn:
                ids_to_build.append(mid)
                tasks.append(fn(period=period, previous=previous, query=query, now=now, freshness=fresh))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        modules: list[AnalyticsModule] = []
        for mid, result in zip(ids_to_build, results, strict=True):
            if isinstance(result, Exception):
                modules.append(
                    AnalyticsModule(
                        id=mid,
                        category=ModuleCategory.OPERATIONS,
                        title=mid,
                        description="",
                        visualization=VisualizationType.KPI,
                        period=period,
                        status=ModuleStatus.ERROR,
                        insight_text=(
                            "No pudimos actualizar esta información. Los demás "
                            "indicadores siguen disponibles."
                        ),
                        action=ModuleAction(label="Reintentar", target="retry"),
                        generated_at=now,
                        freshness=fresh,
                        empty_message=None,
                    )
                )
            else:
                modules.append(result)

        response = DashboardResponse(
            modules=modules,
            period=period,
            generated_at=now,
            freshness=fresh,
            schema_version=ANALYTICS_SCHEMA_VERSION,
        )
        self._cache[key] = {"t": now_mono, "response": response.model_dump(mode="json")}
        return response

    # ── helpers ──────────────────────────────────────────────────────────

    def _dt_bounds(self, period: Period) -> tuple[datetime, datetime]:
        start = datetime.combine(period.start, datetime.min.time(), tzinfo=APP_TIMEZONE)
        end = datetime.combine(period.end, datetime.max.time(), tzinfo=APP_TIMEZONE)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    async def _status_counts_in_period(self, period: Period) -> dict[str, int]:
        start, end = self._dt_bounds(period)
        pipeline = [
            {"$match": {"created_at": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        raw = await self._aggregate(ReservationDocument, pipeline)
        return _count_by_field(raw)

    async def _status_counts_all(self) -> dict[str, int]:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        raw = await self._aggregate(ReservationDocument, pipeline)
        return _count_by_field(raw)

    # ── modules ──────────────────────────────────────────────────────────

    async def _module_action_center(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        counts = await self._status_counts_all()
        pay_raw = await self._aggregate(
            PaymentProofDocument,
            [{"$group": {"_id": "$status", "count": {"$sum": 1}}}],
        )
        pay_counts = _count_by_field(pay_raw)

        overdue_raw = await self._aggregate(
            EquineEventDocument,
            [
                {"$match": {"next_due_at": {"$ne": None, "$lt": now}}},
                {"$count": "count"},
            ],
        )
        overdue = overdue_raw[0]["count"] if overdue_raw else 0

        items: list[BreakdownItem] = []
        actions_map = [
            (
                "contact",
                counts.get(ReservationStatus.CONTACT.value, 0),
                "Contactos nuevos sin cotizar",
                "Ver reservas",
                "reservations",
            ),
            (
                "pending_payment",
                counts.get(ReservationStatus.PENDING_PAYMENT.value, 0),
                "Pendientes de pago",
                "Ver reservas",
                "reservations",
            ),
            (
                "payment_received",
                counts.get(ReservationStatus.PAYMENT_RECEIVED.value, 0),
                "Pago por verificar",
                "Revisar comprobantes",
                "payment_proofs",
            ),
            (
                "pay_received",
                pay_counts.get("received", 0),
                "Comprobantes por revisar",
                "Revisar comprobantes",
                "payment_proofs",
            ),
            (
                "overdue_care",
                overdue,
                "Cuidados equinos vencidos",
                "Revisar cuidados",
                "equines",
            ),
        ]
        for key, value, label, _action_label, _target in actions_map:
            if value > 0:
                items.append(
                    BreakdownItem(
                        dimension="attention",
                        key=key,
                        label=label,
                        raw_value=float(value),
                        formatted_value=str(value),
                        unit="",
                    )
                )

        total = sum(int(i.raw_value) for i in items)
        status = ModuleStatus.OK if total > 0 else ModuleStatus.EMPTY
        insight = (
            f"Hay {total} pendientes que necesitan atención."
            if total > 0
            else "No hay pendientes críticos en este momento."
        )
        return AnalyticsModule(
            id="action_center",
            category=ModuleCategory.ACTION,
            title="Tareas pendientes",
            description="Pendientes que requieren acción inmediata.",
            visualization=VisualizationType.ACTION_LIST,
            period=period,
            primary_value=PrimaryValue(
                raw=float(total),
                formatted=str(total),
                unit="pendientes",
                value_type=ValueType.COUNT,
            ),
            breakdown=items,
            status=status,
            insight_text=insight,
            action=(
                ModuleAction(label="Ver reservas", target="reservations")
                if total > 0
                else None
            ),
            generated_at=now,
            freshness=freshness,
            empty_message="No hay pendientes críticos.",
        )

    async def _module_reservation_trend(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        start, end = self._dt_bounds(period)
        grain = aggregation_grain(period)
        if grain == "day":
            date_fmt = "%Y-%m-%d"
        elif grain == "week":
            date_fmt = "%G-W%V"
        else:
            date_fmt = "%Y-%m"

        pipeline = [
            {"$match": {"created_at": {"$gte": start, "$lte": end}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": date_fmt, "date": "$created_at"}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        raw = await self._aggregate(ReservationDocument, pipeline)
        points = [
            SeriesPoint(
                raw=float(r["count"]),
                unit="reservas",
                label=str(r["_id"]),
                category=str(r["_id"]),
            )
            for r in raw
        ]
        total = sum(p.raw for p in points)

        prev_start, prev_end = self._dt_bounds(previous)
        prev_pipeline = [
            {"$match": {"created_at": {"$gte": prev_start, "$lte": prev_end}}},
            {"$count": "count"},
        ]
        prev_raw = await self._aggregate(ReservationDocument, prev_pipeline)
        prev_total = float(prev_raw[0]["count"]) if prev_raw else 0.0
        comparison = (
            build_comparison(
                current=total,
                previous=prev_total,
                previous_label=previous.label,
                unit="reservas",
            )
            if query.comparison
            else None
        )

        if total == 0:
            insight = "Todavía no hay reservas nuevas en este periodo."
            status = ModuleStatus.EMPTY
        elif comparison and comparison.label:
            insight = comparison.label[0].upper() + comparison.label[1:] + "."
        else:
            insight = f"Se registraron {int(total)} reservas nuevas en {period.label.lower()}."

        return AnalyticsModule(
            id="reservation_trend",
            category=ModuleCategory.RESERVATIONS,
            title="Tendencia de reservas",
            description="Reservas nuevas registradas en el periodo.",
            visualization=VisualizationType.LINE,
            period=period,
            primary_value=PrimaryValue(
                raw=total,
                formatted=format_count(total),
                unit="reservas",
                value_type=ValueType.COUNT,
            ),
            comparison=comparison,
            series=[Series(id="reservations", label="Reservas nuevas", unit="reservas", points=points)],
            status=status if total == 0 else ModuleStatus.OK,
            insight_text=insight,
            action=ModuleAction(label="Ver reservas", target="reservations"),
            generated_at=now,
            freshness=freshness,
            empty_message="Todavía no hay reservas nuevas en este periodo.",
        )

    async def _module_reservation_status(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        counts = await self._status_counts_in_period(period)
        total = sum(counts.values())
        breakdown = [
            BreakdownItem(
                dimension="status",
                key=key,
                label=_STATUS_LABELS.get(key, key),
                raw_value=float(value),
                formatted_value=str(value),
                unit="reservas",
                share_percentage=round(value / total * 100, 1) if total else 0.0,
            )
            for key, value in sorted(counts.items(), key=lambda x: -x[1])
        ]
        top = breakdown[0] if breakdown else None
        if total == 0:
            insight = "Todavía no hay reservas en este periodo."
            status = ModuleStatus.EMPTY
        elif top:
            insight = (
                f"La mayoría de las reservas de este periodo están en estado "
                f"«{top.label}» ({int(top.raw_value)})."
            )
            status = ModuleStatus.OK
        else:
            insight = None
            status = ModuleStatus.OK

        return AnalyticsModule(
            id="reservation_status",
            category=ModuleCategory.RESERVATIONS,
            title="Estado de las reservas",
            description="Distribución por estado en el periodo (no es una tasa de conversión).",
            visualization=VisualizationType.DONUT,
            period=period,
            primary_value=PrimaryValue(
                raw=float(total),
                formatted=str(total),
                unit="reservas",
                value_type=ValueType.COUNT,
            ),
            breakdown=breakdown,
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Ver reservas", target="reservations"),
            generated_at=now,
            freshness=freshness,
            empty_message="Todavía no hay reservas en este periodo.",
            blocked_reason=(
                "La tasa de conversión comercial está bloqueada: no hay "
                "historial de embudo suficiente."
            ),
        )

    async def _module_confirmed_value(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        start, end = self._dt_bounds(period)
        grain = aggregation_grain(period)
        date_fmt = {"day": "%Y-%m-%d", "week": "%G-W%V", "month": "%Y-%m"}[grain]

        match = {
            "status": {"$in": _CONFIRMED_LIKE},
            "quoted_total_amount": {"$ne": None},
            "created_at": {"$gte": start, "$lte": end},
        }
        # Prefer requested_date when present for "service period"; fallback created_at filter already applied
        pipeline_total = [
            {"$match": match},
            {"$group": {"_id": None, "total": {"$sum": "$quoted_total_amount"}, "count": {"$sum": 1}}},
        ]
        total_raw = await self._aggregate(ReservationDocument, pipeline_total)
        total = _to_num(total_raw[0]["total"]) if total_raw else 0.0

        series_pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": date_fmt, "date": "$created_at"}},
                    "total": {"$sum": "$quoted_total_amount"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        series_raw = await self._aggregate(ReservationDocument, series_pipeline)
        points = [
            SeriesPoint(
                raw=_to_num(r["total"]),
                unit="COP",
                label=str(r["_id"]),
                category=str(r["_id"]),
            )
            for r in series_raw
        ]

        prev_start, prev_end = self._dt_bounds(previous)
        prev_pipeline = [
            {
                "$match": {
                    "status": {"$in": _CONFIRMED_LIKE},
                    "quoted_total_amount": {"$ne": None},
                    "created_at": {"$gte": prev_start, "$lte": prev_end},
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$quoted_total_amount"}}},
        ]
        prev_raw = await self._aggregate(ReservationDocument, prev_pipeline)
        prev_total = _to_num(prev_raw[0]["total"]) if prev_raw else 0.0
        comparison = (
            build_comparison(
                current=total,
                previous=prev_total,
                previous_label=previous.label,
                value_type=ValueType.CURRENCY,
            )
            if query.comparison
            else None
        )

        if total == 0:
            insight = "Todavía no hay reservas confirmadas con monto en este periodo."
            status = ModuleStatus.EMPTY
        elif comparison and comparison.label:
            insight = (
                f"Tienes {format_currency_cop(total)} COP en ingresos comprometidos. "
                f"{comparison.label[0].upper() + comparison.label[1:]}."
            )
            status = ModuleStatus.OK
        else:
            insight = (
                f"Tienes {format_currency_cop(total)} COP en ingresos comprometidos "
                "en este periodo."
            )
            status = ModuleStatus.OK

        return AnalyticsModule(
            id="confirmed_value_trend",
            category=ModuleCategory.MONEY,
            title="Ingresos comprometidos",
            description=(
                "Monto cotizado de reservas confirmadas o completadas: lo que ya está "
                "asegurado para facturar, aunque el pago todavía no se haya recibido."
            ),
            visualization=VisualizationType.LINE,
            period=period,
            primary_value=PrimaryValue(
                raw=total,
                formatted=format_currency_cop(total),
                unit="COP",
                value_type=ValueType.CURRENCY,
            ),
            comparison=comparison,
            series=[
                Series(
                    id="confirmed_value",
                    label="Ingresos comprometidos",
                    unit="COP",
                    points=points,
                )
            ],
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Ver reservas", target="reservations"),
            generated_at=now,
            freshness=freshness,
            empty_message="Todavía no hay reservas confirmadas con monto en este periodo.",
        )

    async def _module_payment_status(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        start, end = self._dt_bounds(period)
        pipeline = [
            {"$match": {"uploaded_at": {"$gte": start, "$lte": end}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        raw = await self._aggregate(PaymentProofDocument, pipeline)
        counts = _count_by_field(raw)
        total = sum(counts.values())
        breakdown = [
            BreakdownItem(
                dimension="payment_status",
                key=k,
                label=_PAY_LABELS.get(k, k),
                raw_value=float(v),
                formatted_value=str(v),
                unit="comprobantes",
                share_percentage=round(v / total * 100, 1) if total else 0.0,
            )
            for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ]
        pending_review = counts.get("received", 0) + counts.get("pending", 0)
        if total == 0:
            insight = "No hay comprobantes en este periodo."
            status = ModuleStatus.EMPTY
        elif pending_review > 0:
            insight = f"Hay {pending_review} comprobantes que todavía necesitan revisión."
            status = ModuleStatus.OK
        else:
            insight = "No hay comprobantes pendientes por revisar."
            status = ModuleStatus.OK

        return AnalyticsModule(
            id="payment_status",
            category=ModuleCategory.MONEY,
            title="Comprobantes de pago",
            description="Estado de los comprobantes. No incluye montos cobrados.",
            visualization=VisualizationType.DONUT,
            period=period,
            primary_value=PrimaryValue(
                raw=float(pending_review),
                formatted=str(pending_review),
                unit="por revisar",
                value_type=ValueType.COUNT,
            ),
            breakdown=breakdown,
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Revisar comprobantes", target="payment_proofs"),
            generated_at=now,
            freshness=freshness,
            empty_message="No hay comprobantes pendientes por revisar.",
            blocked_reason=(
                "Ingreso cobrado bloqueado: los comprobantes no registran montos."
            ),
        )

    async def _module_top_experiences(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        start, end = self._dt_bounds(period)
        pipeline = [
            {
                "$match": {
                    "status": {"$in": _CONFIRMED_LIKE},
                    "created_at": {"$gte": start, "$lte": end},
                }
            },
            {"$group": {"_id": "$experience_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        raw = await self._aggregate(ReservationDocument, pipeline)
        total = sum(int(r["count"]) for r in raw)
        ranking: list[RankingItem] = []
        for idx, r in enumerate(raw, start=1):
            exp = await ExperienceDocument.get(r["_id"])
            name = exp.name if exp else "Experiencia"
            count = int(r["count"])
            ranking.append(
                RankingItem(
                    rank=idx,
                    key=str(r["_id"]),
                    label=name,
                    raw_value=float(count),
                    formatted_value=str(count),
                    unit="reservas",
                    share_percentage=round(count / total * 100, 1) if total else 0.0,
                )
            )

        if not ranking:
            insight = "Todavía no hay reservas confirmadas en este periodo."
            status = ModuleStatus.EMPTY
            primary = 0.0
        else:
            top = ranking[0]
            insight = (
                f"{top.label} representa {int(top.raw_value)} de cada "
                f"{max(1, int(round(100 / (top.share_percentage or 100))))} "
                f"reservas confirmadas."
                if top.share_percentage and top.share_percentage >= 10
                else f"{top.label} fue la experiencia más reservada."
            )
            # Simpler insight:
            insight = (
                f"{top.label} concentra {int(top.raw_value)} de {int(total)} "
                f"reservas confirmadas."
            )
            status = ModuleStatus.OK
            primary = float(total)

        return AnalyticsModule(
            id="top_experiences",
            category=ModuleCategory.EXPERIENCES,
            title="Experiencias más reservadas",
            description="Reservas confirmadas o completadas en el periodo.",
            visualization=VisualizationType.RANKING,
            period=period,
            primary_value=PrimaryValue(
                raw=primary,
                formatted=format_count(primary),
                unit="reservas",
                value_type=ValueType.COUNT,
            ),
            ranking=ranking,
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Ver experiencia", target="experiences"),
            generated_at=now,
            freshness=freshness,
            empty_message="Todavía no hay reservas confirmadas en este periodo.",
        )

    async def _module_occupancy(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        today = today_colombia()
        horizon = today + timedelta(days=30)
        pipeline = [
            {
                "$match": {
                    "status": ReservationStatus.CONFIRMED.value,
                    "requested_date": {"$gte": today.isoformat(), "$lte": horizon.isoformat()},
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": "$requested_date",
                        "experience_id": "$experience_id",
                    },
                    "participants": {"$sum": "$participant_count"},
                }
            },
            {"$sort": {"_id.date": 1}},
            {"$limit": 20},
        ]
        # requested_date is stored as date — match with date objects when possible
        pipeline[0]["$match"]["requested_date"] = {"$gte": today, "$lte": horizon}
        raw = await self._aggregate(ReservationDocument, pipeline)

        ranking: list[RankingItem] = []
        degraded = False
        low_occupancy = 0
        for idx, r in enumerate(raw, start=1):
            exp_id = r["_id"]["experience_id"]
            exp = await ExperienceDocument.get(exp_id)
            name = exp.name if exp else "Experiencia"
            capacity = None
            if exp:
                capacity = exp.standard_max_participants or exp.base_capacity
            participants = int(r["participants"])
            if not capacity or capacity <= 0:
                degraded = True
                share = None
                label = f"{name} · {r['_id']['date']}"
                formatted = f"{participants} participantes"
            else:
                share = round(participants / capacity * 100, 1)
                label = f"{name} · {r['_id']['date']}"
                formatted = f"{participants}/{capacity}"
                if share >= 75:
                    low_occupancy += 0
                elif share < 25:
                    low_occupancy += 1
            ranking.append(
                RankingItem(
                    rank=idx,
                    key=f"{exp_id}:{r['_id']['date']}",
                    label=str(label),
                    raw_value=float(participants),
                    formatted_value=formatted,
                    unit="participantes",
                    share_percentage=share,
                )
            )

        total_upcoming = len(ranking)
        if total_upcoming == 0:
            insight = "No hay salidas programadas para los próximos 30 días."
            status = ModuleStatus.EMPTY
        elif low_occupancy > 0:
            insight = (
                f"{low_occupancy} salida{'s' if low_occupancy != 1 else ''} próxima"
                f"{'s' if low_occupancy != 1 else ''} "
                f"tiene{'n' if low_occupancy != 1 else ''} menos del 25 % de sus cupos ocupados."
            )
            status = ModuleStatus.DEGRADED if degraded else ModuleStatus.OK
        else:
            insight = f"Hay {total_upcoming} salidas confirmadas en los próximos 30 días."
            status = ModuleStatus.DEGRADED if degraded else ModuleStatus.OK

        return AnalyticsModule(
            id="occupancy",
            category=ModuleCategory.OPERATIONS,
            title="Ocupación de próximas salidas",
            description=(
                "Participantes confirmados frente al cupo de la experiencia. "
                "No usa capacidad de un schedule (no existe)."
            ),
            visualization=VisualizationType.PROGRESS,
            period=Period(
                start=today,
                end=horizon,
                label="Próximos 30 días",
                preset=DateRangePreset.CUSTOM,
            ),
            primary_value=PrimaryValue(
                raw=float(total_upcoming),
                formatted=str(total_upcoming),
                unit="salidas",
                value_type=ValueType.COUNT,
            ),
            ranking=ranking,
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Ver próximas salidas", target="reservations"),
            generated_at=now,
            freshness=freshness,
            empty_message="No hay salidas programadas para los próximos 30 días.",
        )

    async def _module_top_countries(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        start, end = self._dt_bounds(period)
        # Participants of confirmed/completed reservations in period
        res_pipeline = [
            {
                "$match": {
                    "status": {"$in": _CONFIRMED_LIKE},
                    "created_at": {"$gte": start, "$lte": end},
                }
            },
            {"$project": {"_id": 1}},
        ]
        res_raw = await self._aggregate(ReservationDocument, res_pipeline)
        res_ids = [r["_id"] for r in res_raw]
        if not res_ids:
            return AnalyticsModule(
                id="top_countries",
                category=ModuleCategory.PARTICIPANTS,
                title="Países de los visitantes",
                description=(
                    "Países de residencia de participantes en reservas "
                    "confirmadas o completadas del periodo."
                ),
                visualization=VisualizationType.RANKING,
                period=period,
                primary_value=PrimaryValue(
                    raw=0, formatted="0", unit="participantes", value_type=ValueType.COUNT
                ),
                ranking=[],
                status=ModuleStatus.EMPTY,
                insight_text=(
                    "Aún no hay suficientes participantes registrados "
                    "para mostrar países principales."
                ),
                action=ModuleAction(label="Completar participantes", target="participants"),
                generated_at=now,
                freshness=freshness,
                empty_message=(
                    "Aún no hay suficientes participantes registrados "
                    "para mostrar países principales."
                ),
            )

        par_pipeline = [
            {"$match": {"reservation_id": {"$in": res_ids}}},
            {
                "$group": {
                    "_id": {
                        "code": "$country_code",
                        "name": "$country_name",
                        "raw": "$country",
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
        ]
        par_raw = await self._aggregate(ParticipantDocument, par_pipeline)

        # Aggregate by resolved code
        buckets: dict[str, dict[str, Any]] = {}
        for r in par_raw:
            code = r["_id"].get("code")
            name = r["_id"].get("name")
            raw_country = r["_id"].get("raw")
            if not code:
                result = self._countries.normalize(raw_country)
                code = result.country_code
                name = result.country_name
            key = code or "__unknown__"
            if key not in buckets:
                buckets[key] = {
                    "code": code,
                    "name": name or AnalyticsCountryNormalizer.display_name(code, raw_country),
                    "count": 0,
                }
            buckets[key]["count"] += int(r["count"])

        ordered = sorted(buckets.values(), key=lambda x: -x["count"])
        total = sum(b["count"] for b in ordered)
        top5 = ordered[:5]
        others = ordered[5:]
        ranking: list[RankingItem] = []
        for idx, b in enumerate(top5, start=1):
            ranking.append(
                RankingItem(
                    rank=idx,
                    key=b["code"] or "unknown",
                    label=b["name"],
                    raw_value=float(b["count"]),
                    formatted_value=str(b["count"]),
                    unit="participantes",
                    share_percentage=round(b["count"] / total * 100, 1) if total else 0.0,
                    country_code=b["code"],
                    country_name=b["name"],
                )
            )
        if others:
            other_count = sum(b["count"] for b in others)
            ranking.append(
                RankingItem(
                    rank=len(ranking) + 1,
                    key="others",
                    label="Otros",
                    raw_value=float(other_count),
                    formatted_value=str(other_count),
                    unit="participantes",
                    share_percentage=round(other_count / total * 100, 1) if total else 0.0,
                    country_code=None,
                    country_name="Otros",
                )
            )

        if ranking and ranking[0].country_code:
            insight = (
                f"{ranking[0].label} fue el principal país de residencia "
                f"de los visitantes en {period.label.lower()}."
            )
            status = ModuleStatus.OK
        elif ranking:
            insight = "Hay participantes sin país normalizado en este periodo."
            status = ModuleStatus.DEGRADED
        else:
            insight = (
                "Aún no hay suficientes participantes registrados "
                "para mostrar países principales."
            )
            status = ModuleStatus.EMPTY

        return AnalyticsModule(
            id="top_countries",
            category=ModuleCategory.PARTICIPANTS,
            title="Países de los visitantes",
            description=(
                "Países de residencia de participantes en reservas "
                "confirmadas o completadas del periodo."
            ),
            visualization=VisualizationType.RANKING,
            period=period,
            primary_value=PrimaryValue(
                raw=float(total),
                formatted=str(total),
                unit="participantes",
                value_type=ValueType.COUNT,
            ),
            ranking=ranking,
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Completar participantes", target="participants"),
            generated_at=now,
            freshness=freshness,
            empty_message=(
                "Aún no hay suficientes participantes registrados "
                "para mostrar países principales."
            ),
        )

    async def _module_participant_readiness(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        today = today_colombia()
        horizon = today + timedelta(days=30)
        pipeline = [
            {
                "$match": {
                    "status": ReservationStatus.CONFIRMED.value,
                    "requested_date": {"$gte": today, "$lte": horizon},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "expected": {
                        "$sum": {
                            "$ifNull": [
                                "$expected_participants_count",
                                "$participant_count",
                            ]
                        }
                    },
                    "completed": {"$sum": "$participants_completed_count"},
                }
            },
        ]
        raw = await self._aggregate(ReservationDocument, pipeline)
        expected = int(raw[0]["expected"]) if raw else 0
        completed = int(raw[0]["completed"]) if raw else 0
        pending = max(0, expected - completed)
        rate = round(completed / expected * 100, 1) if expected else 0.0

        if expected == 0:
            insight = "No hay salidas confirmadas próximas con participantes esperados."
            status = ModuleStatus.EMPTY
        elif pending > 0:
            insight = (
                f"Faltan datos de {pending} participante{'s' if pending != 1 else ''} "
                f"para completar la preparación operativa."
            )
            status = ModuleStatus.OK
        else:
            insight = "Todos los participantes de las próximas salidas están registrados."
            status = ModuleStatus.OK

        return AnalyticsModule(
            id="participant_readiness",
            category=ModuleCategory.PARTICIPANTS,
            title="Preparación de participantes",
            description="Participantes esperados menos registros completos en salidas próximas.",
            visualization=VisualizationType.PROGRESS,
            period=Period(
                start=today,
                end=horizon,
                label="Próximos 30 días",
                preset=DateRangePreset.CUSTOM,
            ),
            primary_value=PrimaryValue(
                raw=float(pending),
                formatted=str(pending),
                unit="pendientes",
                value_type=ValueType.COUNT,
            ),
            breakdown=[
                BreakdownItem(
                    dimension="readiness",
                    key="completed",
                    label="Registrados",
                    raw_value=float(completed),
                    formatted_value=str(completed),
                    share_percentage=rate,
                ),
                BreakdownItem(
                    dimension="readiness",
                    key="pending",
                    label="Pendientes",
                    raw_value=float(pending),
                    formatted_value=str(pending),
                    share_percentage=round(100 - rate, 1) if expected else 0.0,
                ),
            ],
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Completar participantes", target="participants"),
            generated_at=now,
            freshness=freshness,
            empty_message="No hay salidas confirmadas próximas con participantes esperados.",
        )

    async def _module_equine_availability(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        pipeline = [{"$group": {"_id": "$operational_status", "count": {"$sum": 1}}}]
        raw = await self._aggregate(EquineDocument, pipeline)
        counts = _count_by_field(raw)
        total = sum(counts.values())
        available = counts.get("available", 0)
        breakdown = [
            BreakdownItem(
                dimension="operational_status",
                key=k,
                label=_EQ_STATUS_LABELS.get(k, k),
                raw_value=float(v),
                formatted_value=str(v),
                unit="equinos",
                share_percentage=round(v / total * 100, 1) if total else 0.0,
            )
            for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ]
        insight = (
            f"Hay {available} mula{'s' if available != 1 else ''} u equino"
            f"{'s' if available != 1 else ''} disponible"
            f"{'s' if available != 1 else ''} para asignar."
            if total
            else "No hay equinos registrados."
        )
        return AnalyticsModule(
            id="equine_availability",
            category=ModuleCategory.EQUINES,
            title="Disponibilidad equina",
            description="Estado operacional actual de los equinos.",
            visualization=VisualizationType.DONUT,
            period=period,
            primary_value=PrimaryValue(
                raw=float(available),
                formatted=str(available),
                unit="disponibles",
                value_type=ValueType.COUNT,
            ),
            breakdown=breakdown,
            status=ModuleStatus.EMPTY if total == 0 else ModuleStatus.OK,
            insight_text=insight,
            action=ModuleAction(label="Abrir detalle", target="equines"),
            generated_at=now,
            freshness=freshness,
            empty_message="No hay equinos registrados.",
        )

    async def _module_equine_workload(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        equines = await EquineDocument.find_all().to_list()
        ranking: list[RankingItem] = []
        workloads = sorted(
            equines,
            key=lambda e: getattr(e, "workload_last_7_days", 0) or 0,
            reverse=True,
        )
        for idx, e in enumerate(workloads[:10], start=1):
            wl = getattr(e, "workload_last_7_days", 0) or 0
            ranking.append(
                RankingItem(
                    rank=idx,
                    key=str(e.id),
                    label=e.name,
                    raw_value=float(wl),
                    formatted_value=str(wl),
                    unit="servicios",
                )
            )
        concentrated = sum(1 for r in ranking[:3] if r.raw_value > 0)
        total_wl = sum(r.raw_value for r in ranking)
        if total_wl == 0:
            insight = "No hay carga de trabajo registrada en los últimos 7 días."
            status = ModuleStatus.EMPTY
        elif concentrated >= 3:
            insight = "La carga de trabajo está concentrada en 3 mulas."
            status = ModuleStatus.OK
        else:
            insight = "La carga de trabajo se distribuye entre varios equinos."
            status = ModuleStatus.OK

        avg = round(total_wl / len(equines), 1) if equines else 0.0
        return AnalyticsModule(
            id="equine_workload",
            category=ModuleCategory.EQUINES,
            title="Carga de trabajo equina",
            description="Servicios recientes por equino (últimos 7 días).",
            visualization=VisualizationType.RANKING,
            period=period,
            primary_value=PrimaryValue(
                raw=avg,
                formatted=format_count(avg),
                unit="promedio",
                value_type=ValueType.RATIO,
            ),
            ranking=ranking,
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Abrir detalle", target="equines"),
            generated_at=now,
            freshness=freshness,
            empty_message="No hay carga de trabajo registrada en los últimos 7 días.",
        )

    async def _module_equine_care_alerts(
        self,
        *,
        period: Period,
        previous: Period,
        query: DashboardQuery,
        now: datetime,
        freshness: Freshness,
    ) -> AnalyticsModule:
        due_soon_end = now + timedelta(days=14)
        overdue_raw = await self._aggregate(
            EquineEventDocument,
            [
                {"$match": {"next_due_at": {"$ne": None, "$lt": now}}},
                {"$count": "count"},
            ],
        )
        overdue = overdue_raw[0]["count"] if overdue_raw else 0
        due_soon_raw = await self._aggregate(
            EquineEventDocument,
            [
                {"$match": {"next_due_at": {"$gte": now, "$lte": due_soon_end}}},
                {"$count": "count"},
            ],
        )
        due_soon = due_soon_raw[0]["count"] if due_soon_raw else 0
        injured_raw = await self._aggregate(
            EquineDocument,
            [
                {"$match": {"operational_status": "injured"}},
                {"$count": "count"},
            ],
        )
        injured = injured_raw[0]["count"] if injured_raw else 0

        items: list[BreakdownItem] = []
        if overdue:
            items.append(
                BreakdownItem(
                    dimension="care",
                    key="overdue",
                    label="Cuidados vencidos",
                    raw_value=float(overdue),
                    formatted_value=str(overdue),
                )
            )
        if due_soon:
            items.append(
                BreakdownItem(
                    dimension="care",
                    key="due_soon",
                    label="Cuidados próximos",
                    raw_value=float(due_soon),
                    formatted_value=str(due_soon),
                )
            )
        if injured:
            items.append(
                BreakdownItem(
                    dimension="care",
                    key="injured",
                    label="Equinos lesionados",
                    raw_value=float(injured),
                    formatted_value=str(injured),
                )
            )

        total = overdue + due_soon + injured
        if total == 0:
            insight = "No existen cuidados equinos vencidos."
            status = ModuleStatus.EMPTY
        elif overdue > 0:
            insight = f"Hay {overdue} cuidados que ya vencieron y requieren revisión."
            status = ModuleStatus.OK
        else:
            insight = f"Hay {due_soon} cuidados programados en los próximos 14 días."
            status = ModuleStatus.OK

        return AnalyticsModule(
            id="equine_care_alerts",
            category=ModuleCategory.EQUINES,
            title="Alertas de cuidados",
            description="Cuidados vencidos, próximos y equinos lesionados.",
            visualization=VisualizationType.ACTION_LIST,
            period=period,
            primary_value=PrimaryValue(
                raw=float(total),
                formatted=str(total),
                unit="alertas",
                value_type=ValueType.COUNT,
            ),
            breakdown=items,
            status=status,
            insight_text=insight,
            action=ModuleAction(label="Revisar cuidados", target="equines"),
            generated_at=now,
            freshness=freshness,
            empty_message="No existen cuidados equinos vencidos.",
        )
