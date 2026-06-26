"""Tests de la tool MCP search_knowledge y su permiso de canal (Fase A)."""

from __future__ import annotations

import asyncio

import pytest

from app.ai.mcp.tools.knowledge import search_knowledge
from app.ai.rag.retriever import KnowledgeSearchHit


def test_search_knowledge_returns_snippets(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search(query, **kwargs):
        return [
            KnowledgeSearchHit(text="Lleva ropa cómoda", title="Guía", source_document_id="d1", score=0.92),
            KnowledgeSearchHit(text="Gorra y bloqueador", title="Guía", source_document_id="d1", score=0.81),
        ]

    monkeypatch.setattr(
        "app.ai.mcp.tools.knowledge.search_knowledge_chunks", fake_search
    )

    result = asyncio.run(search_knowledge(query="qué llevar", trace_id="t-1"))

    assert result["found"] is True
    assert result["total"] == 2
    assert result["snippets"][0]["text"] == "Lleva ropa cómoda"
    assert result["snippets"][0]["score"] == 0.92


def test_search_knowledge_empty_query_short_circuits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"hit": False}

    async def fake_search(query, **kwargs):
        called["hit"] = True
        return []

    monkeypatch.setattr(
        "app.ai.mcp.tools.knowledge.search_knowledge_chunks", fake_search
    )

    result = asyncio.run(search_knowledge(query="   ", trace_id="t-2"))

    assert result["found"] is False
    assert called["hit"] is False  # no se invoca el retriever


def test_search_knowledge_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.ai.mcp.tools.knowledge.settings.rag_enabled", False)

    result = asyncio.run(search_knowledge(query="algo", trace_id="t-3"))

    assert result["found"] is False


def test_search_knowledge_swallows_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(query, **kwargs):
        raise RuntimeError("embedding down")

    monkeypatch.setattr("app.ai.mcp.tools.knowledge.search_knowledge_chunks", boom)

    result = asyncio.run(search_knowledge(query="algo", trace_id="t-4"))

    assert result["found"] is False  # degrada en lugar de romper la conversación


def test_policy_allows_search_knowledge_on_whatsapp() -> None:
    from app.ai.assistant.policy import ToolPolicyEngine
    from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel

    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="search_knowledge",
        arguments={"query": "qué llevar"},
        risk_level=RiskLevel.LOW,
        user_goal="Pregunta informativa.",
        audit_summary="El usuario hizo una pregunta abierta.",
    )

    decision = ToolPolicyEngine().validate(plan, channel="whatsapp")

    assert decision.allowed is True
