_MESSAGES: dict[str, dict[str, str]] = {
    "missing_fields_default": {
        "es": "Necesito algunos datos para continuar. ¿Me los compartes?",
        "en": "I need some details to continue. Could you share them?",
    },
    "missing_fields": {
        "es": "Con gusto sigo. Solo necesito que me indiques {fields}. ¿Me ayudas con eso?",
        "en": "I'd be happy to help. I just need you to tell me {fields}. Can you help with that?",
    },
    "operation_cancelled": {
        "es": "Operación cancelada. ¿En qué más puedo ayudarte?",
        "en": "Operation cancelled. How else can I help you?",
    },
    "resource_exhausted": {
        "es": "Servicio de IA sobrepasado. Intenta en unos minutos.",
        "en": "AI service is overloaded. Please try again in a few minutes.",
    },
    "model_unavailable": {
        "es": "Modelo no disponible. Te transfiero con un asesor.",
        "en": "Model unavailable. I'll transfer you to a human advisor.",
    },
    "provider_error": {
        "es": "Ocurrió un error temporal en mi sistema de procesamiento. Voy a transferirte con un asesor humano para que no te quedes sin atención.",
        "en": "A temporary error occurred in my processing system. I'll transfer you to a human advisor so you don't go unattended.",
    },
    "invalid_date": {
        "es": "Para evitar errores con la reserva, necesito que me confirmes la fecha exacta en formato día, mes y año.",
        "en": "To avoid errors with the reservation, I need you to confirm the exact date in day, month, and year format.",
    },
    "policy_blocked": {
        "es": "Necesito confirmar datos antes de avanzar.",
        "en": "I need to confirm some details before proceeding.",
    },
    "needs_more_info": {
        "es": "Necesito más información.",
        "en": "I need more information.",
    },
    "tool_confirmation": {
        "es": "Voy a ejecutar: {tool_name}. ¿Estás seguro? Responde 'sí' para confirmar o 'no' para cancelar.",
        "en": "I'm going to run: {tool_name}. Are you sure? Reply 'yes' to confirm or 'no' to cancel.",
    },
    "no_alternative_dates": {
        "es": "Lo siento, no encontré más fechas disponibles para esta experiencia. Un asesor humano podrá revisar opciones alternativas y ayudarte con lo que necesites. Te transfiero ahora.",
        "en": "Sorry, I couldn't find any more available dates for this experience. A human advisor can review alternative options and help you with what you need. I'll transfer you now.",
    },
    "media_no_reservation": {
        "es": "Recibimos tu archivo, pero no encuentro una pre-reserva activa con este número. Primero te ayudo a crear la pre-reserva y luego adjuntamos el comprobante.",
        "en": "We received your file, but I can't find an active pre-reservation with this number. Let me help you create the pre-reservation first, then we can attach the proof.",
    },
    "media_multiple_reservations": {
        "es": "Recibí tu comprobante. Como tienes varias reservas activas, envíame el código de la reserva (ej. PR-XXXX) para asociarlo correctamente.",
        "en": "I received your proof. Since you have multiple active reservations, please send me the reservation code (e.g., PR-XXXX) to match it correctly.",
    },
    "media_proof_received": {
        "es": "Recibimos tu comprobante y queda en revisión administrativa.",
        "en": "We received your proof and it's under administrative review.",
    },
    "audio_pending": {
        "es": "[Audio recibido pendiente de transcripción]",
        "en": "[Audio received — pending transcription]",
    },
    "media_received": {
        "es": "[{type} recibido]",
        "en": "[{type} received]",
    },
    "no_availability": {
        "es": "No hay disponibilidad para esa fecha. ¿Te gustaría ver opciones alternativas?",
        "en": "There's no availability for that date. Would you like to see alternative options?",
    },
    # ── check_availability_and_quote (combined) ──
    "check_quote_available_with_quote": {
        "es": "{experience_name} para {participants} persona(s) el {date} está disponible y sale a ${subtotal} COP (${unit_price} por persona).\n\nPara apartarte la fecha, envíame tu nombre completo y tu correo electrónico. ¿Me los compartes?",
        "en": "{experience_name} for {participants} person(s) on {date} is available and comes out to ${subtotal} COP (${unit_price} per person).\n\nTo reserve the date, please send me your full name and email address. Can you share them?",
        "fr": "{experience_name} pour {participants} personne(s) le {date} est disponible et coûte ${subtotal} COP (${unit_price} par personne).\n\nPour réserver la date, envoyez-moi votre nom complet et votre adresse e-mail. Pouvez-vous les partager ?",
        "de": "{experience_name} für {participants} Person(en) am {date} ist verfügbar und kostet ${subtotal} COP (${unit_price} pro Person).\n\nUm das Datum zu reservieren, senden Sie mir bitte Ihren vollständigen Namen und Ihre E-Mail-Adresse. Können Sie diese teilen?",
        "it": "{experience_name} per {participants} persona/e il {date} è disponibile e costa ${subtotal} COP (${unit_price} a persona).\n\nPer prenotare la data, inviami il tuo nome completo e il tuo indirizzo email. Puoi condividerli?",
        "ru": "{experience_name} для {participants} чел. {date} доступно и стоит ${subtotal} COP (${unit_price} за человека).\n\nЧтобы забронировать дату, отправьте мне ваше полное имя и адрес электронной почты. Можете их прислать?",
        "zh": "{experience_name} 在 {date} 有空，可容纳 {participants} 人，总价 ${subtotal} COP（每人 ${unit_price} COP）。\n\n如需预订此日期，请将您的全名和电子邮件地址发送给我。可以分享吗？",
        "ja": "{experience_name} は {date} に {participants} 名様で空きがあり、料金は ${subtotal} COP（お一人様 ${unit_price} COP）です。\n\n日付を予約するため、お名前とメールアドレスをお送りください。",
    },
    "check_quote_not_found": {
        "es": "No encontré una experiencia que coincida con tu solicitud. ¿Me confirmas el nombre?",
        "en": "I couldn't find an experience that matches your request. Could you confirm the name?",
    },
    "check_quote_min_notice": {
        "es": "La reserva requiere mínimo {min_notice_days} días de anticipación. ¿Quieres ver fechas disponibles?",
        "en": "Reservations require at least {min_notice_days} days in advance. Would you like to see available dates?",
    },
    "check_quote_already_booked": {
        "es": "Ya existe una reserva activa para esa fecha. ¿Quieres que te sugiera fechas alternativas?",
        "en": "There's already an active reservation for that date. Would you like me to suggest alternative dates?",
    },
    "check_quote_pricing_missing": {
        "es": "La experiencia no tiene tarifa configurada para esa cantidad de participantes. ¿Me confirmas el número de personas?",
        "en": "The experience doesn't have a rate configured for that number of participants. Could you confirm the number of people?",
    },
    # ── quote_experience ──
    "quote_experience_not_found": {
        "es": "No se encontró una experiencia que coincida con la solicitud.",
        "en": "I couldn't find an experience that matches your request.",
    },
    "quote_experience_unavailable": {
        "es": "La experiencia no está disponible en este momento.",
        "en": "The experience is not available right now.",
    },
    "quote_pricing_missing": {
        "es": "La experiencia no tiene tarifa configurada para esa cantidad de participantes.",
        "en": "The experience doesn't have a rate configured for that number of participants.",
    },
    "quote_experience_response": {
        "es": "{experience_name} para {participants} persona(s) sale a ${subtotal} COP (${unit_price} por persona).\n\nPara apartarte la fecha, envíame tu nombre completo y tu correo electrónico. ¿Me los compartes?",
        "en": "{experience_name} for {participants} person(s) comes out to ${subtotal} COP (${unit_price} per person).\n\nTo reserve the date, please send me your full name and email address. Can you share them?",
        "fr": "{experience_name} pour {participants} personne(s) coûte ${subtotal} COP (${unit_price} par personne).\n\nPour réserver la date, envoyez-moi votre nom complet et votre e-mail. Pouvez-vous les partager ?",
        "de": "{experience_name} für {participants} Person(en) kostet ${subtotal} COP (${unit_price} pro Person).\n\nUm das Datum zu reservieren, senden Sie mir bitte Ihren vollständigen Namen und Ihre E-Mail. Können Sie diese teilen?",
        "it": "{experience_name} per {participants} persona/e costa ${subtotal} COP (${unit_price} a persona).\n\nPer prenotare la data, inviami il tuo nome completo e la tua email. Puoi condividerli?",
        "ru": "{experience_name} для {participants} чел. стоит ${subtotal} COP (${unit_price} за человека).\n\nЧтобы забронировать дату, отправьте полное имя и email. Можете их прислать?",
        "zh": "{experience_name} 共 {participants} 人，总价 ${subtotal} COP（每人 ${unit_price} COP）。\n\n如需预订，请将您的全名和电子邮件发送给我。可以分享吗？",
        "ja": "{experience_name} は {participants} 名様で ${subtotal} COP（お一人様 ${unit_price} COP）です。\n\n予約のため、お名前とメールアドレスをお送りください。",
    },
    "list_experiences_header": {
        "es": "Estas son nuestras experiencias disponibles:",
        "en": "Here are our available experiences:",
        "fr": "Voici nos expériences disponibles :",
        "de": "Das sind unsere verfügbaren Erlebnisse:",
        "it": "Queste sono le nostre esperienze disponibili:",
        "ru": "Вот наши доступные впечатления:",
        "zh": "以下是我们目前提供的体验：",
        "ja": "ご利用いただける体験はこちらです：",
    },
    "list_experiences_item": {
        "es": "• {name} — desde ${price} COP",
        "en": "• {name} — from ${price} COP",
        "fr": "• {name} — à partir de ${price} COP",
        "de": "• {name} — ab ${price} COP",
        "it": "• {name} — da ${price} COP",
        "ru": "• {name} — от ${price} COP",
        "zh": "• {name} — 起价 ${price} COP",
        "ja": "• {name} — ${price} COP から",
    },
    "list_experiences_item_no_price": {
        "es": "• {name}",
        "en": "• {name}",
        "fr": "• {name}",
        "de": "• {name}",
        "it": "• {name}",
        "ru": "• {name}",
        "zh": "• {name}",
        "ja": "• {name}",
    },
    "list_experiences_footer": {
        "es": "\n\n¿Cuál te interesa o quieres más detalles de alguna?",
        "en": "\n\nWhich one interests you, or would you like more details on any?",
        "fr": "\n\nLaquelle vous intéresse, ou voulez-vous plus de détails ?",
        "de": "\n\nWelche interessiert Sie, oder möchten Sie mehr Details?",
        "it": "\n\nQuale ti interessa o vuoi più dettagli su qualcuna?",
        "ru": "\n\nКакая вас интересует, или нужны подробности?",
        "zh": "\n\n您对哪一个感兴趣，或者想了解更多详情？",
        "ja": "\n\nご興味のある体験はありますか？詳細もお伝えできます。",
    },
    "list_experiences_empty": {
        "es": "Ahora mismo no tengo experiencias activas para mostrar. ¿Te ayudo con otra consulta?",
        "en": "I don't have any active experiences to show right now. Can I help with something else?",
        "fr": "Je n'ai aucune expérience active à afficher pour le moment. Puis-je vous aider autrement ?",
        "de": "Ich habe gerade keine aktiven Erlebnisse zum Anzeigen. Kann ich anders helfen?",
        "it": "Al momento non ho esperienze attive da mostrare. Posso aiutarti con altro?",
        "ru": "Сейчас нет активных впечатлений для показа. Чем ещё помочь?",
        "zh": "目前没有可显示的体验。还有什么可以帮您的吗？",
        "ja": "現在表示できる体験がありません。他にご用件はありますか？",
    },
    "experience_detail_title": {
        "es": "*{name}*",
        "en": "*{name}*",
        "fr": "*{name}*",
        "de": "*{name}*",
        "it": "*{name}*",
        "ru": "*{name}*",
        "zh": "*{name}*",
        "ja": "*{name}*",
    },
    "experience_detail_duration": {
        "es": "Duración: {duration}",
        "en": "Duration: {duration}",
        "fr": "Durée : {duration}",
        "de": "Dauer: {duration}",
        "it": "Durata: {duration}",
        "ru": "Длительность: {duration}",
        "zh": "时长：{duration}",
        "ja": "所要時間：{duration}",
    },
    "experience_detail_price": {
        "es": "Desde ${price} {currency}",
        "en": "From ${price} {currency}",
        "fr": "À partir de ${price} {currency}",
        "de": "Ab ${price} {currency}",
        "it": "Da ${price} {currency}",
        "ru": "От ${price} {currency}",
        "zh": "起价 ${price} {currency}",
        "ja": "${price} {currency} から",
    },
    "experience_detail_includes": {
        "es": "Incluye: {items}",
        "en": "Includes: {items}",
        "fr": "Inclus : {items}",
        "de": "Inbegriffen: {items}",
        "it": "Include: {items}",
        "ru": "Включено: {items}",
        "zh": "包含：{items}",
        "ja": "含まれるもの：{items}",
    },
    "experience_detail_footer": {
        "es": "\n\n¿Quieres cotizar alguna, ver fechas o reservar?",
        "en": "\n\nWant a quote, available dates, or to book?",
        "fr": "\n\nVous voulez un devis, des dates ou réserver ?",
        "de": "\n\nMöchten Sie ein Angebot, Termine oder buchen?",
        "it": "\n\nVuoi un preventivo, le date o prenotare?",
        "ru": "\n\nНужна цена, даты или бронь?",
        "zh": "\n\n需要报价、日期还是预订？",
        "ja": "\n\n見積もり・日程・予約をご希望ですか？",
    },
    "experience_detail_not_found": {
        "es": "No encontré esa experiencia en nuestro catálogo. ¿Quieres que te liste las opciones disponibles?",
        "en": "I couldn't find that experience in our catalog. Want me to list the available options?",
        "fr": "Je n'ai pas trouvé cette expérience. Voulez-vous la liste des options ?",
        "de": "Dieses Erlebnis finde ich nicht im Katalog. Soll ich die Optionen listen?",
        "it": "Non ho trovato quell'esperienza. Vuoi l'elenco delle opzioni?",
        "ru": "Не нашёл это впечатление в каталоге. Показать доступные варианты?",
        "zh": "目录里找不到该体验。要我列出可用选项吗？",
        "ja": "その体験はカタログにありません。一覧をお見せしましょうか？",
    },
    "check_available_response": {
        "es": "{experience_name} para {participants} persona(s) el {date} tiene cupo.\n\nPara darte el precio y apartar la fecha, envíame tu nombre completo y correo, o dime 'cotízame'.",
        "en": "{experience_name} for {participants} person(s) on {date} has availability.\n\nTo get the price and hold the date, send me your full name and email, or say 'quote me'.",
        "fr": "{experience_name} pour {participants} personne(s) le {date} a de la place.\n\nPour le prix et réserver, envoyez nom complet et e-mail, ou dites 'cotisez-moi'.",
        "de": "{experience_name} für {participants} Person(en) am {date} hat freie Plätze.\n\nFür Preis und Reservierung: vollständiger Name und E-Mail, oder sagen Sie 'cotízame'.",
        "it": "{experience_name} per {participants} persona/e il {date} ha posti.\n\nPer prezzo e prenotazione: nome completo e email, oppure dimmi 'cotízame'.",
        "ru": "{experience_name} для {participants} чел. на {date} свободно.\n\nДля цены и брони: полное имя и email, или напишите 'cotízame'.",
        "zh": "{experience_name} 在 {date} 有 {participants} 人的名额。\n\n如需报价并预订，请发送全名和邮箱，或说「cotízame」。",
        "ja": "{experience_name} は {date} に {participants} 名分の空きがあります。\n\n料金と予約のため、お名前とメールを送るか「cotízame」と伝えてください。",
    },
    "greeting": {
        "es": "¡Hola! Soy el asistente de La Juana Colombia. ¿En qué puedo ayudarte?",
        "en": "Hello! I'm the assistant from La Juana Colombia. How can I help you?",
    },
    "tool_success": {
        "es": "Tool {tool_name} ejecutada correctamente.",
        "en": "Tool {tool_name} executed successfully.",
    },
    "unsupported_file_type": {
        "es": "¡Hola! Por ahora solo puedo recibir mensajes de texto, imágenes, audios y archivos PDF para comprobantes de pago. Los stickers, videos y otros documentos como Word o Excel no son compatibles. ¿Puedes enviarme la información de otra forma?",
        "en": "Hello! For now I can only receive text messages, images, audio, and PDF files for payment proofs. Stickers, videos, and other documents like Word or Excel are not supported. Could you send me the information another way?",
    },
    "unsupported_document_type": {
        "es": "Recibí tu archivo, pero solo aceptamos archivos PDF para comprobantes de pago. Los documentos de Word, Excel u otros formatos no son compatibles. ¿Puedes enviarme el comprobante en formato PDF o una foto?",
        "en": "I received your file, but we only accept PDF files for payment proofs. Word, Excel, or other formats are not supported. Could you send the proof as a PDF or a photo instead?",
    },
    # ── Payment steps (usados por payment_message_service.render_payment_steps) ──
    "payment_step_1_header": {
        "es": "PASO 1. Realizar el pago del valor de la experiencia según número de participantes.",
        "en": "STEP 1. Make the payment for the experience based on the number of participants.",
        "fr": "ÉTAPE 1. Effectuez le paiement de la valeur de l'expérience selon le nombre de participants.",
        "de": "SCHRITT 1. Zahlen Sie den Betrag der Erfahrung entsprechend der Teilnehmerzahl.",
        "it": "PASSO 1. Effettua il pagamento dell'importo dell'esperienza in base al numero di partecipanti.",
        "ru": "ШАГ 1. Произведите оплату стоимости услуги в зависимости от количества участников.",
        "zh": "步骤 1. 根据参与人数支付体验费用。",
        "ja": "ステップ 1. 参加人数に応じた体験料金をお支払いください。",
    },
    "payment_methods_header": {
        "es": "Medios de pago disponibles:",
        "en": "Available payment methods:",
        "fr": "Moyens de paiement disponibles :",
        "de": "Verfügbare Zahlungsmethoden:",
        "it": "Metodi di pagamento disponibili:",
        "ru": "Доступные способы оплаты:",
        "zh": "可用的付款方式：",
        "ja": "利用可能な支払い方法：",
    },
    "payment_account_label": {
        "es": "CUENTA",
        "en": "ACCOUNT",
        "fr": "COMPTE",
        "de": "KONTO",
        "it": "CONTO",
        "ru": "СЧЁТ",
        "zh": "账户",
        "ja": "口座",
    },
    "payment_account_number": {
        "es": "No.",
        "en": "No.",
        "fr": "N°",
        "de": "Nr.",
        "it": "N.",
        "ru": "№",
        "zh": "号",
        "ja": "No.",
    },
    "payment_bold_link_label": {
        "es": "LINK DE PAGO BOLD",
        "en": "BOLD PAYMENT LINK",
        "fr": "LIEN DE PAIEMENT BOLD",
        "de": "BOLD-ZAHLUNGSLINK",
        "it": "LINK DI PAGAMENTO BOLD",
        "ru": "ССЫЛКА НА ОПЛАТУ BOLD",
        "zh": "BOLD 付款链接",
        "ja": "BOLD 支払いリンク",
    },
    "payment_bold_surcharge": {
        "es": "Comisión adicional",
        "en": "Additional surcharge",
        "fr": "Frais supplémentaires",
        "de": "Zusätzliche Gebühr",
        "it": "Commissione aggiuntiva",
        "ru": "Дополнительная комиссия",
        "zh": "附加费",
        "ja": "追加手数料",
    },
    "payment_step_2": {
        "es": "PASO 2. Enviar comprobante de pago por este mismo medio (WhatsApp).",
        "en": "STEP 2. Send the payment proof through this same channel (WhatsApp).",
        "fr": "ÉTAPE 2. Envoyez la preuve de paiement par ce même canal (WhatsApp).",
        "de": "SCHRITT 2. Senden Sie den Zahlungsbeleg über denselben Kanal (WhatsApp).",
        "it": "PASSO 2. Invia la prova di pagamento attraverso questo stesso canale (WhatsApp).",
        "ru": "ШАГ 2. Отправьте подтверждение оплаты через этот же канал (WhatsApp).",
        "zh": "步骤 2. 通过同一渠道（WhatsApp）发送付款凭证。",
        "ja": "ステップ 2. 同じチャネル（WhatsApp）で支払い証明を送信してください。",
    },
    "payment_step_3": {
        "es": "PASO 3. Registrar a cada participante en el formulario que te enviaremos.",
        "en": "STEP 3. Register each participant in the form we will send you.",
        "fr": "ÉTAPE 3. Inscrivez chaque participant dans le formulaire que nous vous enverrons.",
        "de": "SCHRITT 3. Registrieren Sie jeden Teilnehmer in dem Formular, das wir Ihnen zusenden werden.",
        "it": "PASSO 3. Registra ogni partecipante nel modulo che ti invieremo.",
        "ru": "ШАГ 3. Зарегистрируйте каждого участника в форме, которую мы вам отправим.",
        "zh": "步骤 3. 在我们将发送给您的表格中注册每位参与者。",
        "ja": "ステップ 3. お送りするフォームに各参加者を登録してください。",
    },
    # ── Pre-reservation response (create_reservation_draft) ──
    "pre_reservation_registered": {
        "es": "Pre-reserva registrada.",
        "en": "Pre-reservation registered.",
        "fr": "Pré-réservation enregistrée.",
        "de": "Vorreservierung registriert.",
        "it": "Pre-prenotazione registrata.",
        "ru": "Предварительное бронирование зарегистрировано.",
        "zh": "预预订已登记。",
        "ja": "仮予約が登録されました。",
    },
    "pre_reservation_summary_header": {
        "es": "Resumen:",
        "en": "Summary:",
    },
    "pre_reservation_field_experience": {
        "es": "Experiencia",
        "en": "Experience",
    },
    "pre_reservation_field_date": {
        "es": "Fecha",
        "en": "Date",
    },
    "pre_reservation_field_participants": {
        "es": "Personas",
        "en": "Participants",
    },
    "pre_reservation_field_amount": {
        "es": "Valor",
        "en": "Amount",
    },
    "pre_reservation_field_code": {
        "es": "Código",
        "en": "Code",
    },
    "pre_reservation_field_expires": {
        "es": "Vence",
        "en": "Expires",
    },
    "pre_reservation_confirm_steps": {
        "es": "Para confirmar la reserva sigue estos pasos:",
        "en": "To confirm your reservation, follow these steps:",
    },
    "pre_reservation_important_notice": {
        "es": "Importante: esta pre-reserva no está confirmada. Solo queda confirmada cuando un administrador verifica el pago y revalida la disponibilidad.",
        "en": "Important: this pre-reservation is not confirmed. It is only confirmed once an administrator verifies the payment and revalidates availability.",
    },
    # ── Payment proof (attach_payment_proof_to_reservation) ──
    "payment_proof_invalid_format": {
        "es": "El comprobante debe ser imagen (JPG/PNG) o PDF.",
        "en": "The proof must be an image (JPG/PNG) or PDF.",
    },
    "payment_proof_invalid_format_response": {
        "es": "Recibi tu archivo, pero el formato no es valido. Por favor envia una imagen (JPG/PNG) o PDF del comprobante.",
        "en": "I received your file, but the format is not valid. Please send an image (JPG/PNG) or PDF of the proof.",
    },
    "payment_proof_duplicate_short": {
        "es": "Comprobante ya recibido anteriormente; se mantiene en revision.",
        "en": "Proof already received previously; it remains under review.",
    },
    "payment_proof_duplicate_response": {
        "es": "Ya teniamos tu comprobante para la reserva {code}. Sigue en revision administrativa y la reserva aun no esta confirmada.",
        "en": "We already have your proof for reservation {code}. It is still under administrative review and the reservation is not yet confirmed.",
    },
    "payment_proof_received_short": {
        "es": "Comprobante recibido y en revision administrativa.",
        "en": "Proof received and under administrative review.",
    },
    "payment_proof_received_response": {
        "es": "Recibimos tu comprobante para la reserva {code}. Queda en revision administrativa y la reserva aun NO esta confirmada.",
        "en": "We received your proof for reservation {code}. It is under administrative review and the reservation is NOT yet confirmed.",
        "fr": "Nous avons reçu votre justificatif pour la réservation {code}. Il est en cours de vérification administrative et la réservation n'est PAS encore confirmée.",
        "de": "Wir haben Ihren Beleg für die Reservierung {code} erhalten. Er wird derzeit administrativ geprüft und die Reservierung ist NOCH NICHT bestätigt.",
        "it": "Abbiamo ricevuto la tua ricevuta per la prenotazione {code}. È in fase di revisione amministrativa e la prenotazione NON è ancora confermata.",
        "ru": "Мы получили ваше подтверждение оплаты для бронирования {code}. Оно проходит административную проверку, и бронирование пока НЕ подтверждено.",
        "zh": "我们已收到预订 {code} 的付款凭证。它正在行政审核中，预订尚未确认。",
        "ja": "ご予約 {code} の支払い確認を受け取りました。現在事務確認中で、ご予約はまだ確定していません。",
    },
    "payment_proof_unable_to_attach": {
        "es": "No pude asociar el comprobante. Verifica el codigo de reserva y que este aun este pendiente de confirmacion.",
        "en": "I could not attach the proof. Please verify the reservation code and that it is still pending confirmation.",
    },
    "payment_proof_unable_register": {
        "es": "No logramos registrar el comprobante en este momento. Intenta de nuevo o comparte el codigo de tu reserva.",
        "en": "We could not register the proof at this moment. Try again or share your reservation code.",
    },
    # ── get_payment_instructions ──
    "payment_instructions_bold_unavailable": {
        "es": "El pago por Bold no está disponible en este momento.",
        "en": "Bold payment is not available at this moment.",
    },
    "payment_instructions_follow_steps": {
        "es": "Para confirmar tu reserva sigue estos pasos:",
        "en": "To confirm your reservation, follow these steps:",
    },
    "payment_instructions_reservation_label": {
        "es": "Reserva:",
        "en": "Reservation:",
    },
    # ── get_reservation_public_summary ──
    "reservation_not_found_message": {
        "es": "No se encontró una pre-reserva con ese código.",
        "en": "No pre-reservation was found with that code.",
    },
    "reservation_not_found_by_phone": {
        "es": "No se encontró una reserva para ese teléfono.",
        "en": "No reservation was found for that phone number.",
    },
    # ── Client reservations (cancel/update errors) ──
    "client_reservation_cannot_cancel_paid": {
        "es": "Solo se pueden cancelar reservas con pago pendiente.",
        "en": "Only reservations with pending payment can be cancelled.",
    },
    "client_reservation_terminal_state": {
        "es": "No se puede modificar una reserva en estado terminal.",
        "en": "A reservation in a terminal state cannot be modified.",
    },
    "client_reservation_cannot_modify_paid": {
        "es": "Solo se pueden modificar reservas con pago pendiente.",
        "en": "Only reservations with pending payment can be modified.",
    },
    # ── Client reservations additional templates ──
    "client_reservation_not_found": {
        "es": "No encontré una reserva con ese código y teléfono.",
        "en": "I couldn't find a reservation with that code and phone.",
    },
    "client_reservation_cannot_cancel_paid_response": {
        "es": "Lo siento, solo puedo cancelar reservas que aún no tienen pago registrado. Si necesitas ayuda con esta reserva, te transfiero con un asesor.",
        "en": "Sorry, I can only cancel reservations that don't have a payment registered yet. If you need help with this reservation, I'll transfer you to an advisor.",
    },
    "client_reservation_cancelled_success": {
        "es": "Reserva cancelada exitosamente.",
        "en": "Reservation cancelled successfully.",
    },
    "client_reservation_cancelled_response": {
        "es": "Listo, tu reserva {code} ha sido cancelada. Si en algún momento quieres reprogramar, escríbeme y con gusto te ayudo.",
        "en": "Done, your reservation {code} has been cancelled. If at any point you want to reschedule, just write me and I'll gladly help.",
    },
    "client_reservation_unable_to_cancel": {
        "es": "No pude cancelar la reserva en este momento. Intenta de nuevo.",
        "en": "I couldn't cancel the reservation right now. Please try again.",
    },
    "client_reservation_unexpected_error": {
        "es": "Ocurrió un error inesperado. Intenta de nuevo en unos minutos.",
        "en": "An unexpected error occurred. Please try again in a few minutes.",
    },
    "client_reservation_date_updated_success": {
        "es": "Fecha de la reserva actualizada.",
        "en": "Reservation date updated.",
    },
    "client_reservation_date_updated_response": {
        "es": "Listo, cambié la fecha de tu reserva {code} para el {new_date}. Quedó pendiente de confirmacion por parte del equipo.",
        "en": "Done, I changed the date of your reservation {code} to {new_date}. It's pending confirmation by the team.",
    },
    "client_reservation_date_invalid": {
        "es": "La nueva fecha debe ser valida y posterior a hoy.",
        "en": "The new date must be valid and after today.",
    },
    "client_reservation_date_no_availability": {
        "es": "No hay disponibilidad para la nueva fecha. Elige otra por favor.",
        "en": "There's no availability for the new date. Please choose another.",
    },
    "client_reservation_participants_updated": {
        "es": "Numero de participantes actualizado.",
        "en": "Number of participants updated.",
    },
    "client_reservation_participants_updated_response": {
        "es": "Listo, actualice tu reserva {code} para {participants} participantes. El valor se ajusto a {amount} {currency}.",
        "en": "Done, I updated your reservation {code} to {participants} participants. The amount was adjusted to {amount} {currency}.",
    },
    "client_reservation_participants_out_of_range": {
        "es": "El numero de participantes debe estar entre 1 y 8.",
        "en": "The number of participants must be between 1 and 8.",
    },
    "client_reservation_terminal_state_response": {
        "es": "Lo siento, esta reserva ya no puede modificarse porque está finalizada o cancelada.",
        "en": "Sorry, this reservation can no longer be modified because it is finished or cancelled.",
    },
    "client_reservation_cannot_modify_paid_response": {
        "es": "Lo siento, solo puedo modificar reservas que aún no tienen pago registrado. Si necesitas cambiar una reserva con pago confirmado, te transfiero con un asesor.",
        "en": "Sorry, I can only modify reservations that don't have a payment registered yet. If you need to change a reservation with confirmed payment, I'll transfer you to an advisor.",
    },
    "client_reservation_date_updated_short": {
        "es": "Fecha actualizada exitosamente.",
        "en": "Date updated successfully.",
    },
    "client_reservation_date_updated_message": {
        "es": "Perfecto, cambié la fecha de tu reserva {code} para el {new_date}. Todo sigue igual.",
        "en": "Perfect, I changed the date of your reservation {code} to {new_date}. Everything else stays the same.",
    },
    "client_reservation_date_unable": {
        "es": "No pude cambiar la fecha en este momento. Intenta de nuevo.",
        "en": "I couldn't change the date right now. Please try again.",
    },
    "client_reservation_participants_updated_short": {
        "es": "Cantidad de participantes actualizada exitosamente.",
        "en": "Number of participants updated successfully.",
    },
    "client_reservation_participants_unable": {
        "es": "No pude cambiar la cantidad de participantes en este momento. Intenta de nuevo.",
        "en": "I couldn't change the number of participants right now. Please try again.",
    },
    # ── Idioma no soportado ──
    "unsupported_language_message": {
        "es": "Por ahora solo puedo atenderte en estos idiomas: {supported}. Si me escribes en cualquiera de ellos, con gusto te ayudo.",
        "en": "Right now I can only assist you in these languages: {supported}. If you write to me in any of them, I'll be happy to help.",
        "fr": "Pour l'instant, je ne peux vous aider qu'en : {supported}. Si vous m'écrivez dans l'une de ces langues, je serai ravi de vous aider.",
        "de": "Im Moment kann ich Sie nur in diesen Sprachen unterstützen: {supported}. Wenn Sie mir in einer davon schreiben, helfe ich gerne weiter.",
        "it": "Al momento posso assisterti solo in queste lingue: {supported}. Se mi scrivi in una di esse, sarò felice di aiutarti.",
        "ru": "Сейчас я могу помочь вам только на этих языках: {supported}. Если вы напишете мне на одном из них, я с радостью помогу.",
        "zh": "目前我只能使用以下语言为您服务：{supported}。如果您使用其中任何一种语言给我写信，我将很乐意为您提供帮助。",
        "ja": "現在、以下の言語のみで対応できます：{supported}。いずれかでメッセージをお送りいただければ、お手伝いいたします。",
    },
    "language_name_es": {
        "es": "español", "en": "Spanish", "fr": "espagnol", "de": "Spanisch",
        "it": "spagnolo", "ru": "испанский", "zh": "西班牙语", "ja": "スペイン語",
    },
    "language_name_en": {
        "es": "inglés", "en": "English", "fr": "anglais", "de": "Englisch",
        "it": "inglese", "ru": "английский", "zh": "英语", "ja": "英語",
    },
    "language_name_fr": {
        "es": "francés", "en": "French", "fr": "français", "de": "Französisch",
        "it": "francese", "ru": "французский", "zh": "法语", "ja": "フランス語",
    },
    "language_name_de": {
        "es": "alemán", "en": "German", "fr": "allemand", "de": "Deutsch",
        "it": "tedesco", "ru": "немецкий", "zh": "德语", "ja": "ドイツ語",
    },
    "language_name_it": {
        "es": "italiano", "en": "Italian", "fr": "italien", "de": "Italienisch",
        "it": "italiano", "ru": "итальянский", "zh": "意大利语", "ja": "イタリア語",
    },
    "language_name_ru": {
        "es": "ruso", "en": "Russian", "fr": "russe", "de": "Russisch",
        "it": "russo", "ru": "русский", "zh": "俄语", "ja": "ロシア語",
    },
    "language_name_zh": {
        "es": "chino", "en": "Chinese", "fr": "chinois", "de": "Chinesisch",
        "it": "cinese", "ru": "китайский", "zh": "中文", "ja": "中国語",
    },
    "language_name_ja": {
        "es": "japonés", "en": "Japanese", "fr": "japonais", "de": "Japanisch",
        "it": "giapponese", "ru": "японский", "zh": "日语", "ja": "日本語",
    },
    "language_switched": {
        "es": "Perfecto, seguimos en español. ¿En qué te ayudo?",
        "en": "Perfect, we'll continue in English. How can I help you?",
        "fr": "Parfait, on continue en français. Comment puis-je vous aider ?",
        "de": "Perfekt, wir machen auf Deutsch weiter. Womit kann ich helfen?",
        "it": "Perfetto, continuiamo in italiano. Come posso aiutarti?",
        "ru": "Отлично, продолжаем на русском. Чем могу помочь?",
        "zh": "好的，我们用中文继续。需要我帮您什么？",
        "ja": "承知しました。日本語で続けます。どのようにお手伝いできますか？",
    },
}


