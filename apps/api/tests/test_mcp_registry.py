from app.ai.mcp.registry import registry


def test_reservation_draft_tools_are_registered() -> None:
    names = set(registry.names())
    assert "create_reservation_draft" in names
    assert "attach_payment_proof_to_reservation" in names
    assert "get_reservation_public_summary" in names
    assert "get_reservation_status_by_phone" in names
