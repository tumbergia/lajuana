from __future__ import annotations

from datetime import UTC, datetime

from app.common.collections import Collections
from app.core.config import settings
from app.migrations.base import Migration
from app.migrations.seed_notification_templates import SEED_TEMPLATES


class ConfigureLaJuanaSettingsMigration(Migration):
    def __init__(self) -> None:
        super().__init__(
            version="005",
            name="configure_lajuana_settings",
            description="Seed payment/location/AI settings and dynamic location templates",
        )

    async def apply(self) -> None:
        from app.core.db import db

        if db.client is None:
            raise RuntimeError("Database not initialized")
        database = db.client[settings.mongodb_db_name]
        configs = database[Collections.APP_CONFIG]
        now = datetime.now(UTC)
        await configs.update_one(
            {"key": "payment_instructions"},
            {
                "$setOnInsert": {
                    "key": "payment_instructions",
                    "payment_instructions": {
                        "manual_transfer_enabled": True,
                        "account_bank": "Bancolombia",
                        "account_type": "Ahorros",
                        "account_number": "7165 1544 758",
                        "account_holder_name": "Jairo Ramírez Londoño",
                        "account_holder_id": "C.C. No. 10.288.647",
                        "transfer_note": "Envía el comprobante con el código de pre-reserva.",
                        "bold_enabled": False,
                        "bold_checkout_url": None,
                        "bold_surcharge_percent": 7,
                        "bold_note": "El pago por Bold tiene una comisión adicional.",
                    },
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
            },
            upsert=True,
        )
        await configs.update_one(
            {
                "key": "payment_instructions",
                "$or": [
                    {"payment_instructions.account_number": "00000000000"},
                    {"payment_instructions.account_number": {"$exists": False}},
                ],
            },
            {
                "$set": {
                    "payment_instructions.manual_transfer_enabled": True,
                    "payment_instructions.account_bank": "Bancolombia",
                    "payment_instructions.account_type": "Ahorros",
                    "payment_instructions.account_number": "7165 1544 758",
                    "payment_instructions.account_holder_name": "Jairo Ramírez Londoño",
                    "payment_instructions.account_holder_id": "C.C. No. 10.288.647",
                    "payment_instructions.bold_enabled": False,
                    "payment_instructions.bold_surcharge_percent": 7,
                    "updated_at": now,
                }
            },
        )
        await configs.update_one(
            {"key": "business_location"},
            {
                "$setOnInsert": {
                    "key": "business_location",
                    "business_location": {
                        "name": "La Juana",
                        "address": "Ruta de la Arriería, vía a Salamina",
                        "municipality": "Manizales, Caldas",
                        "directions": (
                            "A 30 minutos al norte de Manizales. En el km 16 toma "
                            "el desvío hacia las ruinas de la antigua fábrica de Cementos Caldas."
                        ),
                        "latitude": 5.152583,
                        "longitude": -75.501472,
                    },
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
            },
            upsert=True,
        )
        await configs.update_one(
            {"key": "ai_configuration"},
            {
                "$setOnInsert": {
                    "key": "ai_configuration",
                    "ai_configuration": {
                        "enabled": False,
                        "routes": [{"position": i} for i in range(1, 4)],
                    },
                    "version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
            },
            upsert=True,
        )
        seen_keys: set[str] = set()
        async for document in configs.find({}, {"key": 1}).sort("updated_at", -1):
            key = document.get("key")
            if not key:
                continue
            if key in seen_keys:
                await configs.delete_one({"_id": document["_id"]})
            else:
                seen_keys.add(key)
        await configs.create_index("key", unique=True, name="uq_app_config_key")

        templates = database[Collections.NOTIFICATION_TEMPLATES]
        dynamic_keys = {
            "pre_service_reminder.customer",
            "payment_approved_location_sent.customer",
            "reservation_confirmed_logistics_sent.customer",
        }
        for template in SEED_TEMPLATES:
            if template["template_key"] not in dynamic_keys:
                continue
            await templates.update_one(
                {"template_key": template["template_key"]},
                {
                    "$set": {
                        "body": template["body"],
                        "variables_allowed": template["variables_allowed"],
                        "updated_at": now,
                    }
                },
            )
