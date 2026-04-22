from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.common.enums import ExperienceLevel
from app.documents.participant_document import EmergencyContact
from app.services.participant_service import ParticipantService


def _build_participant(*, accepted_data_processing: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        first_name="Ana",
        last_name="Perez",
        birth_date=date(2000, 1, 1),
        document_type="cc",
        document_number="123",
        phone="3000000000",
        country="CO",
        city="Bogota",
        height_cm=Decimal("165"),
        weight_kg=Decimal("60"),
        experience_level=ExperienceLevel.BASIC,
        emergency_contact=EmergencyContact(name="Luis", phone="3001111111"),
        accepted_data_processing=accepted_data_processing,
    )


def test_participant_completion_true() -> None:
    service = ParticipantService()
    participant = _build_participant()
    assert service._is_completed(participant) is True


def test_participant_completion_false_without_data_consent() -> None:
    service = ParticipantService()
    participant = _build_participant(accepted_data_processing=False)
    assert service._is_completed(participant) is False
