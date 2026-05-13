from datetime import date

from app.core.time import today_colombia


class InvalidRequestedDateError(ValueError):
    pass


def validate_requested_date_for_business(requested_date: date | None) -> date | None:
    if requested_date is None:
        return None

    today = today_colombia()

    if requested_date < today:
        raise InvalidRequestedDateError(
            f"requested_date {requested_date.isoformat()} is before Colombia today"
            f" {today.isoformat()}"
        )

    return requested_date