def t(key: str, language: str, **fmt: str) -> str:
    supported = {"es", "en", "fr", "de", "it", "ru", "zh", "ja"}
    lang = language if language in supported else "en"
    translations = _MESSAGES.get(key, {})
    msg = translations.get(lang) or translations.get("en") or translations.get("es") or key
    if fmt:
        try:
            return msg.format(**fmt)
        except (KeyError, IndexError):
            return msg
    return msg


_LANGUAGE_NAMES: dict[str, str] = {
    "es": "español",
    "en": "inglés",
    "fr": "francés",
    "de": "alemán",
    "it": "italiano",
    "ru": "ruso",
    "zh": "chino",
    "ja": "japonés",
}

_LANGUAGE_TONE: dict[str, str] = {
    "es": (
        "Mantén un tono cálido, amable y cercano.\n"
        "Habla natural: 'vale', 'cuesta', 'sale', 'tocaría', 'podemos', 'te parece'.\n"
        "Responde breve para WhatsApp, salvo listados o plantillas con varios ítems.\n"
        "Termina con una pregunta breve o invitación a continuar, "
        "salvo en human_handoff, listados o cierre por políticas.\n"
        "Si el tool_output ya trae precio o disponibilidad, NO pidas otra confirmación: "
        "pide nombre y correo o usa el response de la tool.\n"
    ),
    "en": (
        "Keep a warm, friendly, and approachable tone.\n"
        "Speak naturally: 'sure', 'got it', 'let me check', 'does that work?', 'no problem'.\n"
        "Keep it brief for WhatsApp, except for lists or multi-item templates.\n"
        "End with a short question or invitation to continue, "
        "unless it's a handoff, a catalog list, or a policy closure.\n"
        "If tool_output already has price or availability, do NOT ask another confirmation: "
        "ask for full name and email or use the tool response.\n"
    ),
    "fr": (
        "Ton chaleureux et naturel pour WhatsApp.\n"
        "Réponses brèves, sauf listes ou modèles multi-éléments.\n"
        "Si le tool_output a déjà un prix ou une disponibilité, ne demande pas une autre confirmation.\n"
    ),
    "de": (
        "Warmer, freundlicher Ton für WhatsApp.\n"
        "Kurz antworten, außer bei Listen oder Vorlagen mit mehreren Einträgen.\n"
        "Wenn tool_output bereits Preis oder Verfügbarkeit hat, keine weitere Bestätigung verlangen.\n"
    ),
    "it": (
        "Tono caldo e naturale per WhatsApp.\n"
        "Risposte brevi, tranne elenchi o template con più voci.\n"
        "Se tool_output ha già prezzo o disponibilità, non chiedere un'altra conferma.\n"
    ),
    "ru": (
        "Тёплый, дружелюбный тон для WhatsApp.\n"
        "Кратко, кроме списков и шаблонов с несколькими пунктами.\n"
        "Если в tool_output уже есть цена или доступность — не просите ещё одно подтверждение.\n"
    ),
    "zh": (
        "语气温暖友好，适合 WhatsApp。\n"
        "尽量简短，列表或多条目模板除外。\n"
        "如果 tool_output 已有价格或空位信息，不要再要求确认，直接要姓名和邮箱或使用工具回复。\n"
    ),
    "ja": (
        "WhatsApp向けに温かみのある自然な口調で。\n"
        "リストや複数項目のテンプレート以外は短めに。\n"
        "tool_output に価格や空きがある場合、追加の確認はせず名前とメールを聞くか tool の response を使う。\n"
    ),
}


