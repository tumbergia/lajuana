from __future__ import annotations

import asyncio
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from bson.decimal128 import Decimal128

from app.common.enums import ReservationStatus
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    EquineEventDocument,
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    ReservationDocument,
    UserDocument,
)
from app.documents.equine_event_document import EquineEventType
from app.schemas.analytics import AnalyticsResponse, LeadCategory, LeadItem

TTL_SECONDS = 300

_cache: dict[str, Any] = {}
_cache_time: float = 0

# Low-value / slow-changing KPIs: visible in full list, excluded from home pool by default.
HOME_INELIGIBLE_IDS: frozenset[str] = frozenset(
    {
        "eq_total",
        "eq_mules",
        "eq_horses",
        "eq_donkeys",
        "par_total",
        "par_avg_age",
        "par_top_level",
        "ori_total_paises",
        "ori_top_pais",
        "ori_top_pct",
        "ori_top_5",
        "exp_total",
        "exp_published",
        "exp_routes",
        "exp_experiences",
        "exp_private",
        "vol_total",
        "op_usuarios",
        "op_usuarios_total",
        "pay_total",
    }
)

# Default home fill weights (money / revenue / action bias). Missing → 1.
HOME_PRIORITY_BY_ID: dict[str, int] = {
    "ing_total": 10,
    "ing_confirmed": 10,
    "ing_avg_reserva": 8,
    "ing_avg_participante": 7,
    "vol_pending_payment": 9,
    "vol_payment_received": 9,
    "pay_received": 8,
    "pay_pending": 7,
    "pay_verification_rate": 8,
    "pay_verified": 6,
    "pay_rejected": 5,
    "vol_quoted": 6,
    "vol_contact": 5,
    "vol_conversion": 6,
    "vol_activas": 5,
    "vol_confirmed": 5,
    "eq_overdue_care": 6,
    "eq_high_severity": 6,
    "eq_injured": 5,
    "eq_open_injuries": 5,
    "eq_due_soon": 4,
    "par_pending": 5,
    "par_completion_rate": 4,
    "op_asignaciones": 4,
    "eq_available": 4,
    "eq_workload": 3,
}

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
    return float(value or 0)


def _count_by_field(
    results: list[dict[str, Any]],
    field: str = "_id",
) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        out[str(r.get(field, "unknown"))] = r.get("count", 0)
    return out


def _lead(
    *,
    id: str,
    category: str,
    title: str,
    value: str,
    unit: str,
    description: str,
    icon: str,
    order: int,
    details: list[dict[str, str]] | None = None,
    home_eligible: bool | None = None,
    home_priority: int | None = None,
) -> LeadItem:
    eligible = (
        home_eligible if home_eligible is not None else id not in HOME_INELIGIBLE_IDS
    )
    priority = (
        home_priority
        if home_priority is not None
        else HOME_PRIORITY_BY_ID.get(id, 1)
    )
    return LeadItem(
        id=id,
        category=category,
        title=title,
        value=value,
        unit=unit,
        description=description,
        icon=icon,
        order=order,
        details=details or [],
        home_eligible=eligible,
        home_priority=max(1, priority) if eligible else 0,
    )


