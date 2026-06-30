from __future__ import annotations

from app.ai.language.detector import (
    LANGUAGE_CHANGE_STREAK,
    decide_language,
    detect_explicit_language_request,
    detect_language,
    detect_language_stable,
)

# ───────────────────────── detect_language (por mensaje) ────────────────────


def test_detect_language_keeps_previous_on_short_text() -> None:
    assert detect_language("ok", previous_language="es") == "es"
    assert detect_language("", previous_language="es") == "es"
    assert detect_language("   ", previous_language="en") == "en"


def test_detect_language_neutral_messaging_tokens_do_not_flip_language() -> None:
    # Tokens comunes de mensajería solos no deben disparar detección.
    assert detect_language("ok", previous_language="es") == "es"
    assert detect_language("sí", previous_language="es") == "es"
    assert detect_language("no", previous_language="es") == "es"  # noqa: E501
    assert detect_language("vale", previous_language="en") == "en"
    # "yes" aislado no debe flips si la sesión está en español
    assert detect_language("yes", previous_language="es") == "es"


def test_detect_language_spanish_indicator_forces_es_regardless_of_previous() -> None:
    assert detect_language("hola, quiero una reserva", previous_language="en") == "es"
    assert detect_language("cuántas personas somos", previous_language="en") == "es"


def test_detect_language_short_english_message_does_not_override_spanish() -> None:
    # Mensaje inglés corto y similar a romance no debe arrancar racha desde
    # la detección por mensaje; aquí sólo validamos que la detección aislada
    # cae a "en".
    assert detect_language("yes, that works", previous_language="es") == "en"


# ──────────────────── detect_language_stable (votación por mensaje) ─────────


def test_stable_keeps_spanish_with_english_message_among_spanish_history() -> None:
    history = ["hola quiero una reserva", "para cuatro personas", "qué experiences tienen"]
    out = detect_language_stable("yes that works", history, session_language="es")
    assert out == "es"


def test_stable_does_not_chain_prev_lang_chain_independence() -> None:
    # Antes el código encadenaba prev_lang propagando "en" a mensajes viejos.
    # Ahora cada mensaje se detecta con session_language como fallback, sin
    # propagar. El histórico en español debe seguir siendo español.
    history = ["hola", "gracias", "quería reservar", "para cinco"]
    out = detect_language_stable("please reply in english", history, session_language="es")
    assert out == "es"


# ────────────────────── detect_explicit_language_request ────────────────────


def test_explicit_spanish_request_detected() -> None:
    assert detect_explicit_language_request("respóndeme en español por favor") == "es"
    assert detect_explicit_language_request("háblame en español") == "es"
    assert detect_explicit_language_request("quiero que me responds en español") == "es"
    assert detect_explicit_language_request("no me respondas en inglés") == "es"
    assert detect_explicit_language_request("/español") == "es"


def test_explicit_english_request_detected() -> None:
    assert detect_explicit_language_request("please reply in english") == "en"
    assert detect_explicit_language_request("speak english please") == "en"
    assert detect_explicit_language_request("quiero que me respondas en inglés") == "en"
    assert detect_explicit_language_request("no me respondas en español") == "en"
    assert detect_explicit_language_request("/english") == "en"


def test_explicit_no_request_returns_none() -> None:
    assert detect_explicit_language_request("quiero una reserva para mañana") is None
    assert detect_explicit_language_request("ok") is None
    assert detect_explicit_language_request("") is None
    # Frases casuales que mencionan idioma sin petición explícita:
    assert detect_explicit_language_request("el curso de inglés me gustó") is None


# ─────────────────────────────── decide_language ─────────────────────────────


def test_decide_override_blocks_auto_detection() -> None:
    # Override persistente: cualquier detección se ignora.
    lang, streak, streak_lang = decide_language(
        session_language="es",
        language_override="en",
        streak=99,
        streak_lang="en",
        current_detection="es",
    )
    assert lang == "en"
    assert streak == 99  # no se actualiza
    assert streak_lang == "en"


def test_decide_keeps_language_when_detection_matches_effective() -> None:
    lang, streak, streak_lang = decide_language(
        session_language="es",
        language_override=None,
        streak=2,
        streak_lang="en",
        current_detection="es",
    )
    assert lang == "es"
    assert streak == 0
    assert streak_lang == "es"


def test_decide_starts_new_streak_on_different_language() -> None:
    lang, streak, streak_lang = decide_language(
        session_language="es",
        language_override=None,
        streak=0,
        streak_lang="es",
        current_detection="en",
    )
    assert lang == "es"  # todavía no cambia (streak=1 < 3)
    assert streak == 1
    assert streak_lang == "en"


def test_decide_accumulates_streak_and_does_not_change_until_threshold() -> None:
    session_language = "es"
    override = None
    streak = 0
    streak_lang = None

    # Mensaje 1 en inglés
    lang, streak, streak_lang = decide_language(
        session_language=session_language, language_override=override,
        streak=streak, streak_lang=streak_lang, current_detection="en",
    )
    assert lang == "es"
    assert streak == 1
    assert streak_lang == "en"

    # Mensaje 2 en inglés
    lang, streak, streak_lang = decide_language(
        session_language=session_language, language_override=override,
        streak=streak, streak_lang=streak_lang, current_detection="en",
    )
    assert lang == "es"
    assert streak == 2
    assert streak_lang == "en"

    # Mensaje 3 en inglés → cambia al umbral
    lang, streak, streak_lang = decide_language(
        session_language=session_language, language_override=override,
        streak=streak, streak_lang=streak_lang, current_detection="en",
    )
    assert lang == "en"
    assert streak == 0  # se reinicia tras cambio
    assert streak_lang == "en"


def test_decide_resets_streak_when_reverting_to_session_language() -> None:
    lang, streak, streak_lang = decide_language(
        session_language="es",
        language_override=None,
        streak=2,
        streak_lang="en",
        current_detection="es",
    )
    assert lang == "es"
    assert streak == 0
    assert streak_lang == "es"


def test_threshold_value_is_three() -> None:
    assert LANGUAGE_CHANGE_STREAK == 3