def build_language_instruction(language: str) -> str:
    tone = _LANGUAGE_TONE.get(language, _LANGUAGE_TONE["en"])
    lang_name = _LANGUAGE_NAMES.get(language, "inglés")
    supported = (
        "Supported response languages: Spanish, English, French, German, "
        "Italian, Russian, Chinese, Japanese. NEVER say you only speak "
        "English or Spanish. NEVER refuse German, Chinese, French, Spanish, "
        "or any supported language. If the user asks to switch language, "
        "acknowledge and continue in that language — do not invent limitations."
    )
    if language == "en":
        return (
            "RESPONSE LANGUAGE: English (en).\n"
            "The user is in an English-language conversation. The user may write\n"
            "names, slang, or short phrases in other languages, but the conversation\n"
            "language is English. You MUST respond in English regardless of the\n"
            "language of the latest user message.\n"
            f"{tone}"
            f"{supported}\n"
        )
    return (
        f"IDIOMA DE RESPUESTA: {lang_name} ({language}).\n"
        f"El usuario está en una conversación en {lang_name}. El usuario puede\n"
        f"escribir nombres, jerga o frases cortas en otros idiomas, pero el\n"
        f"idioma de la conversación es {lang_name}. Debes responder SIEMPRE en\n"
        f"{lang_name}, sin importar el idioma del último mensaje del usuario.\n"
        f"{tone}"
        f"{supported}\n"
    )


_LANGUAGE_UPPER: dict[str, str] = {
    "es": "ESPAÑOL",
    "en": "INGLÉS",
    "fr": "FRANCÉS",
    "de": "ALEMÁN",
    "it": "ITALIANO",
    "ru": "RUSO",
    "zh": "CHINO",
    "ja": "JAPONÉS",
}


def get_language_upper_token(language: str) -> str:
    """Token en mayúsculas para inyectar en prompts del composer."""
    return _LANGUAGE_UPPER.get(language, "INGLÉS")
