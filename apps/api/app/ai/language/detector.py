import re

from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0

SUPPORTED_LANGUAGES: set[str] = {"es", "en", "fr", "pt", "de", "it", "nl"}
# Idiomas soportados como destino de respuestas (catálogo de mensajes).
# Solo hay catálogo es/en; el resto se mapea a "en" vía messages.t().
RESPONSE_LANGUAGES: set[str] = {"es", "en"}

# Strong Spanish indicators — if any match, prefer Spanish over similar languages (pt, fr, it)
_SPANISH_INDICATORS = [
    r"\bes\b", r"\bla\b", r"\blos\b", r"\blas\b", r"\bun\b", r"\buna\b", r"\bunos\b", r"\bunas\b",
    r"\busted\b", r"\bestá\b", r"\bestán\b", r"\bhay\b", r"\bser\b", r"\bestar\b",
    r"\bqué\b", r"\bcuál\b", r"\bcómo\b", r"\bcuándo\b", r"\bcuánto\b",
    r"\bhola\b", r"\bgracias\b", r"\bpor favor\b", r"\bbueno\b",
    r"\bquería\b", r"\bquisiera\b", r"\bpuedes\b", r"\bpuedo\b",
]

_MIN_LENGTH_FOR_DETECT = 4

# Tokens de mensajería comunes que NO deben disparar detección de idioma: son
# ambiguos o se usan por convención independiente del idioma.
_NEUTRAL_TOKENS = {
    "ok", "okay", "ok.", "ok!", "si", "sí", "no", "yes", "yeah", "vale",
    "dale", "listo", "👍", "y", "mhm", "mm", "jaja", "haha",
    "si?", "sí?", "no?", "ok?", "k", "kk", "thx", "thanks", "gracias",
}


def _has_spanish_indicators(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in _SPANISH_INDICATORS)


def detect_language(text: str, previous_language: str = "es") -> str:
    """Detecta el idioma de un texto aislado.

    - Texto vacío o muy corto → mantiene ``previous_language``.
    - Palabras neutras de mensajería solas → mantiene ``previous_language``.
    - Indicadores fuertes de español → fuerza español (prioridad).
    - Si el ``previous_language`` es español y se detecta un idioma cercano
      (pt/fr/it) sin indicadores españoles, se mantiene español para evitar
      oscilaciones por similitud lingüística.
    - Idiomas fuera del conjunto soportado → fallback a inglés.
    """
    if not text or not text.strip():
        return previous_language
    stripped = text.strip()

    if len(stripped) < _MIN_LENGTH_FOR_DETECT:
        return previous_language

    lowered = stripped.lower()

    # Tokens neutrales de mensajería: no son evidencia suficiente de idioma.
    if lowered in _NEUTRAL_TOKENS or all(tok in _NEUTRAL_TOKENS for tok in lowered.split()):
        return previous_language

    if _has_spanish_indicators(stripped):
        return "es"

    try:
        lang = detect(stripped)
    except LangDetectException:
        return previous_language

    if previous_language == "es" and lang in ("pt", "fr", "it"):
        return previous_language
    return lang if lang in SUPPORTED_LANGUAGES else "en"


# Umbral de mensajes consecutivos en otro idioma antes de cambiar el idioma
# efectivo de la sesión. Ver ADR de política de idioma del bot.
LANGUAGE_CHANGE_STREAK: int = 3


def detect_language_stable(
    current_message: str,
    previous_messages: list[str] | None = None,
    session_language: str = "es",
) -> str:
    """Detecta el idioma del mensaje actual tratando cada mensaje de forma
    independiente (sin encadenar el idioma detectado entre mensajes).

    El ``session_language`` actúa únicamente como:
      - idioma por defecto para mensajes vacíos/cortos/neutros;
      - sesgo fuerte hacia español cuando es el idioma actual.

    La estabilidad real (umbral de cambio) la gestiona :func:`decide_language`,
    no esta función. Aquí solo normalizamos la detección por mensaje.
    """
    current_lang = detect_language(current_message, session_language)

    # Votación simple sobre el mensaje actual y (opcional) los previos.
    # Cada mensaje se detecta de forma independiente usando ``session_language``
    # como fallback, sin propagar el resultado de un mensaje al siguiente.
    candidates: list[str] = [current_lang] if current_lang else []
    if previous_messages:
        for msg in previous_messages[-5:]:
            pl = detect_language(msg, session_language)
            if pl:
                candidates.append(pl)

    if not candidates:
        return session_language

    counts: dict[str, int] = {}
    for lang in candidates:
        counts[lang] = counts.get(lang, 0) + 1

    # Empate o mayoría: se respeta el recuento. En caso de empate con el
    # idioma de sesión, se conserva el de sesión para favorecer estabilidad.
    sorted_langs = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    top_lang, top_count = sorted_langs[0]
    session_count = counts.get(session_language, 0)
    if top_count == session_count and session_count > 0:
        return session_language
    return top_lang


