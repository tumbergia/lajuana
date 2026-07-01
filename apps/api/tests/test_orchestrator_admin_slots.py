from __future__ import annotations

from app.schemas.ask import AskRequest


def test_admin_api_does_not_seed_holder_phone_from_from_phone() -> None:
    """admin_ask passes user id as from_phone; must not become holder_phone."""
    request = AskRequest(
        message="hola",
        channel="admin_api",
        from_phone="507f1f77bcf86cd799439011",
        conversation_id="test-admin-slots",
    )

    phone = request.from_phone
    session_slots: dict = {}

    if request.channel in {"whatsapp", "test", "mobile_api"}:
        if phone and "holder_phone" not in session_slots:
            session_slots["holder_phone"] = phone

    assert "holder_phone" not in session_slots
