"""Crea datos de prueba y genera un link de formulario funcional.

Uso:
    cd apps/api
    python -m app.seed_form_test
"""

import asyncio
from datetime import UTC, date, datetime, timedelta

from beanie import init_beanie
from bson import ObjectId
from pymongo import AsyncMongoClient

from app.common.enums import (
    Channel,
    ExperienceLevel,
    ExperienceStatus,
    PaymentStatus,
    ReservationStatus,
)
from app.core.config import settings
from app.documents import (
    AppConfigDocument,
    ExperienceDocument,
    ParticipantFormLinkDocument,
    PaymentProofDocument,
    ReservationDocument,
)
from app.services.participant_form_link_service import ParticipantFormLinkService


async def main():
    client = AsyncMongoClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    for col in [
        "app_config",
        "experiences",
        "reservations",
        "participant_form_links",
        "participants",
        "payment_proofs",
    ]:
        await db[col].delete_many({})

    await init_beanie(
        database=db,
        document_models=[
            AppConfigDocument,
            ExperienceDocument,
            ParticipantFormLinkDocument,
            PaymentProofDocument,
            ReservationDocument,
        ],
    )

    await db["app_config"].insert_one(
        {
            "key": "reservation_rules",
            "reservation_rules": {
                "min_days_in_advance": 0,
                "require_payment_proof_for_confirmation": False,
            },
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    )
    print("Config OK")

    exp_id = ObjectId()
    await db["experiences"].insert_one(
        {
            "_id": exp_id,
            "name": "Cabalgata Básica",
            "slug": "cabalgata-basica",
            "subtitle": "Media jornada",
            "description": "Paseo a caballo de medio día",
            "level": ExperienceLevel.BASIC.value,
            "difficulty": "basic",
            "category": "route",
            "status": ExperienceStatus.PUBLISHED.value,
            "duration_hours": 4,
            "duration_days": 0,
            "duration": {"activity_minutes": 240, "route_minutes": 30, "display_text": "4 horas"},
            "base_capacity": 10,
            "standard_max_participants": 10,
            "min_participants": 1,
            "is_active": True,
            "pricing": {
                "currency": "COP",
                "prices_are_net": True,
                "tiers": [
                    {"min_participants": 1, "max_participants": 10, "price_per_person": 120000}
                ],
            },
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    )
    print(f"Experiencia OK: {exp_id}")

    future_date = date.today() + timedelta(days=7)
    resv_id = ObjectId()
    await db["reservations"].insert_one(
        {
            "_id": resv_id,
            "code": f"RES-{datetime.now(UTC).strftime('%Y%m%d')}-TEST",
            "experience_id": exp_id,
            "requested_date": datetime.combine(future_date, datetime.min.time()),
            "channel": Channel.WHATSAPP.value,
            "status": ReservationStatus.PAYMENT_RECEIVED.value,
            "holder_name": "Cliente Test",
            "holder_phone": "573001234567",
            "participant_count": 2,
            "payment_status": PaymentStatus.RECEIVED.value,
            "currency": "COP",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
    )
    print(f"Reserva OK: {resv_id} | código: RES-TEST")

    await db["reservations"].update_one(
        {"_id": resv_id},
        {
            "$set": {
                "status": ReservationStatus.CONFIRMED.value,
                "confirmed_at": datetime.now(UTC),
                "blocks_day": True,
                "availability_lock_key": future_date.isoformat(),
            }
        },
    )

    form_svc = ParticipantFormLinkService()
    doc, raw_token = await form_svc.generate(
        reservation_id=str(resv_id),
        expected_participants_count=2,
    )

    form_url = f"{settings.participant_form_base_url}/?token={raw_token}"
    print(f"\n>>> LINK DEL FORMULARIO: {form_url} <<<")
    print(">>> Ábrelo en el navegador para probarlo <<<")

    await client.close()


asyncio.run(main())