class AnalyticsService:
    @staticmethod
    async def _aggregate(model_class: Any, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        collection = model_class.get_motor_collection()
        cursor = await collection.aggregate(pipeline)
        return await cursor.to_list()

    async def get_all_leads(self, force_refresh: bool = False) -> AnalyticsResponse:
        global _cache_time
        now = time.monotonic()
        if not force_refresh and _cache and (now - _cache_time) < TTL_SECONDS:
            return AnalyticsResponse(**_cache["response"])

        categories = await asyncio.gather(
            self._compute_accion(),
            self._compute_reservas(),
            self._compute_dinero(),
            self._compute_eq_operacion(),
            self._compute_eq_salud(),
            self._compute_personas(),
            self._compute_catalogo(),
        )

        total = sum(len(c.leads) for c in categories)
        response = AnalyticsResponse(
            categories=[c for c in categories if c.leads],
            generated_at=datetime.now(timezone.utc),
            total_leads=total,
        )
        _cache["response"] = response.model_dump(mode="json")
        _cache_time = now
        return response

    async def _reservation_status_counts(self) -> dict[str, int]:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        raw = await self._aggregate(ReservationDocument, pipeline)
        return _count_by_field(raw)

    async def _compute_accion(self) -> LeadCategory:
        counts = await self._reservation_status_counts()

        pay_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        pay_raw = await self._aggregate(PaymentProofDocument, pay_pipeline)
        pay_counts = _count_by_field(pay_raw)

        par_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$is_completed", "count": {"$sum": 1}}}
        ]
        par_raw = await self._aggregate(ParticipantDocument, par_pipeline)
        completed_map = {str(r["_id"]): r["count"] for r in par_raw}
        not_completed = completed_map.get("False", 0)

        active_assignments = await AssignmentDocument.find({"is_active": True}).count()

        leads = [
            _lead(
                id="vol_contact",
                category="accion",
                title="Nuevos leads",
                value=str(counts.get(ReservationStatus.CONTACT.value, 0)),
                unit="contactos",
                description="Contactos nuevos sin cotizar",
                icon="contact_mail",
                order=1,
            ),
            _lead(
                id="vol_quoted",
                category="accion",
                title="Cotizadas",
                value=str(counts.get(ReservationStatus.QUOTED.value, 0)),
                unit="cotizaciones",
                description="Reservas con cotizacion enviada",
                icon="request_quote",
                order=2,
            ),
            _lead(
                id="vol_pending_payment",
                category="accion",
                title="Pendientes de pago",
                value=str(counts.get(ReservationStatus.PENDING_PAYMENT.value, 0)),
                unit="reservas",
                description="Esperando comprobante de pago",
                icon="hourglass_bottom",
                order=3,
            ),
            _lead(
                id="vol_payment_received",
                category="accion",
                title="Pago recibido",
                value=str(counts.get(ReservationStatus.PAYMENT_RECEIVED.value, 0)),
                unit="reservas",
                description="Comprobante recibido, pendiente de verificacion",
                icon="payments",
                order=4,
            ),
            _lead(
                id="pay_received",
                category="accion",
                title="Comprobantes por verificar",
                value=str(pay_counts.get("received", 0)),
                unit="comprobantes",
                description="Comprobantes recibidos pendientes de verificacion",
                icon="download",
                order=5,
            ),
            _lead(
                id="pay_pending",
                category="accion",
                title="Comprobantes pendientes",
                value=str(pay_counts.get("pending", 0)),
                unit="comprobantes",
                description="Comprobantes en estado pendiente",
                icon="hourglass_empty",
                order=6,
            ),
            _lead(
                id="par_pending",
                category="accion",
                title="Formularios pendientes",
                value=str(not_completed),
                unit="participantes",
                description="Participantes con formulario incompleto",
                icon="assignment_late",
                order=7,
            ),
            _lead(
                id="op_asignaciones",
                category="accion",
                title="Asignaciones activas",
                value=str(active_assignments),
                unit="asignaciones",
                description="Asignaciones activas de equinos a participantes",
                icon="link",
                order=8,
            ),
        ]
        return LeadCategory(
            id="accion", name="Pendientes de accion", icon="priority_high", leads=leads
        )

    async def _compute_reservas(self) -> LeadCategory:
        counts = await self._reservation_status_counts()
        total = sum(counts.values())
        activas = sum(
            counts.get(s.value, 0)
            for s in ReservationStatus
            if s
            not in (
                ReservationStatus.CANCELLED,
                ReservationStatus.EXPIRED,
                ReservationStatus.COMPLETED,
            )
        )
        completadas = counts.get(ReservationStatus.COMPLETED.value, 0)
        conversion = round(completadas / total * 100, 1) if total else 0.0

        status_labels = {
            "contact": "Contacto",
            "quoted": "Cotizada",
            "pending_payment": "Pendiente pago",
            "payment_received": "Pago recibido",
            "confirmed": "Confirmada",
            "pre_reserved": "Pre-reservada",
            "cancelled": "Cancelada",
            "completed": "Completada",
            "expired": "Expirada",
        }
        all_statuses = sorted(
            (s.value for s in ReservationStatus), key=lambda x: counts.get(x, 0), reverse=True
        )
        vol_details = [
            {"Estado": status_labels.get(s, s), "Cantidad": str(counts.get(s, 0))}
            for s in all_statuses
        ]

        leads = [
            _lead(
                id="vol_activas",
                category="reservas",
                title="Reservas activas",
                value=str(activas),
                unit="reservas",
                description="Reservas en curso (no canceladas ni expiradas)",
                icon="pending_actions",
                order=1,
            ),
            _lead(
                id="vol_confirmed",
                category="reservas",
                title="Confirmadas",
                value=str(counts.get(ReservationStatus.CONFIRMED.value, 0)),
                unit="reservas",
                description="Reservas confirmadas",
                icon="check_circle",
                order=2,
            ),
            _lead(
                id="vol_completed",
                category="reservas",
                title="Completadas",
                value=str(completadas),
                unit="reservas",
                description="Reservas finalizadas exitosamente",
                icon="task_alt",
                order=3,
            ),
            _lead(
                id="vol_cancelled",
                category="reservas",
                title="Canceladas",
                value=str(counts.get(ReservationStatus.CANCELLED.value, 0)),
                unit="reservas",
                description="Reservas canceladas",
                icon="cancel",
                order=4,
            ),
            _lead(
                id="vol_conversion",
                category="reservas",
                title="Tasa de conversion",
                value=f"{conversion}%",
                unit="%",
                description="Porcentaje de reservas que llegaron a completadas",
                icon="trending_up",
                order=5,
            ),
            _lead(
                id="vol_total",
                category="reservas",
                title="Total reservas",
                value=str(total),
                unit="reservas",
                description="Todas las reservas registradas en el sistema",
                icon="receipt_long",
                order=6,
                details=vol_details,
            ),
        ]
        return LeadCategory(
            id="reservas", name="Embudo de reservas", icon="bar_chart", leads=leads
        )

    async def _compute_dinero(self) -> LeadCategory:
        pipeline: list[dict[str, Any]] = [
            {"$match": {"quoted_total_amount": {"$ne": None}}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$quoted_total_amount"},
                    "count": {"$sum": 1},
                    "participants_sum": {"$sum": "$participant_count"},
                }
            },
        ]
        raw = await self._aggregate(ReservationDocument, pipeline)
        total_ingresos = int(_to_num(raw[0]["total"])) if raw else 0
        reservas_con_monto = raw[0]["count"] if raw else 0
        participantes_total = raw[0]["participants_sum"] if raw else 0

        avg_reserva = round(total_ingresos / reservas_con_monto) if reservas_con_monto else 0
        avg_participante = (
            round(total_ingresos / participantes_total) if participantes_total else 0
        )

        confirmed_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "status": {
                        "$in": [
                            ReservationStatus.CONFIRMED.value,
                            ReservationStatus.COMPLETED.value,
                        ]
                    },
                    "quoted_total_amount": {"$ne": None},
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$quoted_total_amount"}}},
        ]
        confirmed_raw = await self._aggregate(ReservationDocument, confirmed_pipeline)
        confirmed_ingresos = int(_to_num(confirmed_raw[0]["total"])) if confirmed_raw else 0

        pay_total = await PaymentProofDocument.count()
        pay_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        pay_raw = await self._aggregate(PaymentProofDocument, pay_pipeline)
        pay_counts = _count_by_field(pay_raw)
        verified = pay_counts.get("verified", 0)
        rejected = pay_counts.get("rejected", 0)
        verification_rate = round(verified / pay_total * 100, 1) if pay_total else 0.0

        pay_status_labels = {
            "pending": "Pendiente",
            "received": "Recibido",
            "verified": "Verificado",
            "rejected": "Rechazado",
        }
        pay_details = [
            {"Estado": pay_status_labels.get(s, s), "Cantidad": str(pay_counts.get(s, 0))}
            for s in ("pending", "received", "verified", "rejected")
        ]

        leads = [
            _lead(
                id="ing_total",
                category="dinero",
                title="Ingreso total facturado",
                value=f"${total_ingresos:,}",
                unit="COP",
                description="Suma de todos los montos cotizados",
                icon="account_balance",
                order=1,
            ),
            _lead(
                id="ing_avg_reserva",
                category="dinero",
                title="Promedio por reserva",
                value=f"${avg_reserva:,}",
                unit="COP",
                description="Monto promedio cotizado por reserva",
                icon="receipt",
                order=2,
            ),
            _lead(
                id="ing_confirmed",
                category="dinero",
                title="Ingreso de confirmadas/completadas",
                value=f"${confirmed_ingresos:,}",
                unit="COP",
                description="Suma de montos de reservas confirmadas o completadas",
                icon="verified",
                order=3,
            ),
            _lead(
                id="ing_avg_participante",
                category="dinero",
                title="Ticket promedio por participante",
                value=f"${avg_participante:,}",
                unit="COP",
                description="Monto promedio por participante",
                icon="groups",
                order=4,
            ),
            _lead(
                id="pay_verified",
                category="dinero",
                title="Comprobantes verificados",
                value=str(verified),
                unit="comprobantes",
                description="Comprobantes verificados correctamente",
                icon="verified",
                order=5,
            ),
            _lead(
                id="pay_rejected",
                category="dinero",
                title="Comprobantes rechazados",
                value=str(rejected),
                unit="comprobantes",
                description="Comprobantes rechazados",
                icon="cancel",
                order=6,
            ),
            _lead(
                id="pay_verification_rate",
                category="dinero",
                title="Tasa de verificacion",
                value=f"{verification_rate}%",
                unit="%",
                description="Porcentaje de comprobantes verificados",
                icon="check_circle",
                order=7,
            ),
            _lead(
                id="pay_total",
                category="dinero",
                title="Total comprobantes",
                value=str(pay_total),
                unit="comprobantes",
                description="Total de comprobantes de pago registrados",
                icon="receipt_long",
                order=8,
                details=pay_details,
            ),
        ]
        return LeadCategory(
            id="dinero", name="Ingresos y pagos", icon="monetization_on", leads=leads
        )

    async def _compute_eq_operacion(self) -> LeadCategory:
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$operational_status", "count": {"$sum": 1}}}
        ]
        raw = await self._aggregate(EquineDocument, pipeline)
        counts = _count_by_field(raw)

        total = sum(counts.values())
        available = counts.get("available", 0)
        resting = counts.get("resting", 0)
        in_service = counts.get("in_service", 0)
        unavailable = counts.get("unavailable", 0)

        workload_total = sum(
            getattr(e, "workload_last_7_days", 0) or 0
            for e in await EquineDocument.find_all().to_list()
        )
        avg_workload = round(workload_total / total, 1) if total else 0.0

        op_status_labels = {
            "available": "Disponible",
            "resting": "Descanso",
            "in_service": "En servicio",
            "injured": "Lesionado",
            "retired": "Retirado",
            "unavailable": "No disponible",
            "restricted": "Restringido",
        }
        eq_details = [
            {"Estado": op_status_labels.get(s, s), "Cantidad": str(counts.get(s, 0))}
            for s in sorted(counts, key=counts.get, reverse=True)
        ]

        leads = [
            _lead(
                id="eq_available",
                category="eq_operacion",
                title="Disponibles",
                value=str(available),
                unit="equinos",
                description="Equinos disponibles para asignar",
                icon="check",
                order=1,
                details=eq_details,
            ),
            _lead(
                id="eq_in_service",
                category="eq_operacion",
                title="En servicio",
                value=str(in_service),
                unit="equinos",
                description="Equinos actualmente en servicio",
                icon="construction",
                order=2,
            ),
            _lead(
                id="eq_resting",
                category="eq_operacion",
                title="En descanso",
                value=str(resting),
                unit="equinos",
                description="Equinos en periodo de descanso",
                icon="bedtime",
                order=3,
            ),
            _lead(
                id="eq_unavailable",
                category="eq_operacion",
                title="No disponibles",
                value=str(unavailable),
                unit="equinos",
                description="Equinos no disponibles por otras razones",
                icon="block",
                order=4,
            ),
            _lead(
                id="eq_workload",
                category="eq_operacion",
                title="Carga laboral semanal",
                value=str(avg_workload),
                unit="promedio",
                description="Promedio de asignaciones por equino en los ultimos 7 dias",
                icon="fitness_center",
                order=5,
            ),
        ]
        return LeadCategory(
            id="eq_operacion",
            name="Equinos (operacion)",
            icon="pets",
            leads=leads,
        )

    async def _compute_eq_salud(self) -> LeadCategory:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        due_soon_end = now + timedelta(days=14)

        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$operational_status", "count": {"$sum": 1}}}
        ]
        status_raw = await self._aggregate(EquineDocument, pipeline)
        status_counts = _count_by_field(status_raw)
        injured = status_counts.get("injured", 0)

        health_7d_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "event_type": {"$in": _HEALTH_EVENT_TYPES},
                    "happened_at": {"$gte": week_ago},
                }
            },
            {"$count": "count"},
        ]
        health_7d_raw = await self._aggregate(EquineEventDocument, health_7d_pipeline)
        health_7d = health_7d_raw[0]["count"] if health_7d_raw else 0

        overdue_pipeline: list[dict[str, Any]] = [
            {"$match": {"next_due_at": {"$ne": None, "$lt": now}}},
            {"$sort": {"next_due_at": 1}},
            {"$limit": 20},
        ]
        overdue_raw = await self._aggregate(EquineEventDocument, overdue_pipeline)
        overdue_count_pipeline: list[dict[str, Any]] = [
            {"$match": {"next_due_at": {"$ne": None, "$lt": now}}},
            {"$count": "count"},
        ]
        overdue_count_raw = await self._aggregate(
            EquineEventDocument, overdue_count_pipeline
        )
        overdue_count = overdue_count_raw[0]["count"] if overdue_count_raw else 0

        due_soon_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "next_due_at": {"$gte": now, "$lte": due_soon_end},
                }
            },
            {"$count": "count"},
        ]
        due_soon_raw = await self._aggregate(EquineEventDocument, due_soon_pipeline)
        due_soon = due_soon_raw[0]["count"] if due_soon_raw else 0

        injury_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "event_type": EquineEventType.INJURY.value,
                    "happened_at": {"$gte": month_ago},
                }
            },
            {"$group": {"_id": "$equine_id", "count": {"$sum": 1}, "last": {"$max": "$happened_at"}}},
            {"$sort": {"last": -1}},
            {"$limit": 15},
        ]
        injury_raw = await self._aggregate(EquineEventDocument, injury_pipeline)
        open_injuries = len(injury_raw)

        severity_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "severity": {"$in": ["high", "critical"]},
                    "happened_at": {"$gte": month_ago},
                }
            },
            {"$count": "count"},
        ]
        severity_raw = await self._aggregate(EquineEventDocument, severity_pipeline)
        high_severity = severity_raw[0]["count"] if severity_raw else 0

        # Resolve equine names for details (best-effort).
        equine_ids = {r["_id"] for r in injury_raw if r.get("_id")}
        for r in overdue_raw[:10]:
            if r.get("equine_id"):
                equine_ids.add(r["equine_id"])
        name_by_id: dict[str, str] = {}
        if equine_ids:
            equines = await EquineDocument.find(
                {"_id": {"$in": list(equine_ids)}}
            ).to_list()
            name_by_id = {str(e.id): e.name for e in equines}

        injury_details = [
            {
                "Equino": name_by_id.get(str(r["_id"]), str(r["_id"])),
                "Eventos": str(r["count"]),
            }
            for r in injury_raw
        ]
        overdue_details = [
            {
                "Equino": name_by_id.get(str(r.get("equine_id")), str(r.get("equine_id"))),
                "Cuidado": str(r.get("title") or r.get("event_type") or ""),
                "Vencio": (
                    r["next_due_at"].isoformat()
                    if isinstance(r.get("next_due_at"), datetime)
                    else str(r.get("next_due_at") or "")
                ),
            }
            for r in overdue_raw[:10]
        ]

        type_breakdown_pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "event_type": {"$in": _HEALTH_EVENT_TYPES},
                    "happened_at": {"$gte": week_ago},
                }
            },
            {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        type_raw = await self._aggregate(EquineEventDocument, type_breakdown_pipeline)
        health_details = [
            {"Tipo": str(r["_id"]), "Cantidad": str(r["count"])} for r in type_raw
        ]

        leads = [
            _lead(
                id="eq_injured",
                category="eq_salud",
                title="Lesionados",
                value=str(injured),
                unit="equinos",
                description="Equinos con estado operacional lesionado",
                icon="sick",
                order=1,
            ),
            _lead(
                id="eq_open_injuries",
                category="eq_salud",
                title="Lesiones recientes",
                value=str(open_injuries),
                unit="equinos",
                description="Equinos con eventos de lesion en los ultimos 30 dias",
                icon="healing",
                order=2,
                details=injury_details,
            ),
            _lead(
                id="eq_overdue_care",
                category="eq_salud",
                title="Cuidados vencidos",
                value=str(overdue_count),
                unit="eventos",
                description="Eventos de bitacora con next_due_at vencido",
                icon="event_busy",
                order=3,
                details=overdue_details,
            ),
            _lead(
                id="eq_due_soon",
                category="eq_salud",
                title="Cuidados proximos",
                value=str(due_soon),
                unit="eventos",
                description="Cuidados con next_due_at en los proximos 14 dias",
                icon="event_available",
                order=4,
            ),
            _lead(
                id="eq_health_7d",
                category="eq_salud",
                title="Eventos de salud (7 dias)",
                value=str(health_7d),
                unit="eventos",
                description="Eventos de salud registrados en la bitacora en los ultimos 7 dias",
                icon="monitor_heart",
                order=5,
                details=health_details,
            ),
            _lead(
                id="eq_high_severity",
                category="eq_salud",
                title="Severidad alta/critica",
                value=str(high_severity),
                unit="eventos",
                description="Eventos de bitacora con severidad alta o critica en los ultimos 30 dias",
                icon="warning",
                order=6,
            ),
        ]
        return LeadCategory(
            id="eq_salud", name="Equinos (salud)", icon="health_and_safety", leads=leads
        )

    async def _compute_personas(self) -> LeadCategory:
        total = await ParticipantDocument.count()
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$is_completed", "count": {"$sum": 1}}}
        ]
        raw = await self._aggregate(ParticipantDocument, pipeline)
        completed_map = {str(r["_id"]): r["count"] for r in raw}
        completed = completed_map.get("True", 0)
        completion_rate = round(completed / total * 100, 1) if total else 0.0

        participants = await ParticipantDocument.find_all().to_list()
        ages: list[int] = []
        level_counts: dict[str, int] = {}
        for p in participants:
            if p.birth_date:
                ages.append((date.today() - p.birth_date).days // 365)
            if p.experience_level:
                key = (
                    p.experience_level.value
                    if hasattr(p.experience_level, "value")
                    else str(p.experience_level)
                )
                level_counts[key] = level_counts.get(key, 0) + 1
        avg_age = round(sum(ages) / len(ages), 1) if ages else 0
        most_common_level = max(level_counts, key=level_counts.get) if level_counts else "N/A"
        level_labels = {"basic": "Basico", "intermediate": "Intermedio", "advanced": "Avanzado"}

        country_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        country_raw = await self._aggregate(ParticipantDocument, country_pipeline)
        total_participantes = sum(r["count"] for r in country_raw)
        paises_representados = len(country_raw)
        top_pais = country_raw[0]["_id"] if country_raw else "N/A"
        top_count = country_raw[0]["count"] if country_raw else 0
        top_pct = (
            round(top_count / total_participantes * 100, 1) if total_participantes else 0.0
        )
        top_5_details = [
            {"Pais": str(r["_id"]), "Participantes": str(r["count"])}
            for r in country_raw[:5]
            if r["_id"]
        ]

        leads = [
            _lead(
                id="par_completed",
                category="personas",
                title="Formularios completados",
                value=str(completed),
                unit="participantes",
                description="Participantes con formulario completo",
                icon="assignment_turned_in",
                order=1,
            ),
            _lead(
                id="par_completion_rate",
                category="personas",
                title="Tasa de completitud",
                value=f"{completion_rate}%",
                unit="%",
                description="Porcentaje de formularios completados",
                icon="percent",
                order=2,
            ),
            _lead(
                id="ori_top_pais",
                category="personas",
                title="Principal pais de origen",
                value=str(top_pais) if top_pais else "N/A",
                unit="",
                description=(
                    f"Pais con mas participantes ({top_count} participantes, "
                    f"{top_pct}% del total)"
                ),
                icon="flag",
                order=3,
            ),
            _lead(
                id="ori_top_pct",
                category="personas",
                title="Concentracion top pais",
                value=f"{top_pct}%",
                unit="%",
                description=f"Porcentaje de participantes del pais principal ({top_pais})",
                icon="pie_chart",
                order=4,
            ),
            _lead(
                id="par_total",
                category="personas",
                title="Total participantes",
                value=str(total),
                unit="participantes",
                description="Total de participantes registrados",
                icon="people",
                order=5,
            ),
            _lead(
                id="par_avg_age",
                category="personas",
                title="Edad promedio",
                value=str(avg_age),
                unit="anos",
                description="Edad promedio de los participantes",
                icon="calendar_today",
                order=6,
            ),
            _lead(
                id="par_top_level",
                category="personas",
                title="Nivel mas comun",
                value=level_labels.get(most_common_level, most_common_level),
                unit="",
                description="Nivel de experiencia mas frecuente",
                icon="star",
                order=7,
            ),
            _lead(
                id="ori_total_paises",
                category="personas",
                title="Paises representados",
                value=str(paises_representados),
                unit="paises",
                description="Cantidad de paises de origen de los participantes",
                icon="public",
                order=8,
            ),
            _lead(
                id="ori_top_5",
                category="personas",
                title="Top 5 paises",
                value=str(top_count) if country_raw else "N/A",
                unit="participantes",
                description="Los 5 paises con mas participantes",
                icon="format_list_numbered",
                order=9,
                details=top_5_details,
            ),
        ]
        return LeadCategory(
            id="personas", name="Participantes y origen", icon="people", leads=leads
        )

    async def _compute_catalogo(self) -> LeadCategory:
        eq_total = await EquineDocument.count()
        species_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$species", "count": {"$sum": 1}}}
        ]
        species_raw = await self._aggregate(EquineDocument, species_pipeline)
        species_counts = _count_by_field(species_raw)

        exp_total = await ExperienceDocument.count()
        status_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_raw = await self._aggregate(ExperienceDocument, status_pipeline)
        status_counts = _count_by_field(status_raw)
        published = status_counts.get("published", 0)

        cat_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        cat_raw = await self._aggregate(ExperienceDocument, cat_pipeline)
        cat_counts = _count_by_field(cat_raw)

        top_exp_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$experience_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
        top_exp_raw = await self._aggregate(ReservationDocument, top_exp_pipeline)
        top_exp_name = "N/A"
        if top_exp_raw:
            exp = await ExperienceDocument.get(top_exp_raw[0]["_id"])
            if exp:
                top_exp_name = exp.name

        total_assignments = await AssignmentDocument.count()
        finalized = await AssignmentDocument.find({"status": "final"}).count()
        assign_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        assign_raw = await self._aggregate(AssignmentDocument, assign_pipeline)
        assign_counts = _count_by_field(assign_raw)
        assign_status_labels = {
            "draft": "Borrador",
            "confirmed": "Confirmada",
            "final": "Final",
            "replaced": "Reemplazada",
            "cancelled": "Cancelada",
        }
        assign_details = [
            {
                "Estado": assign_status_labels.get(s, s),
                "Cantidad": str(assign_counts.get(s, 0)),
            }
            for s in sorted(assign_counts, key=assign_counts.get, reverse=True)
        ]

        total_users = await UserDocument.count()
        active_users = await UserDocument.find({"is_active": True}).count()

        species_labels = {"horse": "Caballo", "mule": "Mula", "donkey": "Burro"}
        eq_details = [
            {"Especie": species_labels.get(s, s), "Cantidad": str(species_counts[s])}
            for s in sorted(species_counts, key=species_counts.get, reverse=True)
        ]

        leads = [
            _lead(
                id="eq_total",
                category="catalogo",
                title="Total equinos",
                value=str(eq_total),
                unit="equinos",
                description="Total de equinos registrados",
                icon="pets",
                order=1,
                details=eq_details,
            ),
            _lead(
                id="eq_horses",
                category="catalogo",
                title="Caballos",
                value=str(species_counts.get("horse", 0)),
                unit="equinos",
                description="Total de caballos registrados",
                icon="pets",
                order=2,
            ),
            _lead(
                id="eq_mules",
                category="catalogo",
                title="Mulas",
                value=str(species_counts.get("mule", 0)),
                unit="equinos",
                description="Total de mulas registradas",
                icon="pets",
                order=3,
            ),
            _lead(
                id="eq_donkeys",
                category="catalogo",
                title="Burros",
                value=str(species_counts.get("donkey", 0)),
                unit="equinos",
                description="Total de burros registrados",
                icon="pets",
                order=4,
            ),
            _lead(
                id="exp_total",
                category="catalogo",
                title="Total experiencias",
                value=str(exp_total),
                unit="experiencias",
                description="Total de experiencias en el catalogo",
                icon="menu_book",
                order=5,
            ),
            _lead(
                id="exp_published",
                category="catalogo",
                title="Publicadas",
                value=str(published),
                unit="experiencias",
                description="Experiencias publicadas activas",
                icon="public",
                order=6,
            ),
            _lead(
                id="exp_routes",
                category="catalogo",
                title="Rutas",
                value=str(cat_counts.get("route", 0)),
                unit="experiencias",
                description="Experiencias de tipo ruta",
                icon="route",
                order=7,
            ),
            _lead(
                id="exp_experiences",
                category="catalogo",
                title="Experiencias",
                value=str(cat_counts.get("experience", 0)),
                unit="experiencias",
                description="Experiencias de tipo experiencia",
                icon="stars",
                order=8,
            ),
            _lead(
                id="exp_private",
                category="catalogo",
                title="Privados",
                value=str(cat_counts.get("private", 0)),
                unit="experiencias",
                description="Experiencias de tipo privado",
                icon="lock",
                order=9,
            ),
            _lead(
                id="exp_top",
                category="catalogo",
                title="Mas reservada",
                value=top_exp_name,
                unit="",
                description="Experiencia con mas reservas",
                icon="emoji_events",
                order=10,
            ),
            _lead(
                id="op_asignaciones_total",
                category="catalogo",
                title="Total asignaciones",
                value=str(total_assignments),
                unit="asignaciones",
                description="Todas las asignaciones registradas",
                icon="list_alt",
                order=11,
                details=assign_details,
            ),
            _lead(
                id="op_finalizadas",
                category="catalogo",
                title="Asignaciones finalizadas",
                value=str(finalized),
                unit="asignaciones",
                description="Asignaciones marcadas como final",
                icon="flag",
                order=12,
            ),
            _lead(
                id="op_usuarios",
                category="catalogo",
                title="Usuarios activos",
                value=str(active_users),
                unit="usuarios",
                description="Usuarios con cuenta activa en el sistema",
                icon="person",
                order=13,
            ),
            _lead(
                id="op_usuarios_total",
                category="catalogo",
                title="Total usuarios",
                value=str(total_users),
                unit="usuarios",
                description="Todos los usuarios registrados",
                icon="group",
                order=14,
            ),
        ]
        return LeadCategory(
            id="catalogo", name="Inventario y catalogo", icon="inventory_2", leads=leads
        )

    async def generate_export(
        self, lead_id: str | None = None
    ) -> tuple[bytes, str]:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        response = await self.get_all_leads()
        wb = Workbook()

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="2D6A4F", end_color="2D6A4F", fill_type="solid"
        )
        sub_font = Font(italic=True, color="555555")

        if lead_id:
            all_leads = [lead for cat in response.categories for lead in cat.leads]
            target = next((l for l in all_leads if l.id == lead_id), None)
            if not target:
                wb.active.title = "No encontrado"
            else:
                ws = wb.active
                ws.title = target.id[:31]
                ws.append(["Indicador", target.title])
                ws.append(["Categoria", target.category])
                ws.append(["Valor", target.value])
                ws.append(["Unidad", target.unit])
                ws.append(["Descripcion", target.description])
                ws.append(["Generado", response.generated_at.isoformat()])
                if target.details:
                    ws.append([])
                    detail_keys = list(target.details[0].keys())
                    sub_header = ["", *detail_keys]
                    ws.append(sub_header)
                    for cell in ws[ws.max_row]:
                        cell.font = header_font
                        cell.fill = header_fill
                    for row in target.details:
                        ws.append(["", *(row.get(k, "") for k in detail_keys)])
                ws.column_dimensions["A"].width = 40
                ws.column_dimensions["B"].width = 30
            filename = f"lead_{lead_id}.xlsx"
        else:
            first = True
            for cat in response.categories:
                if first:
                    ws = wb.active
                    ws.title = cat.id[:31]
                    first = False
                else:
                    ws = wb.create_sheet(title=cat.id[:31])
                ws.append(["Indicador", "Valor", "Unidad", "Descripcion"])
                for cell in ws[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                for lead in cat.leads:
                    ws.append([lead.title, lead.value, lead.unit, lead.description])
                    if lead.details:
                        detail_keys = list(lead.details[0].keys())
                        ws.append(["", "", "", ""])
                        ws.append(["  Detalle", *detail_keys, "", ""])
                        for cell in ws[ws.max_row]:
                            cell.font = sub_font
                        for detail in lead.details:
                            ws.append(
                                ["", *(detail.get(k, "") for k in detail_keys), "", ""]
                            )
                        ws.append(["", "", "", ""])
                ws.column_dimensions["A"].width = 40
                ws.column_dimensions["B"].width = 30
                ws.column_dimensions["C"].width = 20
                ws.column_dimensions["D"].width = 15
                ws.column_dimensions["E"].width = 50
            filename = "todos_los_leads.xlsx"

        from io import BytesIO

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf.getvalue(), filename
