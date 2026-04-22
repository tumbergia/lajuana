import asyncio

import pytest

from app.common.enums import ReservationStatus
from app.core.errors import ApiError
from app.services.reservation_service import ALLOWED_RESERVATION_TRANSITIONS, ReservationService


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        (ReservationStatus.CONTACT, ReservationStatus.QUOTED),
        (ReservationStatus.QUOTED, ReservationStatus.PENDING_PAYMENT),
        (ReservationStatus.PENDING_PAYMENT, ReservationStatus.PAYMENT_RECEIVED),
        (ReservationStatus.PAYMENT_RECEIVED, ReservationStatus.CONFIRMED),
        (ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED),
    ],
)
def test_allowed_transitions(from_status: ReservationStatus, to_status: ReservationStatus) -> None:
    assert to_status in ALLOWED_RESERVATION_TRANSITIONS[from_status]


def test_invalid_transition_raises() -> None:
    reservation = type("ReservationStub", (), {"status": ReservationStatus.CONTACT})()
    service = ReservationService()
    with pytest.raises(ApiError):
        asyncio.run(service.transition_status(reservation, ReservationStatus.CONFIRMED))
