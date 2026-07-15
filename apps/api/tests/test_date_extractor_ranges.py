from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

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


def test_extract_desde_hasta_hoy() -> None:
    fixed = date(2026, 7, 14)
    with patch("app.ai.assistant.date_extractor.now_colombia") as mock_now:
        mock_now.return_value.date.return_value = fixed
        result = extract_date_range_from_message(
            "cuántos ingresos he obtenido desde el 14 de febrero hasta hoy"
        )
    assert result == ("2026-02-14", "2026-07-14")


def test_extract_desde_without_hasta_defaults_to_today() -> None:
    fixed = date(2026, 7, 14)
    with patch("app.ai.assistant.date_extractor.now_colombia") as mock_now:
        mock_now.return_value.date.return_value = fixed
        result = extract_date_range_from_message(
            "dime cuántos ingresos he generado desde el 4 de mayo de este año"
        )
    assert result == ("2026-05-04", "2026-07-14")


def test_extract_desde_month_rolls_back_if_future() -> None:
    # On Jan 10, "desde el 14 de febrero" without year should use previous year.
    fixed = date(2026, 1, 10)
    with patch("app.ai.assistant.date_extractor.now_colombia") as mock_now:
        mock_now.return_value.date.return_value = fixed
        result = extract_date_range_from_message(
            "ingresos desde el 14 de febrero hasta hoy"
        )
    assert result == ("2025-02-14", "2026-01-10")
