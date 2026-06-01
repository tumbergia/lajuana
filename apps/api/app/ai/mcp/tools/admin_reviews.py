"""Admin tool for listing human review requests."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminListHumanReviewRequestsOutput,
    ToolBlockingReason,
)
from app.documents.human_review_request_document import HumanReviewRequestDocument


async def admin_list_human_review_requests(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListHumanReviewRequestsOutput | None = None

    try:
        status_filter = kwargs.get("status")
        priority_filter = kwargs.get("priority")
        limit = kwargs.get("limit", 50)
        skip = kwargs.get("skip", 0)

        query: dict[str, Any] = {}
        if status_filter:
            query["status"] = status_filter
        if priority_filter:
            query["priority"] = priority_filter

        if query:
            docs = await HumanReviewRequestDocument.find(query).skip(skip).limit(limit).to_list()
        else:
            docs = await HumanReviewRequestDocument.find_all().skip(skip).limit(limit).to_list()

        items = []
        for doc in docs:
            items.append(
                {
                    "review_id": doc.review_id,
                    "conversation_id": doc.conversation_id,
                    "reason_code": doc.reason_code,
                    "summary": doc.summary,
                    "priority": doc.priority,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat() if doc.created_at else "",
                }
            )

        output = AdminListHumanReviewRequestsOutput(
            trace_id=trace_id,
            total=len(items),
            requests=items,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListHumanReviewRequestsOutput(
            trace_id=trace_id,
            total=0,
            requests=[],
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_human_review_requests",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()