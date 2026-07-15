"""Tests para los templates bilingües de payment messages (Capa 1.2 + 1.3)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.language.messages import t
from app.schemas.config import PaymentInstructionsSchema
from app.services.payment_message_service import render_payment_steps


def _full_config() -> PaymentInstructionsSchema:
    return PaymentInstructionsSchema(
        manual_transfer_enabled=True,
        account_bank="Bancolombia",
        account_type="Ahorros",
        account_number="7165 1544 758",
        account_holder_name="Jairo Ramirez",
        account_holder_id="CC 10288647",
        transfer_note="Envia el comprobante con el codigo",
        bold_enabled=True,
        bold_checkout_url="https://example.com/pay",
        bold_surcharge_percent=7.0,
        bold_note="Comision adicional",
    )


def test_render_payment_steps_spanish() -> None:
    out = render_payment_steps(_full_config(), "es")
    assert "PASO 1" in out
    assert "PASO 2" in out
    assert "PASO 3" in out
    assert "Medios de pago disponibles" in out
    assert "CUENTA" in out
    assert "BANCOLOMBIA" in out
    assert "AHORROS" in out
    assert "No." in out
    assert "7165 1544 758" in out
    assert "Jairo Ramirez" in out
    assert "LINK DE PAGO BOLD" in out
    assert "Comisión adicional" in out
    assert "Envia el comprobante" in out  # transfer_note (data, no se traduce)


def test_render_payment_steps_english() -> None:
    out = render_payment_steps(_full_config(), "en")
    assert "STEP 1" in out
    assert "STEP 2" in out
    assert "STEP 3" in out
    assert "Available payment methods" in out
    assert "ACCOUNT" in out
    assert "BANCOLOMBIA" in out
    assert "AHORROS" in out
    assert "No." in out
    assert "7165 1544 758" in out
    assert "Jairo Ramirez" in out
    assert "BOLD PAYMENT LINK" in out
    assert "Additional surcharge" in out
    assert "Envia el comprobante" in out  # transfer_note (data)


def test_render_payment_steps_default_language_is_spanish() -> None:
    """Si no se pasa language, debe ser español."""
    out_es = render_payment_steps(_full_config(), "es")
    out_default = render_payment_steps(_full_config())
    assert out_es == out_default


def test_render_payment_steps_only_manual() -> None:
    cfg = _full_config()
    cfg.bold_enabled = False
    out = render_payment_steps(cfg, "en")
    assert "STEP 1" in out
    assert "ACCOUNT" in out
    assert "BOLD" not in out


def test_render_payment_steps_only_bold() -> None:
    cfg = _full_config()
    cfg.manual_transfer_enabled = False
    out = render_payment_steps(cfg, "en")
    assert "STEP 1" in out
    assert "BOLD PAYMENT LINK" in out
    assert "ACCOUNT" not in out


def test_render_payment_steps_neither_method() -> None:
    """Edge case: no hay medios de pago configurados."""
    cfg = _full_config()
    cfg.manual_transfer_enabled = False
    cfg.bold_enabled = False
    out = render_payment_steps(cfg, "en")
    # Debe tener los pasos pero sin métodos numerados.
    assert "STEP 1" in out
    assert "STEP 2" in out
    assert "STEP 3" in out
    assert "BOLD" not in out
    assert "ACCOUNT" not in out


def test_t_payment_step_templates_exist_for_both_languages() -> None:
    """Verifica que todos los templates de payment tienen ambas traducciones."""
    keys = [
        "payment_step_1_header",
        "payment_step_2",
        "payment_step_3",
        "payment_methods_header",
        "payment_account_label",
        "payment_bold_link_label",
        "payment_bold_surcharge",
        "payment_instructions_bold_unavailable",
        "payment_instructions_follow_steps",
        "payment_instructions_reservation_label",
    ]
    for key in keys:
        es = t(key, "es")
        en = t(key, "en")
        assert es and en, f"Missing translation for {key}"
        assert es != en, f"Same translation for {key}: {es!r}"

    # 'No.' (payment_account_number) es la misma abreviatura en es/en.
    assert t("payment_account_number", "es") == t("payment_account_number", "en") == "No."


@pytest.mark.asyncio
async def test_payment_instructions_message_includes_reservation_code() -> None:
    """El campo reservation_code debe aparecer en el mensaje."""
    from app.ai.mcp.tools import payment_instructions as pi_module

    cfg = _full_config()

    mock_container = MagicMock()
    mock_container.config_service.get_payment_instructions = AsyncMock(return_value=cfg)

    mock_log_class = MagicMock()
    mock_log_instance = MagicMock()
    mock_log_instance.insert = AsyncMock()
    mock_log_class.return_value = mock_log_instance

    with patch.object(pi_module, "Container") as mock_container_ref, \
         patch.object(pi_module, "ToolCallLogDocument", mock_log_class):
        mock_container_ref.get_instance = MagicMock(return_value=mock_container)
        result = await pi_module.get_payment_instructions(
            reservation_code="PR-20260601-ABC",
            language="en",
        )

    assert "PR-20260601-ABC" in result["response"]
    assert "STEP" in result["response"]
    assert "Reservation:" in result["response"]


@pytest.mark.asyncio
async def test_payment_instructions_spanish_includes_reservation_code() -> None:
    from app.ai.mcp.tools import payment_instructions as pi_module

    cfg = _full_config()

    mock_container = MagicMock()
    mock_container.config_service.get_payment_instructions = AsyncMock(return_value=cfg)

    mock_log_class = MagicMock()
    mock_log_instance = MagicMock()
    mock_log_instance.insert = AsyncMock()
    mock_log_class.return_value = mock_log_instance

    with patch.object(pi_module, "Container") as mock_container_ref, \
         patch.object(pi_module, "ToolCallLogDocument", mock_log_class):
        mock_container_ref.get_instance = MagicMock(return_value=mock_container)
        result = await pi_module.get_payment_instructions(
            reservation_code="PR-20260601-ABC",
            language="es",
        )

    assert "PR-20260601-ABC" in result["response"]
    assert "PASO" in result["response"]
    assert "Reserva:" in result["response"]
