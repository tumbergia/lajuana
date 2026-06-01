"""Seed notification templates for all notification event types."""

import asyncio

from app.common.enums import NotificationChannel
from app.core.db import init_db
from app.documents.notification_template_document import NotificationTemplateDocument

SEED_TEMPLATES = [
    {
        "template_key": "reservation_created.customer",
        "channel": NotificationChannel.EMAIL,
        "subject": "Solicitud recibida - {{reservation_code}} - La Juana",
        "body": """<h2>Hola {{customer_name}},</h2>
<p>Hemos recibido tu solicitud de reserva. Estos son los detalles:</p>
<ul>
  <li><strong>Código:</strong> {{reservation_code}}</li>
  <li><strong>Participantes:</strong> {{participants_count}}</li>
</ul>
<p>Te contactaremos pronto para coordinar los detalles de tu experiencia.</p>
<p>¡Gracias por elegir La Juana!</p>""",
        "variables_allowed": ["customer_name", "reservation_code", "participants_count"],
    },
    {
        "template_key": "reservation_confirmed.customer",
        "channel": NotificationChannel.EMAIL,
        "subject": "Reserva {{reservation_code}} confirmada - La Juana",
        "body": """<h2>¡Hola {{customer_name}}!</h2>
<p>Tu reserva ha sido <strong>confirmada</strong>.</p>
<ul>
  <li><strong>Código:</strong> {{reservation_code}}</li>
  <li><strong>Participantes:</strong> {{participants_count}}</li>
</ul>
<p>Pronto recibirás la ubicación, recomendaciones y el formulario de participantes.</p>
<p>¡Prepárate para vivir una experiencia inolvidable!</p>""",
        "variables_allowed": ["customer_name", "reservation_code", "participants_count"],
    },
    {
        "template_key": "reservation_confirmed.internal",
        "channel": NotificationChannel.EMAIL,
        "subject": "Nueva reserva confirmada - {{reservation_code}}",
        "body": """<h2>Reserva confirmada</h2>
<ul>
  <li><strong>Código:</strong> {{reservation_code}}</li>
  <li><strong>Cliente:</strong> {{customer_name}}</li>
  <li><strong>Participantes:</strong> {{participants_count}}</li>
</ul>
<p>Revisa la operación y coordina los preparativos necesarios.</p>""",
        "variables_allowed": ["customer_name", "reservation_code", "participants_count"],
    },
    {
        "template_key": "reservation_confirmed.internal",
        "channel": NotificationChannel.IN_APP,
        "subject": "Nueva reserva confirmada",
        "body": "Reserva {{reservation_code}} confirmada - {{participants_count}} participantes.",
        "variables_allowed": ["reservation_code", "participants_count", "customer_name"],
    },
    {
        "template_key": "participant_form_link_generated.customer",
        "channel": NotificationChannel.EMAIL,
        "subject": "Formulario de participantes - {{reservation_code}} - La Juana",
        "body": """<h2>Hola {{customer_name}},</h2>
<p>Completa el formulario de participantes obligatorio para tu reserva {{reservation_code}}.</p>
<p><a href="{{form_url}}">Ir al formulario</a></p>
<p>Este enlace vence el {{form_expires_at}}.</p>
<p>¡Gracias!</p>""",
        "variables_allowed": [
            "customer_name",
            "reservation_code",
            "form_url",
            "form_expires_at",
        ],
    },
    {
        "template_key": "pre_service_reminder.customer",
        "channel": NotificationChannel.EMAIL,
        "subject": "Tu experiencia es mañana - {{reservation_code}} - La Juana",
        "body": """<h2>Hola {{customer_name}},</h2>
<p>Te recordamos que <strong>mañana</strong> tienes tu experiencia reservada.</p>
<ul>
  <li><strong>Código:</strong> {{reservation_code}}</li>
  <li><strong>Participantes:</strong> {{participants_count}}</li>
</ul>

<h3>RECOMENDACIONES PARA LA ACTIVIDAD</h3>
<ul>
  <li>Usar ropa cómoda: pantalón largo, camisa o camiseta manga larga, zapatos cerrados, medias que cubran los tobillos, chaqueta rompevientos.</li>
  <li>Hidratación (evitamos usar botellas de plástico desechable, así que les solicitamos traer sus botellas reutilizables).</li>
  <li>Protección solar</li>
  <li>Repelente de insectos</li>
  <li>Sombrero o en su defecto gorra</li>
  <li>Cámara y/o binoculares en caso que quiera realizar avistamiento y registro de especies.</li>
  <li>Y la mejor actitud para disfrutar junto a las mulas de LA JUANA los hermosos paisajes que el destino ofrece.</li>
</ul>

<p><strong>Durante nuestras actividades el uso de casco es obligatorio. Éste será proporcionado por LA JUANA.</strong></p>

<h3>NUESTRA UBICACIÓN</h3>
<p>Nos encontramos a 30 minutos al norte de Manizales (18 km), sobre la Ruta de la Arriería (vía a Salamina). A los 16 km en la vía principal, tomar el desvío a la derecha, por la vía destapada, que conduce a las ruinas de la antigua fábrica de Cementos Caldas, a 2 km de este desvío (5 min aprox), encontrará la portada al lado izquierdo de la vía (aviso LA JUANA).</p>
<p><strong>Coordenadas:</strong> 5°09'09.3"N 75°30'05.3"W</p>
<p><strong>Google Maps:</strong> <a href="https://maps.google.com/?q=5.152568,-75.501468">5.152568, -75.501468</a></p>

<p><strong>Recuerda:</strong> llegar 15 minutos antes de la hora programada. ¡Te esperamos!</p>""",
        "variables_allowed": ["customer_name", "reservation_code", "participants_count"],
    },
    {
        "template_key": "post_service_completed.customer",
        "channel": NotificationChannel.EMAIL,
        "subject": "Gracias por vivir La Juana - {{reservation_code}}",
        "body": """<h2>Hola {{customer_name}},</h2>
<p>Gracias por compartir esta experiencia con nosotros.</p>
<p>Esperamos que hayas disfrutado al máximo.</p>
<p>Te invitamos a dejarnos tu reseña y compartir tus fotos.</p>
<p>¡Te esperamos pronto para una nueva aventura!</p>""",
        "variables_allowed": ["customer_name", "reservation_code", "participants_count"],
    },
    # --- WhatsApp transactional templates (deterministic, not chatbot) ---
    {
        "template_key": "payment_approved_form_sent.customer",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola {{customer_name}}, tu pago para {{experience_name}} "
            "fue aprobado. Por favor completa el formulario de participantes "
            "obligatorio en este enlace: {{form_url}}"
        ),
        "variables_allowed": [
            "customer_name", "experience_name", "form_url",
        ],
    },
    {
        "template_key": "payment_rejected_sent.customer",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola {{customer_name}}, el comprobante de pago para "
            "{{experience_name}} fue rechazado. Motivo: {{rejection_reason}}. "
            "Por favor envía un nuevo comprobante válido para continuar."
        ),
        "variables_allowed": [
            "customer_name", "experience_name", "rejection_reason",
        ],
    },
    {
        "template_key": "reservation_confirmed_logistics_sent.customer",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola {{customer_name}}, tu reserva {{reservation_code}} para "
            "{{experience_name}} está confirmada para el {{scheduled_date}} "
            "a las {{start_time}}.\n\n"
            "Lugar de encuentro: {{meeting_point}}\n\n"
            "Recomendaciones:\n"
            "- Usar ropa cómoda: pantalón largo, camisa o camiseta manga larga, "
            "zapatos cerrados, medias que cubran los tobillos, chaqueta rompevientos.\n"
            "- Hidratación (trae tu botella reutilizable).\n"
            "- Protección solar y repelente de insectos.\n"
            "- Sombrero o gorra.\n"
            "- Cámara y/o binoculares.\n"
            "- Llegar 15 minutos antes de la hora programada.\n\n"
            "¡Te esperamos!"
        ),
        "variables_allowed": [
            "customer_name", "reservation_code", "experience_name",
            "scheduled_date", "start_time", "meeting_point",
        ],
    },
    {
        "template_key": "participant_form_resent.customer",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola {{customer_name}}, aquí está nuevamente el enlace del "
            "formulario de participantes para {{experience_name}}: {{form_url}}"
        ),
        "variables_allowed": [
            "customer_name", "experience_name", "form_url",
        ],
    },
    {
        "template_key": "reservation_cancelled.customer",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola, lamentamos informarte que tu reserva "
            "{{reservation_code}} para {{experience_name}} ha sido cancelada. "
            "Si tienes alguna duda o deseas reprogramar, escríbenos y con gusto te ayudaremos. "
        ),
        "variables_allowed": [
            "customer_name", "reservation_code", "experience_name",
        ],
    },
]


async def seed_notification_templates() -> int:
    await init_db()
    count = 0
    for tpl in SEED_TEMPLATES:
        existing = await NotificationTemplateDocument.find_one(
            {
                "template_key": tpl["template_key"],
                "channel": tpl["channel"],
            }
        )
        if existing is not None:
            continue
        doc = NotificationTemplateDocument(**tpl)
        await doc.insert()
        count += 1
    return count


if __name__ == "__main__":
    created = asyncio.run(seed_notification_templates())
    print(f"Created {created} notification templates.")
