from typing import Any

from pydantic import BaseModel, Field


class SlotsMergeResult(BaseModel):
    merged: dict[str, Any] = Field(default_factory=dict)
    still_missing: list[str] = Field(default_factory=list)
    filled_from_session: list[str] = Field(default_factory=list)


def merge_slots(
    *,
    session_slots: dict[str, Any],
    plan_args: dict[str, Any],
    required_fields: list[str],
) -> SlotsMergeResult:
    def has_value(value: Any) -> bool:
        if value is None or value == "":
            return False
        if isinstance(value, (dict, list, tuple, set)) and len(value) == 0:
            return False
        return True

    merged = dict(session_slots)
    filled_from_session: list[str] = []

    for key, value in plan_args.items():
        if has_value(value):
            merged[key] = value

    for key in required_fields:
        session_val = session_slots.get(key)
        plan_val = plan_args.get(key)
        if not has_value(plan_val) and has_value(session_val):
            merged[key] = session_val
            filled_from_session.append(key)

    still_missing = [f for f in required_fields if not has_value(merged.get(f))]

    return SlotsMergeResult(
        merged=merged,
        still_missing=still_missing,
        filled_from_session=filled_from_session,
    )
