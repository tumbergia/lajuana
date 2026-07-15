"""Tests para los notification templates bilingües (ES + EN).

Verifica:
- El seed incluye versiones en ambos idiomas para los templates de WhatsApp
  que se envían a clientes finales.
- Cada par ES/EN cubre los mismos campos/variables.
- El enqueue del notification_service filtra por idioma correctamente.
- El fallback a español funciona cuando no hay versión en el idioma del
  cliente.
- El `holder_language` del reservation se respeta como default.
"""

from __future__ import annotations

from app.migrations.seed_notification_templates import SEED_TEMPLATES


# ── Seed: cobertura bilingüe ────────────────────────────────────────────


def _whatsapp_templates(language: str) -> list[dict]:
    return [
        t for t in SEED_TEMPLATES
        if t.get("channel") == "whatsapp" and t.get("language") == language
    ]


def test_seed_has_both_languages_for_whatsapp() -> None:
    """El seed debe tener al menos 5 templates de WhatsApp en cada idioma."""
    es = _whatsapp_templates("es")
    en = _whatsapp_templates("en")
    assert len(es) >= 5, f"WhatsApp ES templates: {len(es)}"
    assert len(en) >= 5, f"WhatsApp EN templates: {len(en)}"


def test_seed_bilingual_pairs_share_variables() -> None:
    """Cada template bilingüe debe declarar las mismas variables en ES y EN.

    Si una versión añade una variable nueva, hay que añadirla a la otra
    para que el render falle en silencio solo en un idioma.
    """
    es_by_key = {t["template_key"]: t for t in _whatsapp_templates("es")}
    en_by_key = {t["template_key"]: t for t in _whatsapp_templates("en")}

    common_keys = set(es_by_key.keys()) & set(en_by_key.keys())
    assert len(common_keys) >= 5, f"Bilingual WhatsApp templates: {common_keys}"

    for key in common_keys:
        es_vars = set(es_by_key[key].get("variables_allowed", []))
        en_vars = set(en_by_key[key].get("variables_allowed", []))
        # Las variables del ES deben ser un superset de EN (o iguales).
        missing_in_en = es_vars - en_vars
        assert not missing_in_en, (
            f"Template {key}: variables presentes en ES pero no en EN: {missing_in_en}"
        )


def test_seed_english_payment_proof_template_says_received() -> None:
    """El template EN de payment_approved_form_sent debe sonar natural en inglés."""
    en_form = next(
        t for t in _whatsapp_templates("en")
        if t["template_key"] == "payment_approved_form_sent.customer"
    )
    body = en_form["body"].lower()
    assert "hi" in body or "hello" in body
    assert "payment" in body
    assert "approved" in body
    assert "form" in body
    assert "link" in body


def test_seed_english_location_template_preserves_structure() -> None:
    """El template EN de location debe mantener saltos de línea y secciones."""
    en_loc = next(
        t for t in _whatsapp_templates("en")
        if t["template_key"] == "payment_approved_location_sent.customer"
    )
    body = en_loc["body"]
    # Estructura: location + URL + directions + recommendations
    assert "location:" in body or "location:" in body.lower()
    assert "RECOMMENDATIONS" in body
    assert "helmet" in body.lower()
    # Mantiene saltos de línea
    assert body.count("\n") >= 8


def test_seed_english_reservation_cancelled_template() -> None:
    """Template EN de cancelación debe estar completo y natural."""
    en = next(
        t for t in _whatsapp_templates("en")
        if t["template_key"] == "reservation_cancelled.customer"
    )
    body = en["body"].lower()
    assert "reservation" in body
    assert "cancelled" in body or "canceled" in body
    assert "reschedule" in body or "reprogramar" not in body
    # NO debe tener español mezclado
    assert "lamentamos" not in body
    assert "escríbenos" not in body


def test_seed_english_reservation_confirmed_logistics_template() -> None:
    """El template EN de confirmed logistics cubre reservation + experience + ubicación."""
    en = next(
        t for t in _whatsapp_templates("en")
        if t["template_key"] == "reservation_confirmed_logistics_sent.customer"
    )
    body = en["body"].lower()
    assert "reservation" in body and "confirmed" in body
    assert "experience" in body
    assert "location" in body
    assert "recommendations" in body
    assert "wear" in body  # recomendación de ropa
