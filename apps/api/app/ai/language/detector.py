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


# Patrones de petición explícita de idioma. El orden importa: se evalúan de
# arriba a abajo y la primera coincidencia gana. Se prioriza español.
# Cada entrada: (patrón_regex, idioma_destino) — el destino ya está limitado a
# los idiomas con catálogo de respuestas (es/en).
_EXPLICIT_LANGUAGE_REQUESTS: list[tuple[str, str]] = [
    # Español explícito (prioridad).
    (
        r"\b(responde|respondeme|respóndeme|hablame|háblame|habla|escribeme|escríbeme"
        r"|contesta|contestame|contéstame)\b[^.\n]{0,40}"
        r"\b(español|espanol|castellano|spanish)\b",
        "es",
    ),
    (
        r"\b(quiero|prefiero|mejor|me\s+gustaría|me\s+gustaria)\b[^.\n]{0,30}"
        r"\b(en\s+)?(español|espanol|castellano)\b",
        "es",
    ),
    (
        r"\b(no\s+(me\s+)?(respondas|hables|contestes|escribas))\b[^.\n]{0,30}"
        r"(inglés|ingles|english|british)\b",
        "es",
    ),
    (
        r"\b(español|espanol|castellano|spanish)\b[^.\n]{0,30}"
        r"\b(por\s+favor|please|pls)\b",
        "es",
    ),
    (r"(?:^|\s)/(español|espanol|spanish)\b", "es"),

    # Inglés explícito.
    (
        r"\b(reply|respond|talk|write|answer|speak|chat)\b[^.\n]{0,40}"
        r"\b(in\s+)?(english|ingles|british)\b",
        "en",
    ),
    (r"\b(español|espanol|castellano|spanish)\b[^.\n]{0,30}\b(no)\b", "en"),
    (
        r"\b(no\s+(me\s+)?(respondas|hables|contestes|escribas))\b[^.\n]{0,30}"
        r"(español|espanol|castellano)\b",
        "en",
    ),
    (
        r"\b(i\s+(want|prefer|would\s+like|need))\b[^.\n]{0,30}"
        r"\b(in\s+)?(english|ingles)\b",
        "en",
    ),
    (
        r"\b(quiero|prefiero|mejor|me\s+gustaría|me\s+gustaria)\b[^.\n]{0,30}"
        r"\b(en\s+)?(inglés|ingles|english)\b",
        "en",
    ),
    (r"(?:^|\s)/(english|ingles?)\b", "en"),
]


def _normalize_response_language(lang: str) -> str:
    """Mapea cualquier idioma al catálogo de respuestas disponible (es/en)."""
    return lang if lang in RESPONSE_LANGUAGES else "en"


def detect_explicit_language_request(text: str) -> str | None:
    """Reconoce una petición explícita del usuario de cambiar/respetar un idioma.

    Devuelve 'es' o 'en' si detecta una instrucción explícita, o ``None`` si el
    mensaje no es una petición de idioma. La detección es intencionalmente
    estricta para evitar falsos positivos en español (ej: 'en español' suelto
    en cualquier oración se interpreta como petición solo si está cerca de un
    verbo imperativo o expresión de preferencia).
    """
    if not text or not text.strip():
        return None
    lower = text.lower().strip()
    if len(lower) < 4:
        return None
    for pattern, lang in _EXPLICIT_LANGUAGE_REQUESTS:
        if re.search(pattern, lower):
            return lang
    return None


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