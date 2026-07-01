from __future__ import annotations

from datetime import timedelta

from app.ai.assistant.date_extractor import extract_date_range_from_message
from app.core.time import now_colombia


def test_extract_this_week_range_monday_to_sunday() -> None:
    today = now_colombia().date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)

    result = extract_date_range_from_message("dame que reservas hay esta semana")
    assert result == (start.isoformat(), end.isoformat())


def test_extract_today_range() -> None:
    today = now_colombia().date().isoformat()
    assert extract_date_range_from_message("reservas de hoy") == (today, today)
