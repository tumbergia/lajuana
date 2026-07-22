"""Tool: búsqueda en la base de conocimiento corporativa (RAG)."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.knowledge.retriever import format_knowledge_response, retrieve
from app.ai.mcp.tool_contracts import (
    SearchCompanyKnowledgeInput,
    SearchCompanyKnowledgeOutput,
    ToolBlockingReason,
)
from app.documents.tool_call_log_document import ToolCallLogDocument


async def search_company_knowledge(**kwargs: Any) -> dict[str, Any]:
    """Recupera fragmentos del MD corporativo relevantes a la pregunta."""
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    language: str = kwargs.pop("language", "es") or "es"
    started = time.perf_counter()

    payload: SearchCompanyKnowledgeInput | None = None
    output: SearchCompanyKnowledgeOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items() if k in SearchCompanyKnowledgeInput.model_fields
        }
        payload = SearchCompanyKnowledgeInput.model_validate(filtered)
        query = (payload.query or "").strip()
        chunks = retrieve(query, language=language, top_k=payload.top_k)
        response = format_knowledge_response(chunks, language=language)
        output = SearchCompanyKnowledgeOutput(
            trace_id=trace_id,
            query=query,
            chunk_ids=[c.chunk_id for c in chunks],
            scores=[round(c.score, 4) for c in chunks],
            response=response,
            blocking_reasons=[],
        )
        return output.model_dump(mode="json")
    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = SearchCompanyKnowledgeOutput(
            trace_id=trace_id,
            query=str(kwargs.get("query") or ""),
            chunk_ids=[],
            scores=[],
            response=str(exc),
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="search_company_knowledge",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
