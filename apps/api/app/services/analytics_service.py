from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from bson.decimal128 import Decimal128

from app.common.enums import ReservationStatus
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    ReservationDocument,
    UserDocument,
)
from app.schemas.analytics import AnalyticsResponse, LeadCategory, LeadItem

TTL_SECONDS = 300

_cache: dict[str, Any] = {}
_cache_time: float = 0


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
            self._compute_volumen(),
            self._compute_ingresos(),
            self._compute_equinos(),
            self._compute_participantes(),
            self._compute_origen(),
            self._compute_experiencias(),
            self._compute_pagos(),
            self._compute_operacion(),
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

    async def _compute_volumen(self) -> LeadCategory:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        raw = await self._aggregate(ReservationDocument, pipeline)
        counts = _count_by_field(raw)

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
            LeadItem(
                id="vol_total",
                category="volumen",
                title="Total reservas",
                value=str(total),
                unit="reservas",
                description="Todas las reservas registradas en el sistema",
                icon="receipt_long",
                order=1,
                details=vol_details,
            ),
            LeadItem(
                id="vol_activas",
                category="volumen",
                title="Reservas activas",
                value=str(activas),
                unit="reservas",
                description="Reservas en curso (no canceladas ni expiradas)",
                icon="pending_actions",
                order=2,
            ),
            LeadItem(
                id="vol_contact",
                category="volumen",
                title="Nuevos leads",
                value=str(counts.get(ReservationStatus.CONTACT.value, 0)),
                unit="contactos",
                description="Contactos nuevos sin cotizar",
                icon="contact_mail",
                order=3,
            ),
            LeadItem(
                id="vol_quoted",
                category="volumen",
                title="Cotizadas",
                value=str(counts.get(ReservationStatus.QUOTED.value, 0)),
                unit="cotizaciones",
                description="Reservas con cotizacion enviada",
                icon="request_quote",
                order=4,
            ),
            LeadItem(
                id="vol_pending_payment",
                category="volumen",
                title="Pendientes de pago",
                value=str(counts.get(ReservationStatus.PENDING_PAYMENT.value, 0)),
                unit="reservas",
                description="Esperando comprobante de pago",
                icon="hourglass_bottom",
                order=5,
            ),
            LeadItem(
                id="vol_payment_received",
                category="volumen",
                title="Pago recibido",
                value=str(counts.get(ReservationStatus.PAYMENT_RECEIVED.value, 0)),
                unit="reservas",
                description="Comprobante recibido, pendiente de verificacion",
                icon="payments",
                order=6,
            ),
            LeadItem(
                id="vol_confirmed",
                category="volumen",
                title="Confirmadas",
                value=str(counts.get(ReservationStatus.CONFIRMED.value, 0)),
                unit="reservas",
                description="Reservas confirmadas",
                icon="check_circle",
                order=7,
            ),
            LeadItem(
                id="vol_completed",
                category="volumen",
                title="Completadas",
                value=str(counts.get(ReservationStatus.COMPLETED.value, 0)),
                unit="reservas",
                description="Reservas finalizadas exitosamente",
                icon="task_alt",
                order=8,
            ),
            LeadItem(
                id="vol_cancelled",
                category="volumen",
                title="Canceladas",
                value=str(counts.get(ReservationStatus.CANCELLED.value, 0)),
                unit="reservas",
                description="Reservas canceladas",
                icon="cancel",
                order=9,
            ),
            LeadItem(
                id="vol_conversion",
                category="volumen",
                title="Tasa de conversion",
                value=f"{conversion}%",
                unit="%",
                description="Porcentaje de reservas que llegaron a completadas",
                icon="trending_up",
                order=10,
            ),
        ]
        return LeadCategory(id="volumen", name="Volumen de reservas", icon="bar_chart", leads=leads)

    async def _compute_ingresos(self) -> LeadCategory:
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
        avg_participante = round(total_ingresos / participantes_total) if participantes_total else 0

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

        leads = [
            LeadItem(
                id="ing_total",
                category="ingresos",
                title="Ingreso total facturado",
                value=f"${total_ingresos:,}",
                unit="COP",
                description="Suma de todos los montos cotizados",
                icon="account_balance",
                order=1,
            ),
            LeadItem(
                id="ing_avg_reserva",
                category="ingresos",
                title="Promedio por reserva",
                value=f"${avg_reserva:,}",
                unit="COP",
                description="Monto promedio cotizado por reserva",
                icon="receipt",
                order=2,
            ),
            LeadItem(
                id="ing_confirmed",
                category="ingresos",
                title="Ingreso de confirmadas/completadas",
                value=f"${confirmed_ingresos:,}",
                unit="COP",
                description="Suma de montos de reservas confirmadas o completadas",
                icon="verified",
                order=3,
            ),
            LeadItem(
                id="ing_avg_participante",
                category="ingresos",
                title="Ticket promedio por participante",
                value=f"${avg_participante:,}",
                unit="COP",
                description="Monto promedio por participante",
                icon="groups",
                order=4,
            ),
        ]
        return LeadCategory(id="ingresos", name="Ingresos", icon="monetization_on", leads=leads)

    async def _compute_equinos(self) -> LeadCategory:
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$operational_status", "count": {"$sum": 1}}}
        ]
        raw = await self._aggregate(EquineDocument, pipeline)
        counts = _count_by_field(raw)

        total = sum(counts.values())
        available = counts.get("available", 0)
        resting = counts.get("resting", 0)
        in_service = counts.get("in_service", 0)
        injured = counts.get("injured", 0)
        unavailable = counts.get("unavailable", 0)

        # workload: average assignments per equine in last 7 days
        workload_total = sum(
            getattr(e, "workload_last_7_days", 0) or 0
            for e in await EquineDocument.find_all().to_list()
        )
        avg_workload = round(workload_total / total, 1) if total else 0.0

        species_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$species", "count": {"$sum": 1}}}
        ]
        species_raw = await self._aggregate(EquineDocument, species_pipeline)
        species_counts = _count_by_field(species_raw)

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

        species_labels = {"horse": "Caballo", "mule": "Mula", "donkey": "Burro"}
        for s in sorted(species_counts, key=species_counts.get, reverse=True):
            eq_details.append(
                {"Estado": species_labels.get(s, s), "Cantidad": str(species_counts[s])}
            )

        leads = [
            LeadItem(
                id="eq_total",
                category="equinos",
                title="Total equinos",
                value=str(total),
                unit="equinos",
                description="Total de equinos registrados",
                icon="pets",
                order=1,
                details=eq_details,
            ),
            LeadItem(
                id="eq_available",
                category="equinos",
                title="Disponibles",
                value=str(available),
                unit="equinos",
                description="Equinos disponibles para asignar",
                icon="check",
                order=2,
            ),
            LeadItem(
                id="eq_resting",
                category="equinos",
                title="En descanso",
                value=str(resting),
                unit="equinos",
                description="Equinos en periodo de descanso",
                icon="bedtime",
                order=3,
            ),
            LeadItem(
                id="eq_in_service",
                category="equinos",
                title="En servicio",
                value=str(in_service),
                unit="equinos",
                description="Equinos actualmente en servicio",
                icon="construction",
                order=4,
            ),
            LeadItem(
                id="eq_injured",
                category="equinos",
                title="Lesionados",
                value=str(injured),
                unit="equinos",
                description="Equinos con lesion registrada",
                icon="sick",
                order=5,
            ),
            LeadItem(
                id="eq_unavailable",
                category="equinos",
                title="No disponibles",
                value=str(unavailable),
                unit="equinos",
                description="Equinos no disponibles por otras razones",
                icon="block",
                order=6,
            ),
            LeadItem(
                id="eq_workload",
                category="equinos",
                title="Carga laboral semanal",
                value=str(avg_workload),
                unit="promedio",
                description="Promedio de asignaciones por equino en los ultimos 7 dias",
                icon="fitness_center",
                order=7,
            ),
            LeadItem(
                id="eq_mules",
                category="equinos",
                title="Mulas",
                value=str(species_counts.get("mule", 0)),
                unit="equinos",
                description="Total de mulas registradas",
                icon="pets",
                order=8,
            ),
            LeadItem(
                id="eq_horses",
                category="equinos",
                title="Caballos",
                value=str(species_counts.get("horse", 0)),
                unit="equinos",
                description="Total de caballos registrados",
                icon="pets",
                order=9,
            ),
            LeadItem(
                id="eq_donkeys",
                category="equinos",
                title="Burros",
                value=str(species_counts.get("donkey", 0)),
                unit="equinos",
                description="Total de burros registrados",
                icon="pets",
                order=10,
            ),
        ]
        return LeadCategory(id="equinos", name="Equinos", icon="pets", leads=leads)

    async def _compute_participantes(self) -> LeadCategory:
        total = await ParticipantDocument.count()
        # form completion stats
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$is_completed", "count": {"$sum": 1}}}
        ]
        raw = await self._aggregate(ParticipantDocument, pipeline)
        completed_map = {str(r["_id"]): r["count"] for r in raw}
        completed = completed_map.get("True", 0)
        not_completed = completed_map.get("False", 0)
        completion_rate = round(completed / total * 100, 1) if total else 0.0

        # avg age
        from datetime import date

        participants = await ParticipantDocument.find_all().to_list()
        ages = []
        level_counts: dict[str, int] = {}
        for p in participants:
            if p.birth_date:
                age = (date.today() - p.birth_date).days // 365
                ages.append(age)
            if p.experience_level:
                key = p.experience_level.value if hasattr(p.experience_level, "value") else str(p.experience_level)
                level_counts[key] = level_counts.get(key, 0) + 1
        avg_age = round(sum(ages) / len(ages), 1) if ages else 0
        most_common_level = max(level_counts, key=level_counts.get) if level_counts else "N/A"

        level_labels = {"basic": "Basico", "intermediate": "Intermedio", "advanced": "Avanzado"}

        par_details = [
            {"Indicador": "Formulario completado", "Cantidad": str(completed)},
            {"Indicador": "Formulario pendiente", "Cantidad": str(not_completed)},
        ]
        for lv in sorted(level_counts, key=level_counts.get, reverse=True):
            par_details.append(
                {
                    "Indicador": f"Nivel {level_labels.get(lv, lv)}",
                    "Cantidad": str(level_counts[lv]),
                }
            )

        leads = [
            LeadItem(
                id="par_total",
                category="participantes",
                title="Total participantes",
                value=str(total),
                unit="participantes",
                description="Total de participantes registrados",
                icon="people",
                order=1,
                details=par_details,
            ),
            LeadItem(
                id="par_completed",
                category="participantes",
                title="Formularios completados",
                value=str(completed),
                unit="participantes",
                description="Participantes con formulario completo",
                icon="assignment_turned_in",
                order=2,
            ),
            LeadItem(
                id="par_pending",
                category="participantes",
                title="Formularios pendientes",
                value=str(not_completed),
                unit="participantes",
                description="Participantes con formulario incompleto",
                icon="assignment_late",
                order=3,
            ),
            LeadItem(
                id="par_completion_rate",
                category="participantes",
                title="Tasa de completitud",
                value=f"{completion_rate}%",
                unit="%",
                description="Porcentaje de formularios completados",
                icon="percent",
                order=4,
            ),
            LeadItem(
                id="par_avg_age",
                category="participantes",
                title="Edad promedio",
                value=str(avg_age),
                unit="anos",
                description="Edad promedio de los participantes",
                icon="calendar_today",
                order=5,
            ),
            LeadItem(
                id="par_top_level",
                category="participantes",
                title="Nivel mas comun",
                value=level_labels.get(most_common_level, most_common_level),
                unit="",
                description="Nivel de experiencia mas frecuente",
                icon="star",
                order=6,
            ),
        ]
        return LeadCategory(
            id="participantes", name="Participantes", icon="people", leads=leads
        )

    async def _compute_origen(self) -> LeadCategory:
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        raw = await self._aggregate(ParticipantDocument, pipeline)
        total_participantes = sum(r["count"] for r in raw)
        paises_representados = len(raw)

        top_pais = raw[0]["_id"] if raw else "N/A"
        top_count = raw[0]["count"] if raw else 0
        top_pct = round(top_count / total_participantes * 100, 1) if total_participantes else 0.0

        top_5 = raw[:5]
        top_5_details = [
            {"Pais": str(r["_id"]), "Participantes": str(r["count"])}
            for r in top_5 if r["_id"]
        ]

        leads = [
            LeadItem(
                id="ori_total_paises",
                category="origen",
                title="Paises representados",
                value=str(paises_representados),
                unit="paises",
                description="Cantidad de paises de origen de los participantes",
                icon="public",
                order=1,
            ),
            LeadItem(
                id="ori_top_pais",
                category="origen",
                title="Principal pais de origen",
                value=str(top_pais) if top_pais else "N/A",
                unit="",
                description=f"Pais con mas participantes ({top_count} participantes, {top_pct}% del total)",
                icon="flag",
                order=2,
            ),
            LeadItem(
                id="ori_top_pct",
                category="origen",
                title="Concentracion top pais",
                value=f"{top_pct}%",
                unit="%",
                description=f"Porcentaje de participantes del pais principal ({top_pais})",
                icon="pie_chart",
                order=3,
            ),
            LeadItem(
                id="ori_top_5",
                category="origen",
                title="Top 5 paises",
                value=str(top_count) if top_5 else "N/A",
                unit="participantes",
                description="Los 5 paises con mas participantes",
                icon="format_list_numbered",
                order=4,
                details=top_5_details,
            ),
        ]
        return LeadCategory(
            id="origen", name="Origen de participantes", icon="public", leads=leads
        )

    async def _compute_experiencias(self) -> LeadCategory:
        total = await ExperienceDocument.count()
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        raw = await self._aggregate(ExperienceDocument, pipeline)
        status_counts = _count_by_field(raw)
        published = status_counts.get("published", 0)

        cat_pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        cat_raw = await self._aggregate(ExperienceDocument, cat_pipeline)
        cat_counts = _count_by_field(cat_raw)

        # most reserved experience
        top_exp_pipeline: list[dict[str, Any]] = [
            {
                "$group": {
                    "_id": "$experience_id",
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
        top_exp_raw = await self._aggregate(ReservationDocument, top_exp_pipeline)
        top_exp_name = "N/A"
        if top_exp_raw:
            exp = await ExperienceDocument.get(top_exp_raw[0]["_id"])
            if exp:
                top_exp_name = exp.name

        category_labels = {"route": "Rutas", "experience": "Experiencias", "private": "Privados"}
        status_labels_exp = {"draft": "Borrador", "published": "Publicada", "archived": "Archivada"}

        exp_details = []
        for s in sorted(status_counts, key=status_counts.get, reverse=True):
            exp_details.append(
                {"Indicador": f"Estado {status_labels_exp.get(s, s)}", "Cantidad": str(status_counts[s])}
            )
        for c in sorted(cat_counts, key=cat_counts.get, reverse=True):
            exp_details.append(
                {"Indicador": f"Categoria {category_labels.get(c, c)}", "Cantidad": str(cat_counts[c])}
            )

        leads = [
            LeadItem(
                id="exp_total",
                category="experiencias",
                title="Total experiencias",
                value=str(total),
                unit="experiencias",
                description="Total de experiencias en el catalogo",
                icon="menu_book",
                order=1,
                details=exp_details,
            ),
            LeadItem(
                id="exp_published",
                category="experiencias",
                title="Publicadas",
                value=str(published),
                unit="experiencias",
                description="Experiencias publicadas activas",
                icon="public",
                order=2,
            ),
            LeadItem(
                id="exp_routes",
                category="experiencias",
                title="Rutas",
                value=str(cat_counts.get("route", 0)),
                unit="experiencias",
                description="Experiencias de tipo ruta",
                icon="route",
                order=3,
            ),
            LeadItem(
                id="exp_experiences",
                category="experiencias",
                title="Experiencias",
                value=str(cat_counts.get("experience", 0)),
                unit="experiencias",
                description="Experiencias de tipo experiencia",
                icon="stars",
                order=4,
            ),
            LeadItem(
                id="exp_private",
                category="experiencias",
                title="Privados",
                value=str(cat_counts.get("private", 0)),
                unit="experiencias",
                description="Experiencias de tipo privado",
                icon="lock",
                order=5,
            ),
            LeadItem(
                id="exp_top",
                category="experiencias",
                title="Mas reservada",
                value=top_exp_name,
                unit="",
                description="Experiencia con mas reservas",
                icon="emoji_events",
                order=6,
            ),
        ]
        return LeadCategory(
            id="experiencias", name="Experiencias", icon="menu_book", leads=leads
        )

    async def _compute_pagos(self) -> LeadCategory:
        total = await PaymentProofDocument.count()
        pipeline: list[dict[str, Any]] = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        raw = await self._aggregate(PaymentProofDocument, pipeline)
        counts = _count_by_field(raw)
        received = counts.get("received", 0)
        verified = counts.get("verified", 0)
        rejected = counts.get("rejected", 0)
        pending = counts.get("pending", 0)
        verification_rate = round(verified / total * 100, 1) if total else 0.0

        pay_status_labels = {
            "pending": "Pendiente",
            "received": "Recibido",
            "verified": "Verificado",
            "rejected": "Rechazado",
        }
        pay_details = [
            {"Estado": pay_status_labels.get(s, s), "Cantidad": str(counts.get(s, 0))}
            for s in ("pending", "received", "verified", "rejected")
        ]

        leads = [
            LeadItem(
                id="pay_total",
                category="pagos",
                title="Total comprobantes",
                value=str(total),
                unit="comprobantes",
                description="Total de comprobantes de pago registrados",
                icon="receipt_long",
                order=1,
                details=pay_details,
            ),
            LeadItem(
                id="pay_received",
                category="pagos",
                title="Recibidos",
                value=str(received),
                unit="comprobantes",
                description="Comprobantes recibidos pendientes de verificacion",
                icon="download",
                order=2,
            ),
            LeadItem(
                id="pay_verified",
                category="pagos",
                title="Verificados",
                value=str(verified),
                unit="comprobantes",
                description="Comprobantes verificados correctamente",
                icon="verified",
                order=3,
            ),
            LeadItem(
                id="pay_rejected",
                category="pagos",
                title="Rechazados",
                value=str(rejected),
                unit="comprobantes",
                description="Comprobantes rechazados",
                icon="cancel",
                order=4,
            ),
            LeadItem(
                id="pay_pending",
                category="pagos",
                title="Pendientes",
                value=str(pending),
                unit="comprobantes",
                description="Comprobantes en estado pendiente",
                icon="hourglass_empty",
                order=5,
            ),
            LeadItem(
                id="pay_verification_rate",
                category="pagos",
                title="Tasa de verificacion",
                value=f"{verification_rate}%",
                unit="%",
                description="Porcentaje de comprobantes verificados",
                icon="check_circle",
                order=6,
            ),
        ]
        return LeadCategory(id="pagos", name="Pagos", icon="payments", leads=leads)

    async def _compute_operacion(self) -> LeadCategory:
        # assignments
        total_assignments = await AssignmentDocument.count()
        active_assignments = await AssignmentDocument.find(
            {"is_active": True}
        ).count()
        # finalized assignments
        finalized = await AssignmentDocument.find(
            {"status": "final"}
        ).count()

        # assignment status breakdown
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
            {"Estado": assign_status_labels.get(s, s), "Cantidad": str(assign_counts.get(s, 0))}
            for s in sorted(assign_counts, key=assign_counts.get, reverse=True)
        ]

        # users
        total_users = await UserDocument.count()
        active_users = await UserDocument.find({"is_active": True}).count()

        leads = [
            LeadItem(
                id="op_asignaciones",
                category="operacion",
                title="Asignaciones activas",
                value=str(active_assignments),
                unit="asignaciones",
                description="Asignaciones activas de equinos a participantes",
                icon="link",
                order=1,
            ),
            LeadItem(
                id="op_asignaciones_total",
                category="operacion",
                title="Total asignaciones",
                value=str(total_assignments),
                unit="asignaciones",
                description="Todas las asignaciones registradas",
                icon="list_alt",
                order=2,
                details=assign_details,
            ),
            LeadItem(
                id="op_finalizadas",
                category="operacion",
                title="Asignaciones finalizadas",
                value=str(finalized),
                unit="asignaciones",
                description="Asignaciones marcadas como final",
                icon="flag",
                order=3,
            ),
            LeadItem(
                id="op_usuarios",
                category="operacion",
                title="Usuarios activos",
                value=str(active_users),
                unit="usuarios",
                description="Usuarios con cuenta activa en el sistema",
                icon="person",
                order=4,
            ),
            LeadItem(
                id="op_usuarios_total",
                category="operacion",
                title="Total usuarios",
                value=str(total_users),
                unit="usuarios",
                description="Todos los usuarios registrados",
                icon="group",
                order=5,
            ),
        ]
        return LeadCategory(
            id="operacion", name="Operacion", icon="settings", leads=leads
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
            all_leads = [
                lead for cat in response.categories for lead in cat.leads
            ]
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
