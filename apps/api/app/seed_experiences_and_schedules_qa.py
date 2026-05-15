"""Seed QA de experiences y schedules para pruebas de disponibilidad, cotizacin y alternativas de fecha.

Uso:
    cd apps/api
    python -m app.seed_experiences_and_schedules_qa
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from beanie import init_beanie
from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError

from app.common.enums import (
    ExperienceDifficulty,
    ExperienceLevel,
    ScheduleStatus,
)
from app.core.config import settings
from app.documents import (
    ExperienceDocument,
    ScheduleDocument,
)
from app.documents.experience_document import (
    ExperiencePricingData,
    ExperiencePricingTierData,
)

# ---------------------------------------------------------------------------
#  Experience definitions (3 obligatorias)
# ---------------------------------------------------------------------------
EXPERIENCE_DEFS = [
    {
        "name": "Recorrido de medio da",
        "slug": "recorrido-medio-dia",
        "subtitle": "Paseo en mula, naturaleza y cultura cafetera",
        "description": (
            "Experiencia familiar de medio da en mula, "
            "naturaleza y cultura rural."
        ),
        "level": ExperienceLevel.BASIC,
        "difficulty": ExperienceDifficulty.BASIC,
        "duration_hours": 4,
        "base_capacity": 8,
        "standard_max_participants": 8,
        "min_participants": 1,
        "tags": [
            "familiar",
            "naturaleza",
            "cultura cafetera",
            "principiantes",
        ],
        "aliases": [
            "medio da",
            "medio dia",
            "recorrido medio da",
            "recorrido medio dia",
            "recorrido de medio da",
            "recorrido de medio dia",
            "experiencia corta",
            "plan corto",
            "paseo corto",
            "paseo cafe",
            "cafe",
            "cafe",
            "medio da familiar",
            "avistamiento",
        ],
        "is_active": True,
        "pricing": ExperiencePricingData(
            tiers=[
                ExperiencePricingTierData(
                    min_participants=1, max_participants=1, price_per_person=150000,
                ),
                ExperiencePricingTierData(
                    min_participants=2, max_participants=2, price_per_person=130000,
                ),
                ExperiencePricingTierData(
                    min_participants=3, max_participants=4, price_per_person=120000,
                ),
                ExperiencePricingTierData(
                    min_participants=5, max_participants=8, price_per_person=100000,
                ),
            ],
        ),
    },
    {
        "name": "Los Chorros",
        "slug": "los-chorros",
        "subtitle": "Da completo de naturaleza y cultura rural",
        "description": (
            "Experiencia de da completo orientada a naturaleza, "
            "recorrido rural y alimentacin tradicional."
        ),
        "level": ExperienceLevel.INTERMEDIATE,
        "difficulty": ExperienceDifficulty.INTERMEDIATE,
        "duration_hours": 8,
        "base_capacity": 8,
        "standard_max_participants": 8,
        "min_participants": 1,
        "tags": [
            "da completo",
            "naturaleza",
            "cultura cafetera",
            "alimentacin tradicional",
        ],
        "aliases": [
            "chorros",
            "los chorros",
            "recorrido los chorros",
            "ruta los chorros",
            "un da",
            "un dia",
            "da completo",
            "dia completo",
            "paseo de un da",
            "paseo de un dia",
        ],
        "is_active": True,
        "pricing": ExperiencePricingData(
            tiers=[
                ExperiencePricingTierData(
                    min_participants=1, max_participants=1, price_per_person=220000,
                ),
                ExperiencePricingTierData(
                    min_participants=2, max_participants=2, price_per_person=200000,
                ),
                ExperiencePricingTierData(
                    min_participants=3, max_participants=4, price_per_person=180000,
                ),
                ExperiencePricingTierData(
                    min_participants=5, max_participants=8, price_per_person=160000,
                ),
            ],
        ),
    },
    {
        "name": "La Montana de Cristal",
        "slug": "montana-cristal",
        "subtitle": "Ruta avanzada de montaa",
        "description": (
            "Ruta avanzada para usuarios con mejor condicin fsica "
            "y mayor tolerancia a recorrido rural."
        ),
        "level": ExperienceLevel.ADVANCED,
        "difficulty": ExperienceDifficulty.ADVANCED,
        "duration_hours": 8,
        "base_capacity": 6,
        "standard_max_participants": 6,
        "min_participants": 1,
        "tags": [
            "avanzada",
            "montaa",
            "naturaleza",
            "experiencia intensa",
        ],
        "aliases": [
            "montaa cristal",
            "montana cristal",
            "cristal",
            "ruta montaa",
            "ruta montana",
        ],
        "is_active": True,
        "pricing": ExperiencePricingData(
            tiers=[
                ExperiencePricingTierData(
                    min_participants=1, max_participants=1, price_per_person=300000,
                ),
                ExperiencePricingTierData(
                    min_participants=2, max_participants=2, price_per_person=280000,
                ),
                ExperiencePricingTierData(
                    min_participants=3, max_participants=4, price_per_person=250000,
                ),
                ExperiencePricingTierData(
                    min_participants=5, max_participants=6, price_per_person=220000,
                ),
            ],
        ),
    },
]

# ---------------------------------------------------------------------------
#  Schedule definitions (35 registros QA)
# ---------------------------------------------------------------------------
@dataclass
class _ScheduleSeed:
    slug: str
    date_iso: str
    time_iso: str
    capacity: int
    reserved: int
    internal: int
    blocked: int
    is_active: bool
    custom: bool
    notes: str


SCHEDULE_DEFS: list[_ScheduleSeed] = [
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-05-15", "08:00:00",
        8, 2, 0, 0, True, False,
        "Medio da familiar - disponibilidad parcial cercana",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-05-16", "08:00:00",
        6, 6, 0, 0, True, False,
        "Da completo - lleno",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-05-17", "07:30:00",
        8, 0, 1, 0, True, False,
        "Avistamiento/naturaleza - cupo interno operativo",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-05-20", "08:00:00",
        8, 0, 0, 0, True, False,
        "Medio da familiar - disponibilidad completa",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-05-22", "07:30:00",
        6, 0, 0, 0, False, False,
        "Avistamiento/naturaleza - cerrado por clima",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-05-23", "08:00:00",
        8, 4, 0, 1, True, False,
        "Medio da familiar - bloqueo manual por contingencia",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-05-24", "08:00:00",
        6, 2, 1, 0, True, False,
        "Da completo - cupo de staff reservado",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-05-27", "08:00:00",
        8, 0, 0, 0, True, False,
        "Medio da familiar - mircoles tranquilo",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-05-29", "09:00:00",
        4, 0, 0, 0, True, True,
        "Personalizada - solo por solicitud",
    ),
    _ScheduleSeed(
        "montana-cristal", "2026-05-30", "07:00:00",
        6, 1, 1, 0, True, False,
        "Ruta avanzada - cupo operativo reservado",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-05-31", "08:00:00",
        8, 8, 0, 0, True, False,
        "Medio da familiar - lleno",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-03", "08:00:00",
        8, 1, 0, 0, True, False,
        "Medio da familiar - baja ocupacin",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-05", "07:30:00",
        8, 3, 0, 0, True, False,
        "Avistamiento/naturaleza - cupo medio",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-06-06", "08:00:00",
        8, 5, 0, 1, True, False,
        "Da completo - casi lleno con bloqueo",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-07", "08:00:00",
        8, 0, 1, 0, True, False,
        "Medio da familiar - cupo interno",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-10", "08:00:00",
        8, 0, 0, 0, False, False,
        "Medio da familiar - cerrado por mantenimiento de ruta",
    ),
    _ScheduleSeed(
        "montana-cristal", "2026-06-12", "07:00:00",
        6, 4, 0, 0, True, False,
        "Ruta avanzada - disponibilidad baja",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-13", "08:00:00",
        8, 6, 0, 0, True, False,
        "Medio da familiar - solo quedan 2 cupos",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-06-14", "08:00:00",
        6, 5, 1, 0, True, False,
        "Da completo - lleno por cupo interno",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-17", "07:30:00",
        8, 0, 0, 0, True, False,
        "Avistamiento/naturaleza - disponibilidad completa",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-06-19", "09:00:00",
        4, 1, 0, 0, True, True,
        "Personalizada - solicitud especial con ocupacin parcial",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-20", "08:00:00",
        8, 7, 0, 0, True, False,
        "Medio da familiar - ltimo cupo",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-06-21", "08:00:00",
        8, 0, 2, 0, True, False,
        "Da completo - dos cupos internos para operacin",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-24", "08:00:00",
        8, 0, 0, 0, True, False,
        "Medio da familiar - disponibilidad limpia",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-26", "07:30:00",
        6, 6, 0, 0, True, False,
        "Avistamiento/naturaleza - lleno",
    ),
    _ScheduleSeed(
        "montana-cristal", "2026-06-27", "07:00:00",
        6, 0, 1, 0, False, False,
        "Ruta avanzada - cerrada por revisin de seguridad",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-06-28", "08:00:00",
        8, 2, 0, 2, True, False,
        "Medio da familiar - bloqueo por contingencia",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-07-01", "08:00:00",
        8, 0, 0, 0, True, False,
        "Medio da familiar - inicio de julio",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-07-03", "07:30:00",
        8, 1, 0, 0, True, False,
        "Avistamiento/naturaleza - baja ocupacin",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-07-04", "08:00:00",
        8, 4, 1, 1, True, False,
        "Da completo - ocupacin media con operacin interna",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-07-05", "08:00:00",
        8, 0, 0, 0, True, False,
        "Medio da familiar - domingo libre",
    ),
    _ScheduleSeed(
        "recorrido-medio-dia", "2026-07-08", "08:00:00",
        8, 5, 0, 0, True, False,
        "Medio da familiar - quedan 3 cupos",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-07-10", "09:00:00",
        4, 0, 0, 0, True, True,
        "Personalizada - solo por solicitud futura",
    ),
    _ScheduleSeed(
        "montana-cristal", "2026-07-11", "07:00:00",
        6, 6, 0, 0, True, False,
        "Ruta avanzada - llena",
    ),
    _ScheduleSeed(
        "los-chorros", "2026-07-12", "08:00:00",
        8, 2, 0, 0, True, False,
        "Da completo - disponibilidad amplia",
    ),
]


async def _upsert_experience(data: dict) -> tuple[str, ExperienceDocument]:
    slug = data["slug"]
    existing = await ExperienceDocument.find_one(
        ExperienceDocument.slug == slug
    )
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.now(UTC)
        await existing.save()
        return "updated", existing
    doc = ExperienceDocument(**data)
    await doc.insert()
    return "created", doc


def _compute_avail_and_status(
    capacity: int,
    reserved: int,
    internal: int,
    blocked: int,
    is_active: bool,
) -> tuple[int, ScheduleStatus]:
    avail = capacity - reserved - internal - blocked
    if avail < 0:
        avail = 0
    if not is_active:
        return avail, ScheduleStatus.CLOSED
    if avail == 0:
        return avail, ScheduleStatus.FULL
    return avail, ScheduleStatus.OPEN


async def run() -> None:
    client = AsyncMongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    await init_beanie(
        database=db,
        document_models=[ExperienceDocument, ScheduleDocument],
    )

    exp_created = 0
    exp_updated = 0
    sched_inserted = 0
    sched_failed = 0
    slug_errors: list[str] = []

    # -- 1. Upsert experiences --
    for exp_data in EXPERIENCE_DEFS:
        action, _ = await _upsert_experience(exp_data)
        if action == "created":
            exp_created += 1
        else:
            exp_updated += 1

    # -- 2. Fetch experience ids by slug --
    required_slugs = {s.slug for s in SCHEDULE_DEFS}
    exp_by_slug: dict[str, ExperienceDocument] = {}
    for slug in required_slugs:
        doc = await ExperienceDocument.find_one(
            ExperienceDocument.slug == slug
        )
        if doc is None:
            slug_errors.append(slug)
        else:
            exp_by_slug[slug] = doc

    # -- 3. Insert schedules (via motor collection, same pattern as seed_reproducible) --
    collection = ScheduleDocument.get_motor_collection()
    for s in SCHEDULE_DEFS:
        if s.slug in slug_errors:
            sched_failed += 1
            continue

        exp_id = exp_by_slug[s.slug].id
        day_dt = datetime.combine(
            date.fromisoformat(s.date_iso), time.min, tzinfo=UTC,
        )
        avail, status = _compute_avail_and_status(
            s.capacity, s.reserved, s.internal, s.blocked, s.is_active,
        )

        raw = {
            "experience_id": exp_id,
            "date": day_dt,
            "start_time": s.time_iso,
            "is_active": s.is_active,
            "capacity_total": s.capacity,
            "reserved_slots": s.reserved,
            "internal_slots": s.internal,
            "blocked_slots": s.blocked,
            "available_slots": avail,
            "status": status.value,
            "custom_request_only": s.custom,
            "notes": s.notes,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        try:
            await collection.insert_one(raw)
            sched_inserted += 1
        except DuplicateKeyError:
            sched_failed += 1
        except Exception as exc:
            print(f"  ERROR insertando schedule {s.slug} {s.date_iso}: {exc!r}")
            sched_failed += 1

    await client.close()

    # -- 4. Summary --
    print(f"experiencias creadas: {exp_created}")
    print(f"experiencias actualizadas: {exp_updated}")
    print(f"schedules insertados: {sched_inserted}")
    print(f"schedules fallidos: {sched_failed}")
    if slug_errors:
        print(f"errores por slug no encontrado: {slug_errors}")
    print(
        f"total final de schedules insertados por este script: "
        f"{sched_inserted}"
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
