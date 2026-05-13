from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.ai.assistant.date_guard import (
    InvalidRequestedDateError,
    validate_requested_date_for_business,
)
from app.core.time import (
    APP_TIMEZONE_NAME,
    format_colombia_today_es,
    now_colombia,
    today_colombia,
    today_colombia_iso,
)


def test_colombia_date_does_not_follow_utc_day_boundary():
    utc_now = datetime(2026, 5, 13, 1, 30, tzinfo=UTC)
    colombia_now = utc_now.astimezone(ZoneInfo(APP_TIMEZONE_NAME))

    assert utc_now.date().isoformat() == "2026-05-13"
    assert colombia_now.date().isoformat() == "2026-05-12"


def test_today_colombia_returns_date():
    result = today_colombia()
    assert isinstance(result, date)


def test_today_colombia_iso_format():
    result = today_colombia_iso()
    assert isinstance(result, str)
    assert len(result) == 10


def test_now_colombia_has_correct_timezone():
    result = now_colombia()
    assert result.tzinfo is not None
    assert result.tzinfo.key == APP_TIMEZONE_NAME


def test_format_colombia_today_es_returns_spanish_string():
    result = format_colombia_today_es()
    assert "de" in result
    assert isinstance(result, str)
    assert len(result) > 10


def test_now_colombia_and_now_utc_same_moment():
    co = now_colombia()
    utc = datetime.now(UTC)
    diff = abs((co.astimezone(UTC) - utc).total_seconds())
    assert diff < 2


def test_validate_requested_date_none():
    assert validate_requested_date_for_business(None) is None


def test_validate_requested_date_future():
    future = today_colombia() + timedelta(days=30)
    result = validate_requested_date_for_business(future)
    assert result == future


def test_validate_requested_date_today():
    today = today_colombia()
    result = validate_requested_date_for_business(today)
    assert result == today


def test_validate_requested_date_past_raises():
    yesterday = today_colombia() - timedelta(days=1)
    with pytest.raises(InvalidRequestedDateError):
        validate_requested_date_for_business(yesterday)
