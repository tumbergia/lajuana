from datetime import UTC, datetime
from uuid import uuid4

from beanie import Document
from pydantic import Field

from app.common.collections import Collections


class HumanReviewRequestDocument(Document):
    review_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    reason_code: str
    summary: str
    priority: str = "normal"
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolved_by: str | None = None

    class Settings:
        name = Collections.HUMAN_REVIEW_REQUESTS
        indexes = [
            "review_id",
            "conversation_id",
            "status",
            "priority",
            "created_at",
            [("status", 1), ("priority", 1), ("created_at", 1)],
        ]
