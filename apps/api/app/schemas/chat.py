from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequestSchema(BaseModel):
    conversation_id: str = Field(min_length=3, max_length=128)
    message: str = Field(min_length=1, max_length=4000)


class ChatResponseSchema(BaseModel):
    conversation_id: str
    role: str
    reply: str
    booking_intent: bool
    rag_context: str | None = None
    processed_at: datetime
