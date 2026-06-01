"""Seed QA idempotente para disponibilidad Q2 2026.

Crea 35 registros de schedule distribuidos entre el 15 de mayo y el 12 de julio
de 2026. Solo toca registros cuyo campo `notes` comience con el prefijo
[SEED_AVAILABILITY_2026_Q2].

Experiencias usadas y su slug (no crea ni modifica experiencias):

  EXP_MEDIO_DIA_ID     -> recorrido-medio-dia
  EXP_DIA_COMPLETO_ID  -> los-chorros
  EXP_AVISTAMIENTO_ID  -> recorrido-medio-dia  (variante comercial)
  EXP_AVANZADA_ID      -> montana-cristal
  EXP_PERSONALIZADA_ID -> los-chorros          (custom_request_only=true)

Uso:
    cd apps/api
    python -m app.seed_schedules_2026_q2
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from beanie import init_beanie
from bson import ObjectId
from pymongo import AsyncMongoClient

from app.common.enums import ScheduleStatus
from app.core.config import settings
from app.documents import ExperienceDocument, ScheduleDocument

SEED_PREFIX = "[SEED_AVAILABILITY_2026_Q2]"

EXP_MEDIO_DIA = "recorrido-medio-dia"
EXP_DIA_COMPLETO = "los-chorros"
EXP_AVISTAMIENTO = "recorrido-medio-dia"
EXP_AVANZADA = "montana-cristal"
EXP_PERSONALIZADA = "los-chorros"


@dataclass(frozen=True)
class SchedulePayload:
    experience_slug: str
    date_iso: str
    start_time: str
    is_active: bool
    capacity_total: int
    reserved_slots: int
    internal_slots: int
    blocked_slots: int
    custom_request_only: bool
    notes: str


def _build_payloads() -> list[SchedulePayload]:
    raw = [
        (
            "EXP_MEDIO_DIA_ID",
            "2026-05-15",
            "08:00:00",
            True,
            8,
            2,
            0,
            0,
            False,
            "Medio dia familiar - disponibilidad parcial cercana",
        ),
        (
            "EXP_DIA_COMPLETO_ID",
            "2026-05-16",
            "08:00:00",
            True,
            6,
            6,
            0,
            0,
            False,
            "Dia completo - lleno",
        ),
        (
            "EXP_AVISTAMIENTO_ID",
            "2026-05-17",
            "07:30:00",
            True,
            8,
            0,
            1,
            0,
            False,
            "Avistamiento/naturaleza - cupo interno operativo",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-05-20",
            "08:00:00",
            True,
            8,
            0,
            0,
            0,
            False,
            "Medio dia familiar - disponibilidad completa",
        ),
        (
            "EXP_AVISTAMIENTO_ID",
            "2026-05-22",
            "07:30:00",
            False,
            6,
            0,
            0,
            0,
            False,
            "Avistamiento/naturaleza - cerrado por clima",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-05-23",
            "08:00:00",
            True,
            8,
            4,
            0,
            1,
            False,
            "Medio dia familiar - bloqueo manual por contingencia",
        ),
        (
            "EXP_DIA_COMPLETO_ID",
            "2026-05-24",
            "08:00:00",
            True,
            6,
            2,
            1,
            0,
            False,
            "Dia completo - cupo de staff reservado",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-05-27",
            "08:00:00",
            True,
            8,
            0,
            0,
            0,
            False,
            "Medio dia familiar - miercoles tranquilo",
        ),
        (
            "EXP_PERSONALIZADA_ID",
            "2026-05-29",
            "09:00:00",
            True,
            4,
            0,
            0,
            0,
            True,
            "Personalizada - solo por solicitud",
        ),
        (
            "EXP_AVANZADA_ID",
            "2026-05-30",
            "07:00:00",
            True,
            6,
            1,
            1,
            0,
            False,
            "Ruta avanzada - cupo operativo reservado",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-05-31",
            "08:00:00",
            True,
            8,
            8,
            0,
            0,
            False,
            "Medio dia familiar - lleno",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-06-03",
            "08:00:00",
            True,
            8,
            1,
            0,
            0,
            False,
            "Medio dia familiar - baja ocupacion",
        ),
        (
            "EXP_AVISTAMIENTO_ID",
            "2026-06-05",
            "07:30:00",
            True,
            8,
            3,
            0,
            0,
            False,
            "Avistamiento/naturaleza - cupo medio",
        ),
        (
            "EXP_DIA_COMPLETO_ID",
            "2026-06-06",
            "08:00:00",
            True,
            8,
            5,
            0,
            1,
            False,
            "Dia completo - casi lleno con bloqueo",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-06-07",
            "08:00:00",
            True,
            8,
            0,
            1,
            0,
            False,
            "Medio dia familiar - cupo interno",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-06-10",
            "08:00:00",
            False,
            8,
            0,
            0,
            0,
            False,
            "Medio dia familiar - cerrado por mantenimiento de ruta",
        ),
        (
            "EXP_AVANZADA_ID",
            "2026-06-12",
            "07:00:00",
            True,
            6,
            4,
            0,
            0,
            False,
            "Ruta avanzada - disponibilidad baja",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-06-13",
            "08:00:00",
            True,
            8,
            6,
            0,
            0,
            False,
            "Medio dia familiar - solo quedan 2 cupos",
        ),
        (
            "EXP_DIA_COMPLETO_ID",
            "2026-06-14",
            "08:00:00",
            True,
            6,
            5,
            1,
            0,
            False,
            "Dia completo - lleno por cupo interno",
        ),
        (
            "EXP_AVISTAMIENTO_ID",
            "2026-06-17",
            "07:30:00",
            True,
            8,
            0,
            0,
            0,
            False,
            "Avistamiento/naturaleza - disponibilidad completa",
        ),
        (
            "EXP_PERSONALIZADA_ID",
            "2026-06-19",
            "09:00:00",
            True,
            4,
            1,
            0,
            0,
            True,
            "Personalizada - solicitud especial con ocupacion parcial",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-06-20",
            "08:00:00",
            True,
            8,
            7,
            0,
            0,
            False,
            "Medio dia familiar - ultimo cupo",
        ),
        (
            "EXP_DIA_COMPLETO_ID",
            "2026-06-21",
            "08:00:00",
            True,
            8,
            0,
            2,
            0,
            False,
            "Dia completo - dos cupos internos para operacion",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-06-24",
            "08:00:00",
            True,
            8,
            0,
            0,
            0,
            False,
            "Medio dia familiar - disponibilidad limpia",
        ),
        (
            "EXP_AVISTAMIENTO_ID",
            "2026-06-26",
            "07:30:00",
            True,
            6,
            6,
            0,
            0,
            False,
            "Avistamiento/naturaleza - lleno",
        ),
        (
            "EXP_AVANZADA_ID",
            "2026-06-27",
            "07:00:00",
            False,
            6,
            0,
            1,
            0,
            False,
            "Ruta avanzada - cerrada por revision de seguridad",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-06-28",
            "08:00:00",
            True,
            8,
            2,
            0,
            2,
            False,
            "Medio dia familiar - bloqueo por contingencia",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-07-01",
            "08:00:00",
            True,
            8,
            0,
            0,
            0,
            False,
            "Medio dia familiar - inicio de julio",
        ),
        (
            "EXP_AVISTAMIENTO_ID",
            "2026-07-03",
            "07:30:00",
            True,
            8,
            1,
            0,
            0,
            False,
            "Avistamiento/naturaleza - baja ocupacion",
        ),
        (
            "EXP_DIA_COMPLETO_ID",
            "2026-07-04",
            "08:00:00",
            True,
            8,
            4,
            1,
            1,
            False,
            "Dia completo - ocupacion media con operacion interna",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-07-05",
            "08:00:00",
            True,
            8,
            0,
            0,
            0,
            False,
            "Medio dia familiar - domingo libre",
        ),
        (
            "EXP_MEDIO_DIA_ID",
            "2026-07-08",
            "08:00:00",
            True,
            8,
            5,
            0,
            0,
            False,
            "Medio dia familiar - quedan 3 cupos",
        ),
        (
            "EXP_PERSONALIZADA_ID",
            "2026-07-10",
            "09:00:00",
            True,
            4,
            0,
            0,
            0,
            True,
            "Personalizada - solo por solicitud futura",
        ),
        (
            "EXP_AVANZADA_ID",
            "2026-07-11",
            "07:00:00",
            True,
            6,
            6,
            0,
            0,
            False,
            "Ruta avanzada - llena",
        ),
        (
            "EXP_DIA_COMPLETO_ID",
            "2026-07-12",
            "08:00:00",
            True,
            8,
            2,
            0,
            0,
            False,
            "Dia completo - disponibilidad amplia",
        ),
    ]
    slug_map = {
        "EXP_MEDIO_DIA_ID": EXP_MEDIO_DIA,
        "EXP_DIA_COMPLETO_ID": EXP_DIA_COMPLETO,
        "EXP_AVISTAMIENTO_ID": EXP_AVISTAMIENTO,
        "EXP_AVANZADA_ID": EXP_AVANZADA,
        "EXP_PERSONALIZADA_ID": EXP_PERSONALIZADA,
    }
    payloads: list[SchedulePayload] = []
    for (
        placeholder,
        date_iso,
        start_time,
        is_active,
        capacity_total,
        reserved_slots,
        internal_slots,
        blocked_slots,
        custom_request_only,
        desc,
    ) in raw:
        slug = slug_map[placeholder]
        notes = f"{SEED_PREFIX} {desc}"
        payloads.append(
            SchedulePayload(
                experience_slug=slug,
                date_iso=date_iso,
                start_time=start_time,
                is_active=is_active,
                capacity_total=capacity_total,
                reserved_slots=reserved_slots,
                internal_slots=internal_slots,
                blocked_slots=blocked_slots,
                custom_request_only=custom_request_only,
                notes=notes,
            )
        )
    return payloads


def _compute_available_slots(
    capacity_total: int,
    reserved_slots: int,
    blocked_slots: int,
    internal_slots: int,
) -> int:
    available = capacity_total - reserved_slots - blocked_slots - internal_slots
    if available < 0:
        raise ValueError(f"available_slots negativo: {available}")
    return available


def _derive_status(is_active: bool, available_slots: int) -> str:
    if not is_active:
        return ScheduleStatus.CLOSED.value
    return ScheduleStatus.FULL.value if available_slots == 0 else ScheduleStatus.OPEN.value


async def run_seed() -> None:
    client = AsyncMongoClient(settings.mongodb_uri)
    database = client[settings.mongodb_db_name]

    await init_beanie(
        database=database,
        document_models=[
            ExperienceDocument,
            ScheduleDocument,
        ],
    )

    collection = ScheduleDocument.get_motor_collection()
    deleted = await collection.delete_many({"notes": {"$regex": f"^{SEED_PREFIX}"}})
    print(f"Limpieza: {deleted} registros eliminados con prefijo {SEED_PREFIX}")

    experiences = await ExperienceDocument.find_all().to_list()
    experiences_by_slug: dict[str, ExperienceDocument] = {}
    for exp in experiences:
        experiences_by_slug[exp.slug] = exp

    missing = []
    for slug in {
        EXP_MEDIO_DIA,
        EXP_DIA_COMPLETO,
        EXP_AVANZADA,
        EXP_PERSONALIZADA,
        EXP_AVISTAMIENTO,
    }:
        if slug not in experiences_by_slug:
            missing.append(slug)
    if missing:
        print(f"ERROR: Experiencias no encontradas: {missing}")
        print("Ejecuta primero el seed principal: python -m app.seed_reproducible")
        await client.close()
        return

    payloads = _build_payloads()
    inserted_count = 0
    errors: list[str] = []

    for item in payloads:
        exp = experiences_by_slug[item.experience_slug]
        try:
            available_slots = _compute_available_slots(
                capacity_total=item.capacity_total,
                reserved_slots=item.reserved_slots,
                blocked_slots=item.blocked_slots,
                internal_slots=item.internal_slots,
            )
            status = _derive_status(is_active=item.is_active, available_slots=available_slots)
            day = date.fromisoformat(item.date_iso)
            raw = {
                "_id": ObjectId(),
                "experience_id": exp.id,
                "date": datetime.combine(day, time.min, tzinfo=UTC),
                "start_time": item.start_time,
                "is_active": item.is_active,
                "capacity_total": item.capacity_total,
                "reserved_slots": item.reserved_slots,
                "internal_slots": item.internal_slots,
                "blocked_slots": item.blocked_slots,
                "available_slots": available_slots,
                "status": status,
                "custom_request_only": item.custom_request_only,
                "notes": item.notes,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
            await collection.insert_one(raw)
            inserted_count += 1
        except Exception as e:
            errors.append(f"{item.date_iso} / {item.experience_slug}: {e}")

    print(f"Insertados: {inserted_count} de {len(payloads)}")
    if errors:
        print(f"Errores ({len(errors)}):")
        for err in errors[:5]:
            print(f"  - {err}")
        if len(errors) > 5:
            print(f"  ... y {len(errors) - 5} mas")

    print()
    print("=" * 60)
    print("VALIDACIONES POST-SEED")
    print("=" * 60)
    await _run_validations(experiences_by_slug)
    print("=" * 60)

    await client.close()


async def _run_validations(
    experiences_by_slug: dict[str, ExperienceDocument],
) -> None:
    validation_results: list[tuple[str, str, str, str]] = []

    async def find_schedule(slug: str, date_iso: str) -> ScheduleDocument | None:
        exp = experiences_by_slug.get(slug)
        if exp is None:
            return None
        return await ScheduleDocument.find_one(
            {"experience_id": exp.id, "date": date.fromisoformat(date_iso)},
        )

    # 1) check_experience_availability medio dia, 2026-06-24, 4 personas -> available=true
    doc_1 = await find_schedule(EXP_MEDIO_DIA, "2026-06-24")
    if doc_1 is not None:
        ok = doc_1.status.value == "open" and doc_1.available_slots >= 4
        validation_results.append(
            (
                "1",
                "medio dia 2026-06-24, 4p -> available=true",
                "PASS" if ok else "FAIL",
                f"status={doc_1.status.value}, available={doc_1.available_slots}",
            )
        )
    else:
        validation_results.append(
            ("1", "medio dia 2026-06-24, 4p -> available=true", "FAIL", "schedule not found")
        )

    # 2) check_experience_availability medio dia, 2026-06-13, 4 personas -> available=false
    doc_2 = await find_schedule(EXP_MEDIO_DIA, "2026-06-13")
    if doc_2 is not None:
        ok = doc_2.available_slots < 4
        validation_results.append(
            (
                "2",
                "medio dia 2026-06-13, 4p -> available=false",
                "PASS" if ok else "FAIL",
                f"status={doc_2.status.value}, available={doc_2.available_slots}",
            )
        )
    else:
        validation_results.append(
            ("2", "medio dia 2026-06-13, 4p -> available=false", "FAIL", "schedule not found")
        )

    # 3) check_experience_availability medio dia, 2026-06-20, 1 persona -> available=true
    doc_3 = await find_schedule(EXP_MEDIO_DIA, "2026-06-20")
    if doc_3 is not None:
        ok = doc_3.status.value == "open" and doc_3.available_slots >= 1
        validation_results.append(
            (
                "3",
                "medio dia 2026-06-20, 1p -> available=true",
                "PASS" if ok else "FAIL",
                f"status={doc_3.status.value}, available={doc_3.available_slots}",
            )
        )
    else:
        validation_results.append(
            ("3", "medio dia 2026-06-20, 1p -> available=true", "FAIL", "schedule not found")
        )

    # 4) check_experience_availability medio dia, 2026-06-20, 2 personas -> available=false
    if doc_3 is not None:
        ok = doc_3.available_slots < 2
        validation_results.append(
            (
                "4",
                "medio dia 2026-06-20, 2p -> available=false",
                "PASS" if ok else "FAIL",
                f"available={doc_3.available_slots}",
            )
        )
    else:
        validation_results.append(
            ("4", "medio dia 2026-06-20, 2p -> available=false", "FAIL", "schedule not found")
        )

    # 5) check_experience_availability dia completo, 2026-06-14, 1 persona -> available=false (full)
    doc_5 = await find_schedule(EXP_DIA_COMPLETO, "2026-06-14")
    if doc_5 is not None:
        ok = doc_5.status.value == "full" or doc_5.available_slots < 1
        validation_results.append(
            (
                "5",
                "dia completo 2026-06-14, 1p -> available=false (full)",
                "PASS" if ok else "FAIL",
                f"status={doc_5.status.value}, available={doc_5.available_slots}",
            )
        )
    else:
        validation_results.append(
            (
                "5",
                "dia completo 2026-06-14, 1p -> available=false (full)",
                "FAIL",
                "schedule not found",
            )
        )

    # 6) check_experience_availability medio dia, 2026-06-10, 1 persona -> available=false (closed)
    doc_6 = await find_schedule(EXP_MEDIO_DIA, "2026-06-10")
    if doc_6 is not None:
        ok = not doc_6.is_active or doc_6.status.value == "closed"
        validation_results.append(
            (
                "6",
                "medio dia 2026-06-10, 1p -> available=false (closed)",
                "PASS" if ok else "FAIL",
                f"is_active={doc_6.is_active}, status={doc_6.status.value}",
            )
        )
    else:
        validation_results.append(
            (
                "6",
                "medio dia 2026-06-10, 1p -> available=false (closed)",
                "FAIL",
                "schedule not found",
            )
        )

    # 7) check_experience_availability medio dia, 2026-06-25, 1 persona -> available=false (schedule.not_found)
    doc_7 = await find_schedule(EXP_MEDIO_DIA, "2026-06-25")
    ok_7 = doc_7 is None
    validation_results.append(
        (
            "7",
            "medio dia 2026-06-25, 1p -> available=false (schedule.not_found)",
            "PASS" if ok_7 else "FAIL",
            "schedule found (unexpected)" if doc_7 else "not found (expected)",
        )
    )

    # 8) list schedules date_from=2026-06-01 date_to=2026-06-30 status=open
    exp_medio = experiences_by_slug.get(EXP_MEDIO_DIA)
    if exp_medio:
        open_docs = await ScheduleDocument.find(
            {"experience_id": exp_medio.id, "date": {"$gte": date.fromisoformat("2026-06-01"), "$lte": date.fromisoformat("2026-06-30")}},
        ).to_list()
        open_docs_filtered = [d for d in open_docs if d.status == ScheduleStatus.OPEN]
        open_count = len(open_docs_filtered)
        validation_results.append(
            (
                "8",
                "list schedules junio, status=open",
                "PASS" if open_count >= 3 else "FAIL",
                f"open count={open_count} (expected >=3)",
            )
        )
    else:
        validation_results.append(
            ("8", "list schedules junio, status=open", "FAIL", "experience not found")
        )

    # 9) list_available_schedules medio dia, participant_count=4, rango junio
    if exp_medio:
        available_4 = (
            await ScheduleDocument.find(
                {"experience_id": exp_medio.id, "date": {"$gte": date.fromisoformat("2026-06-01"), "$lte": date.fromisoformat("2026-06-30")}, "status": ScheduleStatus.OPEN, "available_slots": {"$gte": 4}},
            )
            .sort(("date", 1))
            .to_list()
        )
        cnt = len(available_4)
        excludes_wrong = all(
            d.date.isoformat() not in {"2026-06-13", "2026-06-20"} for d in available_4
        )
        validation_results.append(
            (
                "9",
                "list_available_schedules medio dia, 4p, junio",
                "PASS" if excludes_wrong and cnt >= 2 else "FAIL",
                f"count={cnt}, excludes_13_20={excludes_wrong}",
            )
        )
    else:
        validation_results.append(
            ("9", "list_available_schedules medio dia, 4p, junio", "FAIL", "experience not found")
        )

    # 10) suggest_alternative_dates medio dia, requested_date=2026-06-20, participant_count=4
    if exp_medio:
        suggested = (
            await ScheduleDocument.find(
                {"experience_id": exp_medio.id, "date": {"$gte": date.fromisoformat("2026-06-20"), "$lte": date.fromisoformat("2026-07-05")}, "status": ScheduleStatus.OPEN, "available_slots": {"$gte": 4}},
            )
            .sort(("date", 1))
            .limit(5)
            .to_list()
        )
        sug_dates = [d.date.isoformat() for d in suggested]
        has_0624 = "2026-06-24" in sug_dates
        has_0628 = "2026-06-28" in sug_dates
        validation_results.append(
            (
                "10",
                "suggest_alternative_dates medio dia, cerca 2026-06-20",
                "PASS" if has_0624 or has_0628 else "FAIL",
                f"dates={sug_dates}" if sug_dates else "no alternatives found",
            )
        )
    else:
        validation_results.append(
            (
                "10",
                "suggest_alternative_dates medio dia, cerca 2026-06-20",
                "FAIL",
                "experience not found",
            )
        )

    print(f"{'':>3}  {'Caso':<60} {'Resultado':<8} Detalle")
    print("-" * 100)
    for num, label, result, detail in validation_results:
        print(f"{num:>3}  {label:<60} {result:<8} {detail}")

    total = len(validation_results)
    passed = sum(1 for _, _, r, _ in validation_results if r == "PASS")
    failed = total - passed
    print(f"\nTotal: {total}  |  PASS: {passed}  |  FAIL: {failed}")
    if failed > 0:
        print(f"! {failed} validaciones fallaron.")


if __name__ == "__main__":
    asyncio.run(run_seed())
