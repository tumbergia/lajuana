import pytest

from app.core.errors import ApiError
from app.services.schedule_service import compute_available_slots


def test_compute_available_slots_ok() -> None:
    assert (
        compute_available_slots(
            capacity_total=8,
            reserved_slots=2,
            held_slots=1,
            blocked_slots=1,
            internal_slots=1,
        )
        == 3
    )


def test_compute_available_slots_negative_raises() -> None:
    with pytest.raises(ApiError):
        compute_available_slots(
            capacity_total=2,
            reserved_slots=2,
            held_slots=0,
            blocked_slots=1,
            internal_slots=0,
        )
