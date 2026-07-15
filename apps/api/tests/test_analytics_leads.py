"""Unit tests for analytics leads preferences and home eligibility (legacy)."""

from __future__ import annotations

from app.schemas.analytics import LeadsPreferencesSchema, LeadItem
from app.services.analytics_service import HOME_INELIGIBLE_IDS, _lead


def test_leads_preferences_caps_pins_and_drops_dupes() -> None:
    schema = LeadsPreferencesSchema.from_user_prefs(
        {
            "pinned_lead_ids": [
                "a",
                "b",
                "a",
                "c",
                "d",
                "e",
                "f",
                "",
                123,  # type: ignore[list-item]
            ],
            "excluded_lead_ids": ["x", "a", "y", "x"],
        }
    )
    assert schema.pinned_lead_ids == ["a", "b", "c", "d", "e"]
    assert schema.excluded_lead_ids == ["x", "y"]


def test_leads_preferences_empty_defaults() -> None:
    schema = LeadsPreferencesSchema.from_user_prefs(None)
    assert schema.pinned_lead_ids == []
    assert schema.excluded_lead_ids == []


def test_home_ineligible_ids_cover_static_kpis() -> None:
    for lead_id in (
        "eq_total",
        "par_total",
        "vol_total",
        "pay_total",
        "exp_total",
        "ori_top_5",
        "op_usuarios_total",
        "vol_conversion",
    ):
        assert lead_id in HOME_INELIGIBLE_IDS


def test_lead_helper_sets_home_eligible_from_blacklist() -> None:
    blocked = _lead(
        id="eq_total",
        category="catalogo",
        title="Total equinos",
        value="10",
        unit="equinos",
        description="x",
        icon="pets",
        order=1,
    )
    assert isinstance(blocked, LeadItem)
    assert blocked.home_eligible is False
    assert blocked.home_priority == 0

    eligible = _lead(
        id="eq_available",
        category="eq_operacion",
        title="Disponibles",
        value="3",
        unit="equinos",
        description="x",
        icon="check",
        order=1,
    )
    assert eligible.home_eligible is True
    assert eligible.home_priority >= 1


def test_lead_helper_allows_explicit_override() -> None:
    forced = _lead(
        id="eq_total",
        category="catalogo",
        title="Total equinos",
        value="10",
        unit="equinos",
        description="x",
        icon="pets",
        order=1,
        home_eligible=True,
    )
    assert forced.home_eligible is True


def test_money_leads_have_elevated_home_priority() -> None:
    from app.services.analytics_service import HOME_PRIORITY_BY_ID

    assert HOME_PRIORITY_BY_ID["ing_confirmed"] >= 8
    money = _lead(
        id="ing_confirmed",
        category="dinero",
        title="Valor confirmado",
        value="1",
        unit="COP",
        description="x",
        icon="verified",
        order=1,
    )
    assert money.home_priority >= 8
