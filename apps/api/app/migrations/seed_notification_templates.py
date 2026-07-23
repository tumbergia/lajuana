"""Seed notification templates for all notification event types.

Templates se siembran en DOS idiomas (es/en) cuando aplica a clientes finales.
El campo `language` permite que el `notification_service` seleccione el
template correcto según el `holder_language` del reservation.
"""

import asyncio

from app.common.enums import NotificationChannel
from app.core.db import init_db
from app.documents.notification_template_document import NotificationTemplateDocument

# Cada entrada: (template_key, language, channel, body, variables_allowed)
# Los emails y notificaciones internas se mantienen en español únicamente.
SEED_TEMPLATES = [
    # ── Email: reservation_created.customer ──────────────────────────────
    {
        "template_key": "reservation_created.customer",
        "language": "es",
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
    # ── Email: reservation_confirmed.customer ────────────────────────────
    {
        "template_key": "reservation_confirmed.customer",
        "language": "es",
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
    # ── Email: reservation_confirmed.internal ────────────────────────────
    {
        "template_key": "reservation_confirmed.internal",
        "language": "es",
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
        "language": "es",
        "channel": NotificationChannel.IN_APP,
        "subject": "Nueva reserva confirmada",
        "body": "Reserva {{reservation_code}} confirmada - {{participants_count}} participantes.",
        "variables_allowed": ["reservation_code", "participants_count", "customer_name"],
    },
    # ── Email: participant_form_link_generated.customer ───────────────────
    {
        "template_key": "participant_form_link_generated.customer",
        "language": "es",
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
    # ── Email: pre_service_reminder.customer ──────────────────────────────
    {
        "template_key": "pre_service_reminder.customer",
        "language": "es",
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
<p><strong>{{location_name}}</strong> — {{location_address}}, {{location_municipality}}</p>
<p>{{location_directions}}</p>
<p><strong>Google Maps:</strong> <a href="{{location_url}}">Abrir ubicación de La Juana</a></p>

<p><strong>Recuerda:</strong> llegar 15 minutos antes de la hora programada. ¡Te esperamos!</p>""",
        "variables_allowed": [
            "customer_name",
            "reservation_code",
            "participants_count",
            "location_name",
            "location_address",
            "location_municipality",
            "location_directions",
            "location_url",
        ],
    },
    {
        "template_key": "post_service_completed.customer",
        "language": "es",
        "channel": NotificationChannel.EMAIL,
        "subject": "Gracias por vivir La Juana - {{reservation_code}}",
        "body": """<h2>Hola {{customer_name}},</h2>
<p>Gracias por compartir esta experiencia con nosotros.</p>
<p>Esperamos que hayas disfrutado al máximo.</p>
<p>Te invitamos a dejarnos tu reseña y compartir tus fotos.</p>
<p>¡Te esperamos pronto para una nueva aventura!</p>""",
        "variables_allowed": ["customer_name", "reservation_code", "participants_count"],
    },
    # ── WhatsApp: payment_approved_form_sent.customer ────────────────────
    # Multi-idioma — enviado cuando el admin aprueba el comprobante de pago.
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "es",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola {{customer_name}}, tu pago para {{experience_name}} "
            "fue aprobado. Por favor completa el formulario de participantes "
            "obligatorio en este enlace: {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "en",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hi {{customer_name}}, your payment for {{experience_name}} "
            "has been approved. Please complete the mandatory participants form "
            "at this link: {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "fr",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Bonjour {{customer_name}}, votre paiement pour {{experience_name}} "
            "a été approuvé. Veuillez remplir le formulaire obligatoire des "
            "participants à ce lien : {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "de",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hallo {{customer_name}}, Ihre Zahlung für {{experience_name}} "
            "wurde genehmigt. Bitte füllen Sie das obligatorische "
            "Teilnehmerformular unter diesem Link aus: {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "it",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Ciao {{customer_name}}, il tuo pagamento per {{experience_name}} "
            "è stato approvato. Per favore compila il modulo obbligatorio "
            "dei partecipanti a questo link: {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "ru",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Здравствуйте, {{customer_name}}! Ваш платёж за {{experience_name}} "
            "одобрен. Пожалуйста, заполните обязательную форму участников "
            "по этой ссылке: {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "zh",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "您好 {{customer_name}}，您对 {{experience_name}} 的付款已获批准。"
            "请通过此链接填写必需的参与者表格：{{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "payment_approved_form_sent.customer",
        "language": "ja",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "{{customer_name}} 様、{{experience_name}} の支払いが承認されました。"
            "下記のリンクから参加者フォーム（必須）にご記入ください：{{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    # ── WhatsApp: payment_approved_location_sent.customer ────────────────
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "es",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "¡Pago confirmado! Aquí tienes la información para tu experiencia:\n\n"
            "Ubicación de {{location_name}}:\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
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
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "en",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Payment confirmed! Here is the information for your experience:\n\n"
            "{{location_name}} location:\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "RECOMMENDATIONS FOR THE ACTIVITY\n\n"
            "- Wear comfortable clothes: long pants, long-sleeve shirt or t-shirt, "
            "closed shoes, socks covering the ankles, a windbreaker jacket.\n"
            "- Hydration (we avoid single-use plastic bottles, so please bring "
            "your own reusable bottle).\n"
            "- Sunscreen\n"
            "- Insect repellent\n"
            "- Hat or cap\n"
            "- Camera and/or binoculars in case you want to spot and record species.\n"
            "- And the best attitude to enjoy, alongside LA JUANA's mules, the "
            "beautiful landscapes the destination has to offer.\n\n"
            "*During our activities wearing a helmet is mandatory. "
            "It will be provided by LA JUANA.\n\n"
            "We look forward to seeing you!"
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "fr",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Paiement confirmé ! Voici les informations pour votre expérience :\n\n"
            "Emplacement de {{location_name}} :\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "RECOMMANDATIONS POUR L'ACTIVITÉ\n\n"
            "- Portez des vêtements confortables : pantalon long, chemise ou t-shirt "
            "à manches longues, chaussures fermées, chaussettes couvrant les chevilles, "
            "veste coupe-vent.\n"
            "- Hydratation (nous évitons les bouteilles en plastique à usage unique, "
            "veuillez apporter votre propre gourde réutilisable).\n"
            "- Protection solaire\n"
            "- Répulsif à insectes\n"
            "- Chapeau ou casquette\n"
            "- Appareil photo et/ou jumelles au cas où vous voudriez observer et "
            "enregistrer des espèces.\n"
            "- Et la meilleure attitude pour profiter, avec les mules de LA JUANA, "
            "des magnifiques paysages que la destination offre.\n\n"
            "*Pendant nos activités le port du casque est obligatoire. "
            "Il sera fourni par LA JUANA.\n\n"
            "Nous avons hâte de vous accueillir !"
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "de",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Zahlung bestätigt! Hier sind die Informationen für Ihr Erlebnis:\n\n"
            "Standort von {{location_name}}:\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "EMPFEHLUNGEN FÜR DIE AKTIVITÄT\n\n"
            "- Tragen Sie bequeme Kleidung: lange Hose, langärmliges Hemd oder "
            "T-Shirt, geschlossene Schuhe, Socken, die die Knöchel bedecken, "
            "Windbreaker.\n"
            "- Ausreichend Wasser (wir vermeiden Einweg-Plastikflaschen, bitte "
            "bringen Sie Ihre eigene wiederverwendbare Flasche mit).\n"
            "- Sonnenschutz\n"
            "- Insektenschutzmittel\n"
            "- Hut oder Mütze\n"
            "- Kamera und/oder Fernglas, falls Sie Arten beobachten und "
            "fotografieren möchten.\n"
            "- Und die beste Einstellung, um zusammen mit den Maultieren von "
            "LA JUANA die wunderschönen Landschaften des Ziels zu genießen.\n\n"
            "*Während unserer Aktivitäten ist das Tragen eines Helms "
            "obligatorisch. Dieser wird von LA JUANA gestellt.\n\n"
            "Wir freuen uns auf Sie!"
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "it",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Pagamento confermato! Ecco le informazioni per la tua esperienza:\n\n"
            "Posizione di {{location_name}}:\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "RACCOMANDAZIONI PER L'ATTIVITÀ\n\n"
            "- Indossa abiti comodi: pantaloni lunghi, camicia o maglietta a maniche "
            "lunghe, scarpe chiuse, calze che coprano le caviglie, giacca antivento.\n"
            "- Idratazione (evitiamo bottiglie di plastica monouso, quindi ti "
            "chiediamo di portare la tua borraccia riutilizzabile).\n"
            "- Protezione solare\n"
            "- Repellente per insetti\n"
            "- Cappello o berretto\n"
            "- Macchina fotografica e/o binocolo nel caso voglia avvistare e "
            "registrare specie.\n"
            "- E l'atteggiamento migliore per godere, insieme ai muli di LA JUANA, "
            "i bellissimi paesaggi che la destinazione offre.\n\n"
            "*Durante le nostre attività l'uso del casco è obbligatorio. "
            "Sarà fornito da LA JUANA.\n\n"
            "Ti aspettiamo!"
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "ru",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Оплата подтверждена! Вот информация о вашем опыте:\n\n"
            "Расположение {{location_name}}:\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "РЕКОМЕНДАЦИИ ДЛЯ АКТИВНОСТИ\n\n"
            "- Носите удобную одежду: длинные брюки, рубашку или футболку с "
            "длинным рукавом, закрытую обувь, носки, закрывающие щиколотки, "
            "ветрозащитную куртку.\n"
            "- Гидратация (мы избегаем одноразовых пластиковых бутылок, "
            "поэтому просим принести свою многоразовую бутылку).\n"
            "- Солнцезащитный крем\n"
            "- Средство от насекомых\n"
            "- Шляпа или кепка\n"
            "- Камера и/или бинокль на случай, если вы захотите наблюдать и "
            "фотографировать виды.\n"
            "- И лучший настрой, чтобы наслаждаться вместе с мулами LA JUANA "
            "красивыми пейзажами этого места.\n\n"
            "*Во время наших активностей ношение шлема обязательно. "
            "Его предоставит LA JUANA.\n\n"
            "Ждём вас!"
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "zh",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "付款确认！以下是您体验的信息：\n\n"
            "{{location_name}} 位置：\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "活动建议\n\n"
            "- 穿着舒适的衣服：长裤、长袖衬衫或T恤、封闭式鞋子、覆盖脚踝的袜子、防风外套。\n"
            "- 补水（我们避免使用一次性塑料瓶，请自带可重复使用的水壶）。\n"
            "- 防晒\n"
            "- 驱虫剂\n"
            "- 帽子或棒球帽\n"
            "- 相机和/或望远镜（如果您想观察和记录物种）。\n"
            "- 以及与LA JUANA的骡子一起欣赏目的地美丽风景的最佳态度。\n\n"
            "*在我们的活动中，必须佩戴头盔。头盔将由LA JUANA提供。\n\n"
            "我们期待您的到来！"
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "payment_approved_location_sent.customer",
        "language": "ja",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "お支払いが確認されました！体験に関する情報はこちらです：\n\n"
            "{{location_name}} の場所：\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "アクティビティのおすすめ\n\n"
            "- 快適な服装でお越しください：長ズボン、長袖のシャツまたはTシャツ、"
            " closed-toeの靴、くるぶしが覆われる靴下、ウィンドブレーカー。\n"
            "- 水分補給（使い捨てのペットボトルは避けていますので、"
            "ご自身の reusableボトルをお持ちください）。\n"
            "- 日焼け止め\n"
            "- 虫除け\n"
            "- 帽子またはキャップ\n"
            "- カメラおよび/または双眼鏡（種の観察や記録をご希望の場合）。\n"
            "- そして、LA JUANAのら馬と一緒に、目的地の美しい景色を楽しむ最高の姿勢。\n\n"
            "*アクティビティ中はヘルメットの着用が必須です。"
            "ヘルメットはLA JUANAが提供します。\n\n"
            "お会いできるのを楽しみにしています！"
        ),
        "variables_allowed": [
            "customer_name",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    # ── WhatsApp: payment_rejected_sent.customer ──────────────────────────
    {
        "template_key": "payment_rejected_sent.customer",
        "language": "es",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola {{customer_name}}, el comprobante de pago para "
            "{{experience_name}} fue rechazado. Motivo: {{rejection_reason}}. "
            "Por favor envía un nuevo comprobante válido para continuar."
        ),
        "variables_allowed": ["customer_name", "experience_name", "rejection_reason"],
    },
    {
        "template_key": "payment_rejected_sent.customer",
        "language": "en",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hi {{customer_name}}, the payment proof for "
            "{{experience_name}} was rejected. Reason: {{rejection_reason}}. "
            "Please send a new valid proof to continue."
        ),
        "variables_allowed": ["customer_name", "experience_name", "rejection_reason"],
    },
    # ── WhatsApp: reservation_confirmed_logistics_sent.customer ───────────
    {
        "template_key": "reservation_confirmed_logistics_sent.customer",
        "language": "es",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "¡Tu reserva {{reservation_code}} ha sido confirmada! "
            "Aquí tienes la información para tu experiencia {{experience_name}} "
            "el {{scheduled_date}}:\n\n"
            "Ubicación de {{location_name}}:\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "RECOMENDACIONES PARA LA ACTIVIDAD\n\n"
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
            "customer_name",
            "reservation_code",
            "experience_name",
            "scheduled_date",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    {
        "template_key": "reservation_confirmed_logistics_sent.customer",
        "language": "en",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Your reservation {{reservation_code}} has been confirmed! "
            "Here is the information for your {{experience_name}} "
            "on {{scheduled_date}}:\n\n"
            "{{location_name}} location:\n"
            "{{location_url}}\n"
            "{{location_directions}}\n\n"
            "RECOMMENDATIONS FOR THE ACTIVITY\n\n"
            "- Wear comfortable clothes: long pants, long-sleeve shirt or t-shirt, "
            "closed shoes, socks covering the ankles, a windbreaker jacket.\n"
            "- Hydration (bring your reusable bottle).\n"
            "- Sunscreen and insect repellent.\n"
            "- Hat or cap.\n"
            "- Camera and/or binoculars.\n"
            "- Arrive 15 minutes before the scheduled time.\n\n"
            "We look forward to seeing you!"
        ),
        "variables_allowed": [
            "customer_name",
            "reservation_code",
            "experience_name",
            "scheduled_date",
            "location_name",
            "location_url",
            "location_directions",
        ],
    },
    # ── WhatsApp: participant_form_resent.customer ───────────────────────
    {
        "template_key": "participant_form_resent.customer",
        "language": "es",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola {{customer_name}}, aquí está nuevamente el enlace del "
            "formulario de participantes para {{experience_name}}: {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    {
        "template_key": "participant_form_resent.customer",
        "language": "en",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hi {{customer_name}}, here is the participants form link again "
            "for {{experience_name}}: {{form_url}}"
        ),
        "variables_allowed": ["customer_name", "experience_name", "form_url"],
    },
    # ── WhatsApp: reservation_cancelled.customer ──────────────────────────
    {
        "template_key": "reservation_cancelled.customer",
        "language": "es",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hola, lamentamos informarte que tu reserva "
            "{{reservation_code}} para {{experience_name}} ha sido cancelada. "
            "Si tienes alguna duda o deseas reprogramar, escríbenos y con gusto te ayudaremos. "
        ),
        "variables_allowed": ["customer_name", "reservation_code", "experience_name"],
    },
    {
        "template_key": "reservation_cancelled.customer",
        "language": "en",
        "channel": NotificationChannel.WHATSAPP,
        "subject": None,
        "body": (
            "Hi, we're sorry to inform you that your reservation "
            "{{reservation_code}} for {{experience_name}} has been cancelled. "
            "If you have any questions or would like to reschedule, write to us and we'll be happy to help. "
        ),
        "variables_allowed": ["customer_name", "reservation_code", "experience_name"],
    },
]


async def seed_notification_templates() -> int:
    await init_db()
    count = 0
    for tpl in SEED_TEMPLATES:
        natural_key = {
            "template_key": tpl["template_key"],
            "channel": tpl["channel"],
        }
        existing = await NotificationTemplateDocument.find_one(natural_key)
        if existing is not None:
            continue
        doc = NotificationTemplateDocument(**tpl)
        await doc.insert()
        count += 1
    return count


if __name__ == "__main__":
    created = asyncio.run(seed_notification_templates())
    print(f"Created {created} notification templates.")
