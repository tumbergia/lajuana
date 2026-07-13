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
