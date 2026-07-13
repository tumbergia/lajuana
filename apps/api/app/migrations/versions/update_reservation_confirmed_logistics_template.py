"""Update reservation_confirmed_logistics WhatsApp template after schedule removal."""

import asyncio

from app.common.enums import NotificationChannel
from app.core.db import init_db
from app.documents.notification_template_document import NotificationTemplateDocument

UPDATED_BODY = (
    "Hola {{customer_name}}, tu reserva {{reservation_code}} para "
    "{{experience_name}} está confirmada para el {{scheduled_date}} "
    "a las {{start_time}}.\n\n"
    "Lugar de encuentro:\n"
    "{{meeting_point}}\n\n"
    "RECOMENDACIONES PARA LA ACTIVIDAD\n\n"
    "- Usar ropa cómoda: pantalón largo, camisa o camiseta manga larga, "
    "zapatos cerrados, medias que cubran los tobillos, chaqueta rompevientos.\n"
    "- Hidratación (trae tu botella reutilizable).\n"
    "- Protección solar y repelente de insectos.\n"
    "- Sombrero o gorra.\n"
    "- Cámara y/o binoculares.\n"
    "- Llegar 15 minutos antes de la hora programada.\n\n"
    "¡Te esperamos!"
)


async def update_reservation_confirmed_logistics_template() -> bool:
    await init_db()
    doc = await NotificationTemplateDocument.find_one(
        {
            "template_key": "reservation_confirmed_logistics_sent.customer",
            "channel": NotificationChannel.WHATSAPP,
        }
    )
    if doc is None:
        return False
    doc.body = UPDATED_BODY
    doc.variables_allowed = [
        "customer_name",
        "reservation_code",
        "experience_name",
        "scheduled_date",
        "start_time",
        "meeting_point",
    ]
    await doc.save()
    return True


if __name__ == "__main__":
    updated = asyncio.run(update_reservation_confirmed_logistics_template())
    print("Updated template." if updated else "Template not found.")