# Catálogo de idiomas soportados por el bot.
SUPPORTED_RESPONSE_LANGUAGES: set[str] = {"es", "en", "fr", "de", "it", "ru", "zh", "ja"}

# Mapa de nombres nativos y aliases de cada idioma soportado.
_LANGUAGE_KEYWORDS: dict[str, set[str]] = {
    "es": {"español", "espanol", "castellano", "spanish", "esp"},
    "en": {"inglés", "ingles", "english", "anglo", "british"},
    "fr": {"francés", "frances", "french", "francais", "français"},
    "de": {"alemán", "aleman", "german", "deutsch", "deutsche"},
    "it": {"italiano", "italian", "italiana"},
    "ru": {"ruso", "russian", "ruski", "russkiy", "русский"},
    "zh": {"chino", "chinese", "mandarin", "mandarín", "中文", "zhongwen"},
    "ja": {"japonés", "japones", "japanese", "japones", "日本語", "nihongo"},
}

# Palabras de petición (verbos / expresiones de preferencia) en varios idiomas.
_INTENT_VERBS = (
    r"responde|respondeme|respóndeme|hablame|háblame|habla|escribeme|escríbeme"
    r"|contesta|contestame|contéstame|cambia|cambiar|usa|utiliza|continua|continuar"
    r"|quiero|prefiero|mejor|me\s+gustaría|me\s+gustaria|deseo|necesito"
    r"|puedes|podrias|podrías|sigue|seguir|esta|esta\s+conversación|conversacion"
    r"|i\s+(want|prefer|would\s+like|need|wish)"
    r"|please|can\s+you|could\s+you|reply|talk|speak|write|answer|chat|continue|switch|use"
    r"|parle|parles|parlez|parlare|parli|parlami|rispondi|risponde"
    r"|sprich|sprichst|sprechen|schreib|schreibe|antworten"
    r"|voglio|vorrei|preferisco"
    r"|je\s+(veux|voudrais|préfère|parle|continue)"
    r"|in\s+english|in\s+spanish|in\s+french|in\s+german|in\s+italian"
)

# Patrones de petición explícita de idioma. El orden importa: se evalúan de
# arriba a abajo y la primera coincidencia gana. Devuelven el código del
# idioma (soportado o no). Si el código no está en SUPPORTED_RESPONSE_LANGUAGES,
# el caller debe responder con el mensaje "unsupported_language".
def _build_lang_pattern(verb_part: str, lang_words: set[str]) -> str:
    words_alt = "|".join(re.escape(w) for w in sorted(lang_words, key=len, reverse=True))
    return rf"\b(?:{verb_part})\b[^.\n]{{0,50}}\b(?:en\s+|a\s+|al\s+|in\s+)?(?:{words_alt})\b"


def _detect_explicit_request_supported(text: str) -> str | None:
    """Detecta peticiones de idioma soportado. Devuelve el código o None."""
    if not text or not text.strip():
        return None
    lower = text.lower().strip()
    if len(lower) < 4:
        return None
    # Construimos un patrón por idioma (verb + palabras de ese idioma).
    for lang_code, lang_words in _LANGUAGE_KEYWORDS.items():
        pattern = _build_lang_pattern(_INTENT_VERBS, lang_words)
        if re.search(pattern, lower, flags=re.IGNORECASE):
            return lang_code
    # Slash commands: "/ingles", "/english", etc.
    for lang_code, lang_words in _LANGUAGE_KEYWORDS.items():
        words_alt = "|".join(re.escape(w) for w in sorted(lang_words, key=len, reverse=True))
        if re.search(rf"(?:^|\s)/(?:{words_alt})\b", lower, flags=re.IGNORECASE):
            return lang_code
    # Fallback: mensajes cortos que son SOLO el nombre del idioma
    # (e.g. "frances", "italiano", "en aleman"). Útil cuando el usuario
    # responde a "¿en qué idioma?" con el nombre del idioma.
    stripped = lower.strip(" .,!?")
    for lang_code, lang_words in _LANGUAGE_KEYWORDS.items():
        if stripped in lang_words:
            return lang_code
    return None


