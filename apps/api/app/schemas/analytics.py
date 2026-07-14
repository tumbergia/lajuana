from datetime import datetime

from pydantic import BaseModel, Field


class LeadItem(BaseModel):
    id: str
    category: str
    title: str
    value: str
    unit: str
    description: str
    icon: str
    order: int
    details: list[dict[str, str]] = []
    home_eligible: bool = True
    # Higher = more likely to appear in the random home fill (money/action bias).
    home_priority: int = 1


class LeadCategory(BaseModel):
    id: str
    name: str
    icon: str
    leads: list[LeadItem]


class AnalyticsResponse(BaseModel):
    categories: list[LeadCategory]
    generated_at: datetime
    total_leads: int


class LeadsPreferencesSchema(BaseModel):
    """Per-user home lead pins and exclusions."""

    pinned_lead_ids: list[str] = Field(default_factory=list)
    excluded_lead_ids: list[str] = Field(default_factory=list)

    @classmethod
    def from_user_prefs(cls, prefs: dict | None) -> "LeadsPreferencesSchema":
        stored = prefs or {}
        pinned = list(stored.get("pinned_lead_ids") or [])
        excluded = list(stored.get("excluded_lead_ids") or [])
        # Pins win over exclusions; cap pins at 5; preserve order, drop dupes.
        seen_pin: set[str] = set()
        clean_pins: list[str] = []
        for lid in pinned:
            if not isinstance(lid, str) or not lid or lid in seen_pin:
                continue
            seen_pin.add(lid)
            clean_pins.append(lid)
            if len(clean_pins) >= 5:
                break
        seen_excl: set[str] = set()
        clean_excl: list[str] = []
        for lid in excluded:
            if not isinstance(lid, str) or not lid or lid in seen_excl or lid in seen_pin:
                continue
            seen_excl.add(lid)
            clean_excl.append(lid)
        return cls(pinned_lead_ids=clean_pins, excluded_lead_ids=clean_excl)


class LeadsPreferencesUpdateSchema(BaseModel):
    pinned_lead_ids: list[str] = Field(default_factory=list)
    excluded_lead_ids: list[str] = Field(default_factory=list)
