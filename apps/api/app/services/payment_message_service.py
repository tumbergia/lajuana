from __future__ import annotations

from app.ai.language.messages import t
from app.schemas.config import PaymentInstructionsSchema


def render_payment_steps(config: PaymentInstructionsSchema, language: str = "es") -> str:
    methods: list[str] = []
    if config.manual_transfer_enabled:
        account_label = t("payment_account_label", language)
        no_label = t("payment_account_number", language)
        methods.append(
            f"{account_label} {config.account_type.upper()} {config.account_bank.upper()}\n"
            f"   {no_label} {config.account_number}\n"
            f"   {config.account_holder_name}\n"
            f"   {config.account_holder_id}\n"
            f"   {config.transfer_note}"
        )
    if config.bold_enabled and config.bold_checkout_url:
        bold_label = t("payment_bold_link_label", language)
        surcharge_label = t("payment_bold_surcharge", language)
        methods.append(
            f"{bold_label}\n"
            f"   {config.bold_checkout_url}\n"
            f"   {surcharge_label}: {config.bold_surcharge_percent:g}%.\n"
            f"   {config.bold_note}"
        )
    numbered = "\n\n".join(f"{index}. {method}" for index, method in enumerate(methods, 1))
    step_1 = t("payment_step_1_header", language)
    methods_header = t("payment_methods_header", language)
    step_2 = t("payment_step_2", language)
    step_3 = t("payment_step_3", language)
    return (
        f"{step_1}\n\n"
        f"{methods_header}\n\n{numbered}\n\n"
        f"{step_2}\n\n"
        f"{step_3}"
    )
