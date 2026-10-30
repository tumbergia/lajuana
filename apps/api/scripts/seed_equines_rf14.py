"""
Seed RF14: upsert equinos reales desde CVs.xlsx.

Uso:
    cd apps/api
    python -m app.seed_equines_rf14

Reglas:
    - match por inventory_number (primaria)
    - fallback por name normalizado
    - no inventar fechas
    - guardar birth_date_raw aunque sea no parseable
    - weight_kg/height_m vienen de Seguimiento Procesos → last_weight_at / last_height_at
    - si no existe dato, null
"""

from __future__ import annotations

import asyncio

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    PolicyDocument,
    ProviderDocument,
    ReservationDocument,
    SaddleDocument,
    ServiceLogDocument,
    UserDocument,
)

EQUINES_DATA = [
    {
        "inventory_number": 1,
        "name": "Juana",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Zaino",
        "registry_number": "ACC 242625-C GD",
        "microchip": "AVID*094*275*528",
        "approximate_birth_date": "2008-10-15",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Oct. 15 de 2008",
        "weight_kg": 350,
        "height_m": 1.42,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "sire_name": "Pegaso",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 6,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 2,
        "name": "Redentor",
        "species": "mule",
        "sex": "male",
        "breed": "Criolla",
        "coat_color": "Zaino",
        "registry_number": "CAB266104-CGD",
        "microchip": "AVID*012*328*552",
        "approximate_birth_date": "2012-04-06",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Abril 6 de 2012",
        "weight_kg": 370,
        "height_m": 1.46,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "sire_name": "Carolo",
        "dam_name": "Francisca",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 7,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 3,
        "name": "Chula",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Zaino",
        "weight_kg": 340,
        "height_m": 1.35,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 8,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 4,
        "name": "Cachirula",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Zaino",
        "weight_kg": 380,
        "height_m": 1.44,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Cundinamarca",
        "sire_name": "Cachirulo",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 9,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 5,
        "name": "Soñadora",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Colorado",
        "weight_kg": 345,
        "height_m": 1.36,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Aranzazu",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 10,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 6,
        "name": "Lucerito",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Bayo",
        "weight_kg": 310,
        "height_m": 1.32,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Valle",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 11,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 7,
        "name": "Napoleón",
        "species": "mule",
        "sex": "male",
        "breed": "Criolla",
        "coat_color": "Zaino",
        "weight_kg": 400,
        "height_m": 1.47,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "is_available": False,
        "operational_status": "restricted",
        "availability_notes": "No disponible para asignación según BD previa.",
        "availability_reasons": "status=restricted",
        "experience_fit": "not_assignable",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 12,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 8,
        "name": "Carbonero",
        "species": "mule",
        "sex": "male",
        "breed": "Criolla",
        "coat_color": "Negro",
        "weight_kg": 315,
        "height_m": 1.33,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 13,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 9,
        "name": "Gitana",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Castaña",
        "gait": "Fino",
        "registry_number": "ASD 283605-R GB",
        "microchip": "AVID*039*859*771",
        "approximate_birth_date": "2013-06-03",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Junio 3 de 2013",
        "weight_kg": 360,
        "height_m": 1.43,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Titiribí (Criadero La Suiza Mejía)",
        "sire_name": "Carolo",
        "dam_name": "NN",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 14,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 10,
        "name": "Linda",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Zaino",
        "approximate_birth_date": "2018-03-22",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Marzo 22 de 2018",
        "weight_kg": 260,
        "height_m": 1.35,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Manizales",
        "sire_name": "Burro (Jorge)",
        "dam_name": "Estrella",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 15,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 11,
        "name": "Almendra",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Zaino oscuro",
        "approximate_birth_date": "2009-10-10",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Octubre 10 de 2009",
        "weight_kg": 415,
        "height_m": 1.46,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Manizales (Vda. La Cabaña)",
        "sire_name": "Carolo",
        "dam_name": "Berenjena",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 16,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 12,
        "name": "Suzana",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Zaino claro",
        "gait": "Trocha",
        "approximate_birth_date": "2014-06-15",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Junio 15 de 2014",
        "weight_kg": 340,
        "height_m": 1.37,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Aranzazu",
        "sire_name": "Burro de Pensilvania de los Escobar, dueños de Acesco, la familia de Óscar Iván Zuluaga.",
        "dam_name": "Yegua trochadora, hija de Sobregiro (caballo FC)",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 17,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 13,
        "name": "Cosaco 24",
        "species": "donkey",
        "sex": "male",
        "breed": "Criolla",
        "coat_color": "Moro",
        "gait": "Fino",
        "registry_number": "ASD 282514-C GD",
        "microchip": "AVID*039*605*590",
        "approximate_birth_date": "2015-02-24",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Febrero 24 de 2015",
        "height_m": 1.36,
        "last_height_at": "2021-09-24",
        "birth_place": "Girardota (ANT) - Criadero Villa Luz",
        "sire_name": "Cosaco 26 de Villa Luz",
        "dam_name": "Luciana de Villa Luz",
        "is_available": False,
        "operational_status": "unavailable",
        "availability_notes": "No asignable a participante en operación turística; conservar como inventario equino.",
        "availability_reasons": "is_assignable=false;species_not_assignable_for_tourist",
        "experience_fit": "not_assignable",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 18,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 14,
        "name": "Julia",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Moro",
        "weight_kg": 290,
        "height_m": 1.32,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "ANT",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 19,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 15,
        "name": "Mimosa",
        "species": "horse",
        "sex": "female",
        "breed": "Criolla",
        "coat_color": "Alazán",
        "gait": "Fino",
        "registry_number": "ABA-293731",
        "microchip": "AVID-044-841-370",
        "approximate_birth_date": "2013-02-27",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Febrero 27 de 2013",
        "weight_kg": 400,
        "height_m": 1.45,
        "last_weight_at": "2021-09-24",
        "last_height_at": "2021-09-24",
        "birth_place": "Criadero JJV - Montejicar",
        "sire_name": "REX DE MONTEJICAR R: ABA 293661",
        "dam_name": "SARITA DE MONTEJICAR R: ABA-293707",
        "is_available": False,
        "operational_status": "unavailable",
        "availability_notes": "No asignable a participante en operación turística; conservar como inventario equino.",
        "availability_reasons": "is_assignable=false;species_not_assignable_for_tourist",
        "experience_fit": "not_assignable",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 20,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 16,
        "name": "Calandria",
        "species": "mule",
        "sex": "female",
        "breed": "Criolla x Lusitana",
        "coat_color": "Negro",
        "approximate_birth_date": "2020-01-09",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Enero 9 de 2020",
        "birth_place": "Quipile (Cundinamarca)",
        "sire_name": "Burro criollo",
        "dam_name": "Yegua Lusitana",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 21,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
    {
        "inventory_number": 17,
        "name": "Picasso",
        "species": "horse",
        "sex": "male",
        "breed": "Lusitana",
        "coat_color": "Moro",
        "approximate_birth_date": "2018-02-22",
        "birth_date_is_approximate": False,
        "birth_date_raw": "Febrero 22 de 2018",
        "birth_place": "Quipile (Cundinamarca)",
        "sire_name": "Dominguín (Lusitano)",
        "dam_name": "Yegua Lusitana",
        "is_available": False,
        "operational_status": "unavailable",
        "availability_notes": "No asignable a participante en operación turística; conservar como inventario equino.",
        "availability_reasons": "is_assignable=false;species_not_assignable_for_tourist",
        "experience_fit": "not_assignable",
        "source_file": "CVs.xlsx",
        "source_sheet": "Mulada LA JUANA",
        "source_row_number": 22,
        "source_updated_at_label": "Fecha actualización: Noviembre 9 de 2021",
    },
]


async def run_seed():
    client = AsyncMongoClient(settings.mongodb_uri)
    database = client[settings.mongodb_db_name]
    await init_beanie(
        database=database,
        document_models=[
            UserDocument,
            ExperienceDocument,
            ReservationDocument,
            ParticipantDocument,
            PaymentProofDocument,
            EquineDocument,
            SaddleDocument,
            AssignmentDocument,
            ServiceLogDocument,
            ProviderDocument,
            PolicyDocument,
        ],
    )

    # 1. Limpiar equinos viejos sin inventory_number (datos de seed_reproducible.py)
    deleted = await EquineDocument.find({"inventory_number": None}).delete()
    count = deleted.deleted_count if hasattr(deleted, "deleted_count") else 0
    print(f"  cleanup: {count} viejos sin inventory_number eliminados")

    upserted = 0
    skipped = 0

    for raw in EQUINES_DATA:
        name = raw.get("name", "")
        inv = raw.get("inventory_number")
        if not name or not inv:
            skipped += 1
            print("  [skipped] sin nombre/inventory_number")
            continue

        raw.setdefault("operational_status", "available")
        raw.setdefault("experience_fit", "all")
        raw.setdefault("workload_last_7_days", 0)

        existing = await EquineDocument.find_one(EquineDocument.inventory_number == inv)
        if existing:
            print(f"  [upsert] #{inv} {name}")
            for field, value in raw.items():
                setattr(existing, field, value)
            # Reset audit fields so Beanie defaults apply
            existing.version = 1
            await existing.save()
        else:
            print(f"  [insert] #{inv} {name}")
            doc = EquineDocument(**raw)
            await doc.insert()
        upserted += 1

    total = await EquineDocument.find_all().count()
    print(f"\n  Hecho: {upserted} equinos procesados - {total} en BD")
    await client.close()


if __name__ == "__main__":
    asyncio.run(run_seed())
