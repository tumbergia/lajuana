"""Tests para los templates bilingües de payment proof y pre-reserva."""

from __future__ import annotations

from app.ai.language.messages import t


def test_t_payment_proof_templates_bilingual() -> None:
    keys = [
        "payment_proof_invalid_format",
        "payment_proof_invalid_format_response",
        "payment_proof_duplicate_short",
        "payment_proof_duplicate_response",
        "payment_proof_received_short",
        "payment_proof_received_response",
        "payment_proof_unable_to_attach",
        "payment_proof_unable_register",
    ]
    for key in keys:
        es = t(key, "es")
        en = t(key, "en")
        assert es and en, f"Missing translation for {key}"
        assert es != en, f"Same translation for {key}: {es!r}"


def test_t_pre_reservation_templates_bilingual() -> None:
    keys = [
        "pre_reservation_registered",
        "pre_reservation_summary_header",
        "pre_reservation_field_experience",
        "pre_reservation_field_date",
        "pre_reservation_field_participants",
        "pre_reservation_field_amount",
        "pre_reservation_field_code",
        "pre_reservation_field_expires",
        "pre_reservation_confirm_steps",
        "pre_reservation_important_notice",
    ]
    for key in keys:
        es = t(key, "es")
        en = t(key, "en")
        assert es and en, f"Missing translation for {key}"
        assert es != en, f"Same translation for {key}"


def test_t_client_reservation_templates_bilingual() -> None:
    keys = [
        "client_reservation_not_found",
        "client_reservation_cannot_cancel_paid",
        "client_reservation_cannot_cancel_paid_response",
        "client_reservation_cancelled_success",
        "client_reservation_cancelled_response",
        "client_reservation_terminal_state",
        "client_reservation_terminal_state_response",
        "client_reservation_cannot_modify_paid",
        "client_reservation_cannot_modify_paid_response",
        "client_reservation_date_updated_short",
        "client_reservation_date_updated_message",
        "client_reservation_participants_updated",
        "client_reservation_participants_updated_response",
    ]
    for key in keys:
        es = t(key, "es")
        en = t(key, "en")
        assert es and en, f"Missing translation for {key}"


def test_payment_proof_duplicate_response_includes_code() -> None:
    """El template de duplicate debe aceptar {code}."""
    out = t("payment_proof_duplicate_response", "es", code="PR-001")
    assert "PR-001" in out
    out_en = t("payment_proof_duplicate_response", "en", code="PR-001")
    assert "PR-001" in out_en
    assert "reservation" in out_en.lower()


def test_payment_proof_received_response_includes_code() -> None:
    out = t("payment_proof_received_response", "es", code="PR-XYZ")
    assert "PR-XYZ" in out
    out_en = t("payment_proof_received_response", "en", code="PR-XYZ")
    assert "PR-XYZ" in out_en
    assert "review" in out_en.lower() or "received" in out_en.lower()


def test_client_reservation_cancelled_response_includes_code() -> None:
    out = t("client_reservation_cancelled_response", "es", code="PR-001")
    assert "PR-001" in out
    out_en = t("client_reservation_cancelled_response", "en", code="PR-001")
    assert "PR-001" in out_en
    assert "cancel" in out_en.lower()


def test_pre_reservation_field_translations_dont_match() -> None:
    """Sanity check: las traducciones de campos son diferentes."""
    fields = [
        "pre_reservation_field_experience",
        "pre_reservation_field_date",
        "pre_reservation_field_participants",
        "pre_reservation_field_amount",
        "pre_reservation_field_code",
        "pre_reservation_field_expires",
    ]
    for field in fields:
        es = t(field, "es")
        en = t(field, "en")
        assert es != en, f"{field} translates to same string: {es!r}"
