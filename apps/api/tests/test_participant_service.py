import asyncio
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.common.enums import ExperienceLevel
from app.core.di import Container
from app.documents.participant_document import EmergencyContact
from app.services import sync_change_recorder as rec


def _build_participant(
    *, accepted_data_processing: bool = True, accepted_risk_release: bool = True
) -> SimpleNamespace:
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
        emergency_contact=EmergencyContact(name="Luis", phone="3001111111"),
        accepted_data_processing=accepted_data_processing,
        accepted_risk_release=accepted_risk_release,
        is_completed=False,
        id="660000000000000000000101",
    )


def test_participant_completion_true() -> None:
    service = Container.get_instance().participant_service
    participant = _build_participant()
    assert service._is_completed(participant) is True


def test_participant_completion_false_without_data_consent() -> None:
    service = Container.get_instance().participant_service
    participant = _build_participant(accepted_data_processing=False)
    assert service._is_completed(participant) is False


class _CapturingSyncChangeDocument:
    """Fake de SyncChangeDocument — captura kwargs sin tocar Mongo."""

    captured: list[dict] = []

    def __init__(self, **kwargs: object) -> None:
        _CapturingSyncChangeDocument.captured.append(kwargs)

    async def insert(self) -> "_CapturingSyncChangeDocument":
        return self


@pytest.fixture(autouse=True)
def _capture_sync_changes(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    _CapturingSyncChangeDocument.captured = []
    monkeypatch.setattr(rec, "SyncChangeDocument", _CapturingSyncChangeDocument)

    async def _fake_payload(entity_type: str, doc: object) -> dict:
        return {"entity_type": entity_type, "id": getattr(doc, "id", None)}

    monkeypatch.setattr(rec, "_build_payload", _fake_payload)
    return _CapturingSyncChangeDocument.captured


def test_create_emits_participant_change(
    monkeypatch: pytest.MonkeyPatch, _capture_sync_changes: list[dict]
) -> None:
    from app.schemas.participant import EmergencyContactSchema, ParticipantCreateSchema

    reservation = SimpleNamespace(
        id="660000000000000000000001",
        participant_ids=[],
    )

    class _FakeParticipantDocument:
        def __init__(self, **kwargs: object) -> None:
            self.id = "660000000000000000000101"
            for key, value in kwargs.items():
                setattr(self, key, value)

        async def insert(self) -> "_FakeParticipantDocument":
            return self

    async def run() -> None:
        async def _mock_reservation_get(_id: object) -> object:
            return reservation

        async def _noop_save() -> None:
            pass

        reservation.save = _noop_save  # type: ignore[assignment]
        monkeypatch.setattr(
            "app.services.participant_service.ReservationDocument.get",
            _mock_reservation_get,
        )
        monkeypatch.setattr(
            "app.services.participant_service.ParticipantDocument",
            _FakeParticipantDocument,
        )

        payload = ParticipantCreateSchema(
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
            emergency_contact=EmergencyContactSchema(name="Luis", phone="3001111111"),
            accepted_data_processing=False,  # evita el flujo de audit log
        )

        svc = Container.get_instance().participant_service
        await svc.create("660000000000000000000001", payload)

        assert len(_capture_sync_changes) == 1
        assert _capture_sync_changes[0]["entity_type"] == "participant"
        assert _capture_sync_changes[0]["stream"] == "participants"

    asyncio.run(run())


def test_update_emits_participant_change(
    monkeypatch: pytest.MonkeyPatch, _capture_sync_changes: list[dict]
) -> None:
    from app.schemas.participant import ParticipantUpdateSchema

    participant = _build_participant(accepted_data_processing=False)
    participant.id = "660000000000000000000101"

    async def run() -> None:
        async def _mock_get(_id: str) -> object:
            return participant

        async def _noop_save() -> None:
            pass

        participant.save = _noop_save  # type: ignore[assignment]

        svc = Container.get_instance().participant_service
        monkeypatch.setattr(svc, "get", _mock_get)

        payload = ParticipantUpdateSchema(first_name="Nuevo Nombre")
        await svc.update("660000000000000000000101", payload)

        assert len(_capture_sync_changes) == 1
        assert _capture_sync_changes[0]["entity_type"] == "participant"

    asyncio.run(run())
