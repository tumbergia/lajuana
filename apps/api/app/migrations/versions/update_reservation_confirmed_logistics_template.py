"""Update reservation_confirmed_logistics WhatsApp template after schedule removal."""

import asyncio

from app.common.enums import NotificationChannel
from app.core.db import init_db
from app.documents.notification_template_document import NotificationTemplateDocument

UPDATED_BODY = (
    "¡Tu reserva {{reservation_code}} ha sido confirmada! "
    "Aquí tienes la información para tu experiencia {{experience_name}} "
    "el {{scheduled_date}}:\n\n"
    "Ubicación de la finca:\n"
    "https://maps.google.com/?q=5.152583,-75.501472\n\n"
    "RECOMENDACIONES PARA LA ACTIVIDAD\n\n"
    "- Usar ropa cómoda: pantalón largo, camisa o camiseta manga larga, "
    "zapatos cerrados, medias que cubran los tobillos, chaqueta rompevientos.\n"
    "- Hidratación (evitamos usar botellas de plástico desechable, así que "
    "les solicitamos traer sus botellas reutilizables).\n"
    "- Protección solar\n"
    "- Repelente de insectos\n"
    "- Sombrero o en su defecto gorra\n"
    "- Cámara y/o binoculares en caso que quiera realizar avistamiento y "
    "registro de especies.\n"
    "- Y la mejor actitud para disfrutar junto a las mulas de LA JUANA "
    "los hermosos paisajes que el destino ofrece.\n\n"
    "*Durante nuestras actividades el uso de casco es obligatorio. "
    "Éste será proporcionado por LA JUANA.\n\n"
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
    ]
    await doc.save()
    return True


if __name__ == "__main__":
    updated = asyncio.run(update_reservation_confirmed_logistics_template())
    print("Updated template." if updated else "Template not found.")
