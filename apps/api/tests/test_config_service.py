"""Tests for ConfigService.

Covers: emergency contacts (static), reservation rules (DB-backed),
payment instructions (DB-backed), and update validation.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from app.common.labels import ErrorCode
from app.core.errors import ApiError


class _FakeRules(BaseModel):
    """Matches ReservationRules shape for mocking."""
    min_days_in_advance: int = 3
    require_payment_proof_for_confirmation: bool = True
    reservation_draft_ttl_minutes: int = 30
    min_age: int = 12
    max_age: int = 65


def _fake_rules_doc(**overrides: object) -> SimpleNamespace:
    """Create a fake AppConfigDocument-like object."""
    base = dict(
        id="config_id_001",
        key="reservation_rules",
        reservation_rules=_FakeRules(),
        payment_instructions=None,
        automation=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class TestConfigEmergencyContacts:
    """ConfigService.get_emergency_contacts — pure function, no DB."""

    def test_returns_contacts_list(self) -> None:
        from app.services.config_service import ConfigService

        async def run() -> None:
            result = await ConfigService().get_emergency_contacts()
            assert len(result.items) > 0
            assert result.items[0].code is not None

        asyncio.run(run())

    def test_contacts_contain_police(self) -> None:
        from app.services.config_service import ConfigService

        async def run() -> None:
            result = await ConfigService().get_emergency_contacts()
            codes = {c.code for c in result.items}
            assert "police" in codes or "POLICIA" in codes

        asyncio.run(run())


class TestConfigReservationRules:

    def test_get_rules_returns_defaults_when_no_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.services.config_service import ConfigService

        async def run() -> None:
            svc = ConfigService()

            async def no_doc() -> None:
                return None
            monkeypatch.setattr(svc, "get_reservation_rules_document", no_doc)

            result = await svc.get_reservation_rules()
            assert result.min_days_in_advance == 7
            assert result.min_age == 12
            assert result.max_age == 65

        asyncio.run(run())

    def test_get_rules_returns_stored_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.services.config_service import ConfigService

        stored = _fake_rules_doc()

        async def run() -> None:
            svc = ConfigService()

            async def return_stored() -> SimpleNamespace:
                return stored
            monkeypatch.setattr(svc, "get_reservation_rules_document", return_stored)

            result = await svc.get_reservation_rules()
            assert result.min_days_in_advance == 3

        asyncio.run(run())

    def test_update_rules_rejects_negative_days(self) -> None:
        """Pydantic catches negative days at schema level."""
        from pydantic import ValidationError
        from app.schemas.config import ReservationRulesUpdateSchema

        with pytest.raises(ValidationError):
            ReservationRulesUpdateSchema(min_days_in_advance=-1)

    def test_update_rules_creates_new_doc_when_none_exists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.schemas.config import ReservationRulesUpdateSchema
        from app.services.config_service import ConfigService

        inserted_docs: list[object] = []

        class FakeDoc(BaseModel):
            model_config = {"arbitrary_types_allowed": True}
            key: str = ""
            reservation_rules: object = None
            payment_instructions: object = None
            automation: object = None

            async def insert(self) -> None:
                inserted_docs.append(self)

            async def save(self) -> None:
                pass

        async def run() -> None:
            svc = ConfigService()

            async def no_doc() -> None:
                return None
            monkeypatch.setattr(svc, "get_reservation_rules_document", no_doc)
            monkeypatch.setattr(
                "app.services.config_service.AppConfigDocument",
                FakeDoc,
            )

            payload = ReservationRulesUpdateSchema(min_days_in_advance=5)
            result = await svc.update_reservation_rules(payload)
            # Service returns AppConfigDocument; min_days lives in reservation_rules
            assert result.reservation_rules.min_days_in_advance == 5
            assert len(inserted_docs) == 1

        asyncio.run(run())


class TestConfigPaymentInstructions:

    def test_returns_defaults_when_no_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from app.services.config_service import ConfigService

        async def run() -> None:
            svc = ConfigService()

            async def no_doc() -> None:
                return None
            monkeypatch.setattr(svc, "get_payment_instructions_document", no_doc)

            result = await svc.get_payment_instructions()
            assert result.account_bank == "Bancolombia"

        asyncio.run(run())
