from app.ai.assistant.prompts.planner import PLANNER_SYSTEM_PROMPT


def test_planner_requires_file_for_payment_proof_flow() -> None:
    assert 'Si el usuario dice "ya pagué" pero NO adjunta imagen/PDF del comprobante' in PLANNER_SYSTEM_PROMPT
    assert "NO confirmes la reserva ni el pago" in PLANNER_SYSTEM_PROMPT
