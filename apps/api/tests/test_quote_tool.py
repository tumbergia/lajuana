import asyncio
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.ai.mcp.tools.quote import quote_experience
from app.documents.experience_document import ExperienceDocument
from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionStatus,
)


class FakeToolLogDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = "log-fake"


async def _run_quote_experience_accepts_trace_id_and_conversation_turn_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(PydanticObjectId()),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    fake_exp = SimpleNamespace(
        id=PydanticObjectId(),
        pricing=SimpleNamespace(
            tiers=[
                SimpleNamespace(
                    min_participants=1,
                    max_participants=10,
                    price_per_person=50000,
                )
            ]
        ),
    )

    async def fake_get(_):
        return fake_exp

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.quote.ToolCallLogDocument", FakeToolLogDoc)

    result = await quote_experience(
        experience_query="medio d\u00eda",
        participant_count=4,
        trace_id=str(uuid4()),
        conversation_turn_id=str(uuid4()),
    )

    assert result["quoted"] is True
    assert result["participant_count"] == 4
    assert result["blocking_reasons"] == []


def test_quote_experience_accepts_trace_id_and_conversation_turn_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_quote_experience_accepts_trace_id_and_conversation_turn_id(monkeypatch))