def _detect_explicit_request_any(text: str) -> str | None:
    """Detecta peticiones de idioma INCLUYENDO no soportados.

    Útil para informar al usuario qué idiomas SÍ soportamos.
    """
    if not text or not text.strip():
        return None
    lower = text.lower().strip()
    if len(lower) < 4:
        return None
    # Buscamos cualquier palabra reconocible como idioma, con o sin verbo.
    # Palabras comunes de muchos idiomas (no soportados).
    extra_keywords = {
        "ar": {"árabe", "arabe", "arabic"},
        "ko": {"coreano", "korean"},
        "pt": {"portugués", "portugues", "portuguese"},
        "nl": {"holandés", "holandes", "dutch", "neerlandés"},
        "sv": {"sueco", "swedish"},
        "tr": {"turco", "turkish"},
        "pl": {"polaco", "polish"},
        "hi": {"hindi", "hindustani"},
    }
    all_langs = dict(_LANGUAGE_KEYWORDS)
    all_langs.update(extra_keywords)
    pattern = _build_lang_pattern(_INTENT_VERBS, set().union(*all_langs.values()))
    m = re.search(pattern, lower, flags=re.IGNORECASE)
    if m:
        matched_word = m.group(0).lower()
        for code, words in all_langs.items():
            if any(w in matched_word for w in words):
                return code
    return None


def detect_explicit_language_request(text: str) -> str | None:
    """Reconoce una petición explícita del usuario de cambiar a un idioma.

    Devuelve:
      - código de idioma soportado (es, en, fr, de, it, ru, zh, ja) si el
        usuario pidió uno de los soportados;
      - "unsupported" si pidió un idioma que NO soportamos;
      - None si el mensaje no es una petición de idioma.
    """
    supported = _detect_explicit_request_supported(text)
    if supported:
        return supported
    if _detect_explicit_request_any(text):
        return "unsupported"
    return None


def _normalize_response_language(lang: str) -> str:
    """Mapea cualquier idioma al catálogo de respuestas disponible."""
    if lang in SUPPORTED_RESPONSE_LANGUAGES:
        return lang
    return "en"


def decide_language(
    *,
    session_language: str,
    language_override: str | None,
    streak: int,
    streak_lang: str | None,
    current_detection: str,
) -> tuple[str, int, str | None]:
    """Aplica la política de estabilidad del idioma efectivo de la sesión.

    Reglas:
      1. Si existe ``language_override`` (petición explícita previa, persistente),
         el idioma efectivo es ese override y no se actualiza la racha.
      2. Si la detección del mensaje actual coincide con el idioma efectivo →
         la racha se reinicia a 0.
      3. Si la detección coincide con ``streak_lang`` → la racha sube en 1.
      4. Si la detección es un idioma distinto → arranca nueva racha en 1 con
         ese idioma como ``streak_lang``.
      5. Cuando la racha alcanza :data:`LANGUAGE_CHANGE_STREAK`, se cambia el
         idioma efectivo a ``streak_lang`` y se reinicia la racha.
      6. La detección que llega aquí ya está mapeada a catálogo de respuestas
         (es/en) por el llamador; esta función no redefine el conjunto.

    Devuelve ``(new_session_language, new_streak, new_streak_lang)``.
    """
    effective = _normalize_response_language(
        language_override if language_override else session_language
    )

    if language_override:
        # Override persistente: el auto-detección no actúa.
        return effective, streak, streak_lang

    current = _normalize_response_language(current_detection)

    if current == effective:
        return effective, 0, current

    # current != effective: acumular o arrancar racha hacia current.
    if streak_lang == current:
        new_streak = streak + 1
    else:
        new_streak = 1
        streak_lang = current

    if new_streak >= LANGUAGE_CHANGE_STREAK:
        # Cambio efectivo de idioma: la racha se reinicia desde 0 en el nuevo
        # idioma, ya que ahora current se vuelve el idioma efectivo.
        return current, 0, current

    return effective, new_streak, streak_lang