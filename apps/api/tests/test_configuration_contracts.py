from __future__ import annotations

import asyncio
import base64
import json

import pytest
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.assistant_plan import ToolArgs
from app.schemas.config import (
    AiConfigurationUpdateSchema,
    AiRouteUpdateSchema,
    BusinessLocationUpdateSchema,
    PaymentInstructionsUpdateSchema,
    ReservationRulesUpdateSchema,
)


def test_ai_configuration_requires_exactly_three_routes() -> None:
    route = AiRouteUpdateSchema(
        position=1,
        service="gemini",
        model="gemini-test",
        api_key="secret",
    )
    with pytest.raises(ValidationError):
        AiConfigurationUpdateSchema(enabled=True, routes=[route])


def test_ai_models_have_no_defaults() -> None:
    route = AiRouteUpdateSchema(position=1, service="openai")
    assert route.model is None


def test_planner_contract_exposes_bold_requested() -> None:
    schema = ToolArgs.model_json_schema()

    assert schema["properties"]["bold_requested"]["default"] is False


def test_planner_requires_live_config_for_payment_proof_questions() -> None:
    from app.ai.assistant.prompts.planner import (
        PLANNER_SYSTEM_PROMPT,
        TOOL_RESULT_RESPONSE_SYSTEM_PROMPT,
    )

    assert "comprobante o recibo es obligatorio" in PLANNER_SYSTEM_PROMPT
    assert "usa get_public_business_rules" in PLANNER_SYSTEM_PROMPT
    assert "nunca afirmes que el pago se refleja automáticamente" in TOOL_RESULT_RESPONSE_SYSTEM_PROMPT


def test_payment_requires_one_enabled_method() -> None:
    with pytest.raises(ValidationError):
        PaymentInstructionsUpdateSchema(
            manual_transfer_enabled=False,
            bold_enabled=False,
        )


def test_location_validates_coordinates() -> None:
    with pytest.raises(ValidationError):
        BusinessLocationUpdateSchema(latitude=95, longitude=-75)


def test_reservation_rules_validate_age_range_and_ttl() -> None:
    with pytest.raises(ValidationError):
        ReservationRulesUpdateSchema(min_age=70, max_age=12)
    with pytest.raises(ValidationError):
        ReservationRulesUpdateSchema(reservation_draft_ttl_minutes=0)


def test_secret_crypto_round_trip_and_no_plaintext(monkeypatch: pytest.MonkeyPatch) -> None:
    key = base64.urlsafe_b64encode(b"x" * 32).decode()
    monkeypatch.setattr(settings, "ai_config_encryption_key", key)

    from app.core.secret_crypto import decrypt_secret, encrypt_secret

    encrypted = encrypt_secret("sk-super-secret")
    assert "sk-super-secret" not in encrypted
    assert decrypt_secret(encrypted) == "sk-super-secret"


def test_request_model_validation_error_is_json_serializable() -> None:
    from app.core.errors import validation_error_handler

    error = RequestValidationError(
        [
            {
                "type": "value_error",
                "loc": ("body",),
                "msg": "Value error, rango inválido",
                "input": {"min_age": 80, "max_age": 20},
                "ctx": {"error": ValueError("rango inválido")},
            }
        ]
    )

    response = asyncio.run(validation_error_handler(None, error))  # type: ignore[arg-type]

    assert response.status_code == 422
    assert json.loads(response.body)["code"] == "common.validation_error"
