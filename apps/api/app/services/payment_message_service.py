from __future__ import annotations

from app.schemas.config import PaymentInstructionsSchema


def render_payment_steps(config: PaymentInstructionsSchema) -> str:
    methods: list[str] = []
    if config.manual_transfer_enabled:
        methods.append(
            f"CUENTA {config.account_type.upper()} {config.account_bank.upper()}\n"
            f"   No. {config.account_number}\n"
            f"   {config.account_holder_name}\n"
            f"   {config.account_holder_id}\n"
            f"   {config.transfer_note}"
        )
    if config.bold_enabled and config.bold_checkout_url:
        methods.append(
            "LINK DE PAGO BOLD\n"
            f"   {config.bold_checkout_url}\n"
            f"   Comisión adicional: {config.bold_surcharge_percent:g}%.\n"
            f"   {config.bold_note}"
        )
    numbered = "\n\n".join(f"{index}. {method}" for index, method in enumerate(methods, 1))
    return (
        "PASO 1. Realizar el pago del valor de la experiencia según número de participantes.\n\n"
        f"Medios de pago disponibles:\n\n{numbered}\n\n"
        "PASO 2. Enviar comprobante de pago por este mismo medio (WhatsApp).\n\n"
        "PASO 3. Registrar a cada participante en el formulario que te enviaremos."
    )
