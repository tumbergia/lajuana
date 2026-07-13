from __future__ import annotations

from typing import Any

import pytest

from app.ai.mcp.tools.payment_instructions import get_payment_instructions
from app.core.di import Container
from app.schemas.config import PaymentInstructionsSchema


@pytest.fixture(autouse=True)
def _configured_payments(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeConfigService:
        async def get_payment_instructions(self) -> PaymentInstructionsSchema:
            return PaymentInstructionsSchema(
                manual_transfer_enabled=True,
                account_bank="Bancolombia",
                account_type="Ahorros",
                account_number="7165 1544 758",
                account_holder_name="Jairo Ramírez Londoño",
                account_holder_id="C.C. No. 10.288.647",
                transfer_note="Envía el comprobante.",
                bold_enabled=True,
                bold_checkout_url="https://checkout.bold.co/demo",
                bold_surcharge_percent=7,
                bold_note="Comisión del intermediario.",
            )

    monkeypatch.setitem(Container.get_instance()._services, "config_service", FakeConfigService())


def _last_log(logs: list, tool_name: str) -> dict[str, Any] | None:
    for log in reversed(logs):
        d = log.model_dump() if hasattr(log, "model_dump") else log
        if d.get("tool_name") == tool_name:
            return d
    return None


@pytest.mark.asyncio
async def test_payment_instructions_returns_bancolombia_and_bold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Any] = []

    class _FakeLog:
        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)
            calls.append(self)

        async def insert(self) -> None:
            return None

    monkeypatch.setattr(
        "app.ai.mcp.tools.payment_instructions.ToolCallLogDocument",
        _FakeLog,
    )

    out = await get_payment_instructions(trace_id="t1", conversation_turn_id="turn-1")

    assert out["tool_name"] == "get_payment_instructions"
    assert out["bold_requested"] is False
    response: str = out["response"]
    assert "BANCOLOMBIA" in response
    assert "7165 1544 758" in response
    assert "Jairo Ramírez Londoño" in response
    assert "10.288.647" in response
    assert "LINK DE PAGO BOLD" in response
    assert "Comisión adicional: 7%" in response
    # No debe decir que envió correo.
    assert "correo" not in response.lower()


@pytest.mark.asyncio
async def test_payment_instructions_with_code_includes_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeLog:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def insert(self) -> None:
            return None

    monkeypatch.setattr(
        "app.ai.mcp.tools.payment_instructions.ToolCallLogDocument",
        _FakeLog,
    )

    out = await get_payment_instructions(
        trace_id="t2", conversation_turn_id="turn-2", reservation_code="PR-20260615-ABC"
    )
    assert "PR-20260615-ABC" in out["response"]


@pytest.mark.asyncio
async def test_payment_instructions_bold_requested_returns_configured_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeLog:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def insert(self) -> None:
            return None

    monkeypatch.setattr(
        "app.ai.mcp.tools.payment_instructions.ToolCallLogDocument",
        _FakeLog,
    )

    out = await get_payment_instructions(
        trace_id="t3", conversation_turn_id="turn-3", bold_requested=True
    )
    assert out["bold_requested"] is True
    assert "https://checkout.bold.co/demo" in out["response"]
    assert "asesor humano" not in out["response"].lower()
