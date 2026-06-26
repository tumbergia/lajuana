from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeDocumentResponseSchema(BaseModel):
    id: str
    title: str
    filename: str
    mime_type: str
    scope: Literal["public", "ops"]
    source: str
    size_bytes: int
    chunk_count: int
    status: Literal["processing", "ready", "failed"]
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeListResponseSchema(BaseModel):
    total: int
    documents: list[KnowledgeDocumentResponseSchema]


class KnowledgeUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    scope: Literal["public", "ops"] | None = None


class KnowledgeSearchRequestSchema(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    scope: Literal["public", "ops"] = "public"
    top_k: int | None = Field(default=None, ge=1, le=20)


class KnowledgeSearchResultItem(BaseModel):
    text: str
    title: str
    source_document_id: str
    score: float


class KnowledgeSearchResponseSchema(BaseModel):
    query: str
    scope: Literal["public", "ops"]
    total: int
    results: list[KnowledgeSearchResultItem]
