import pytest

from app.ai.assistant.orchestrator import (
    CANCEL_WORDS,
    CONFIRM_WORDS,
    WRITE_TOOLS_REQUIRING_CONFIRMATION,
    AssistantOrchestrator,
)


class TestIsConfirmation:
    @pytest.mark.parametrize(
        "message,expected",
        [
            # Confirmaciones
            ("sí", True),
            ("SÍ", True),
            ("si", True),
            ("yes", True),
            ("YES", True),
            ("confirmar", True),
            ("confirmo", True),
            ("ok", True),
            ("OK", True),
            ("okay", True),
            ("dale", True),
            ("adelante", True),
            ("hazlo", True),
            ("ejecutar", True),
            ("sí, hazlo", True),
            ("ok dale", True),
            # No confirmaciones
            ("no", False),
            ("cancelar", False),
            ("nope", False),
            ("quizás", False),
            ("", False),
            ("hola", False),
            ("muéstrame los equinos", False),
        ],
    )
    def test_is_confirmation(self, message: str, expected: bool) -> None:
        assert AssistantOrchestrator._is_confirmation(message) == expected


class TestIsCancellation:
    @pytest.mark.parametrize(
        "message,expected",
        [
            ("no", True),
            ("NO", True),
            ("cancelar", True),
            ("cancelo", True),
            ("nope", True),
            ("abortar", True),
            ("detener", True),
            ("no quiero", True),
            ("olvídalo", True),
            ("no, cancela", True),
            ("deten eso", True),
            # No cancelaciones
            ("sí", False),
            ("confirmar", False),
            ("ok", False),
            ("", False),
            ("hola", False),
        ],
    )
    def test_is_cancellation(self, message: str, expected: bool) -> None:
        assert AssistantOrchestrator._is_cancellation(message) == expected


class TestWriteToolsRequiringConfirmation:
    """Verifica que WRITE_TOOLS_REQUIRING_CONFIRMATION contiene tools destructivas."""

    def test_contains_deactivation_tools(self) -> None:
        assert "admin_deactivate_experience" in WRITE_TOOLS_REQUIRING_CONFIRMATION
        assert "admin_deactivate_user" in WRITE_TOOLS_REQUIRING_CONFIRMATION
        assert "admin_deactivate_schedule" in WRITE_TOOLS_REQUIRING_CONFIRMATION
        assert "admin_deactivate_equine" in WRITE_TOOLS_REQUIRING_CONFIRMATION

    def test_contains_write_tools(self) -> None:
        assert "admin_confirm_reservation" in WRITE_TOOLS_REQUIRING_CONFIRMATION
        assert "admin_cancel_reservation" in WRITE_TOOLS_REQUIRING_CONFIRMATION
        assert "admin_approve_payment" in WRITE_TOOLS_REQUIRING_CONFIRMATION
        assert "admin_reject_payment_proof" in WRITE_TOOLS_REQUIRING_CONFIRMATION

    def test_not_empty(self) -> None:
        assert len(WRITE_TOOLS_REQUIRING_CONFIRMATION) > 0

    def test_confirm_words_not_empty(self) -> None:
        assert len(CONFIRM_WORDS) >= 5

    def test_cancel_words_not_empty(self) -> None:
        assert len(CANCEL_WORDS) >= 5
