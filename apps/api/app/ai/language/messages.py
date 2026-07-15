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
    },
    "payment_methods_header": {
        "es": "Medios de pago disponibles:",
        "en": "Available payment methods:",
    },
    "payment_account_label": {
        "es": "CUENTA",
        "en": "ACCOUNT",
    },
    "payment_account_number": {
        "es": "No.",
        "en": "No.",
    },
    "payment_bold_link_label": {
        "es": "LINK DE PAGO BOLD",
        "en": "BOLD PAYMENT LINK",
    },
    "payment_bold_surcharge": {
        "es": "Comisión adicional",
        "en": "Additional surcharge",
    },
    "payment_step_2": {
        "es": "PASO 2. Enviar comprobante de pago por este mismo medio (WhatsApp).",
        "en": "STEP 2. Send the payment proof through this same channel (WhatsApp).",
    },
    "payment_step_3": {
        "es": "PASO 3. Registrar a cada participante en el formulario que te enviaremos.",
        "en": "STEP 3. Register each participant in the form we will send you.",
    },
    # ── Pre-reservation response (create_reservation_draft) ──
    "pre_reservation_registered": {
        "es": "Pre-reserva registrada.",
        "en": "Pre-reservation registered.",
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
}


def t(key: str, language: str, **fmt: str) -> str:
    lang = language if language in {"es", "en"} else "en"
    msg = _MESSAGES.get(key, {}).get(lang, _MESSAGES.get(key, {}).get("en", key))
    if fmt:
        return msg.format(**fmt)
    return msg


_LANGUAGE_NAMES: dict[str, str] = {
    "es": "español",
    "en": "inglés",
    "fr": "francés",
    "pt": "portugués",
    "de": "alemán",
    "it": "italiano",
    "nl": "neerlandés",
}

_LANGUAGE_TONE: dict[str, str] = {
    "es": (
        "Mantén un tono cálido, amable y cercano.\n"
        "Habla natural: 'vale', 'cuesta', 'sale', 'tocaría', 'podemos', 'te parece'.\n"
        "Responde breve para WhatsApp, máximo 2 oraciones.\n"
        "Termina SIEMPRE con una pregunta breve o invitación a continuar, "
        "salvo en human_handoff o cierre por políticas.\n"
    ),
    "en": (
        "Keep a warm, friendly, and approachable tone.\n"
        "Speak naturally: 'sure', 'got it', 'let me check', 'does that work?', 'no problem'.\n"
        "Keep it brief for WhatsApp, max 2 sentences.\n"
        "ALWAYS end with a short question or invitation to continue, "
        "unless it's a human handoff or policy closure.\n"
    ),
}


def build_language_instruction(language: str) -> str:
    tone = _LANGUAGE_TONE.get(language, _LANGUAGE_TONE["en"])
    lang_name = _LANGUAGE_NAMES.get(language, "inglés")
    if language == "en":
        return (
            "RESPONSE LANGUAGE: English (en).\n"
            "The user is writing in English.\n"
            "You MUST ALWAYS respond in English, in the same language as the user.\n"
            f"{tone}"
            "Exception: for unsupported languages, respond in English.\n"
        )
    return (
        f"IDIOMA DE RESPUESTA: {lang_name} ({language}).\n"
        f"El usuario está escribiendo en {lang_name}.\n"
        f"Debes responder SIEMPRE en {lang_name}, exactamente en el mismo idioma del usuario.\n"
        f"Si el usuario escribe en español, responde en español.\n"
        f"Si el usuario escribe en inglés, responde en inglés.\n"
        f"{tone}"
        "Excepción: para idiomas no soportados, responde en inglés.\n"
    )
