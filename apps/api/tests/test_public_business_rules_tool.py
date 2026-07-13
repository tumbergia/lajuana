from __future__ import annotations

from typing import Any

import pytest

from app.ai.mcp.tools import get_public_business_rules
from app.core.di import Container
from app.schemas.config import BusinessLocationSchema, ReservationRulesSchema


@pytest.mark.asyncio
async def test_public_business_rules_uses_live_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeConfigService:
        async def get_reservation_rules(self) -> ReservationRulesSchema:
            return ReservationRulesSchema(
                min_days_in_advance=2,
                require_payment_proof_for_confirmation=True,
                reservation_draft_ttl_minutes=45,
                min_age=10,
                max_age=70,
            )

        async def get_business_location(self) -> BusinessLocationSchema:
            return BusinessLocationSchema(
                name="La Juana QA",
                address="Dirección QA",
                municipality="Municipio QA",
                directions="Indicaciones QA",
                latitude=4.5,
                longitude=-74.1,
                google_maps_url="https://maps.google.com/?q=4.500000,-74.100000",
            )

    class FakeLog:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        async def insert(self) -> None:
            return None

    monkeypatch.setitem(Container.get_instance()._services, "config_service", FakeConfigService())
    monkeypatch.setattr("app.documents.tool_call_log_document.ToolCallLogDocument", FakeLog)

    output = await get_public_business_rules(trace_id="qa-live-config")

    assert output["reservation_notice_days"] == 2
    assert output["reservation_draft_ttl_minutes"] == 45
    assert output["min_age"] == 10
    assert output["max_age"] == 70
    assert output["location_name"] == "La Juana QA"
    assert output["location_address"] == "Dirección QA"
    assert output["google_maps_url"] == "https://maps.google.com/?q=4.500000,-74.100000"
