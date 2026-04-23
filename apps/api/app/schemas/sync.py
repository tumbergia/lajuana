from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class SyncStreamCursorSchema(BaseModel):
    name: str
    cursor: str | None = None


class SyncPullRequestSchema(BaseModel):
    streams: list[SyncStreamCursorSchema]


class SyncChangeSchema(BaseModel):
    change_type: Literal["upsert", "delete"]
    entity_id: str
    version: int
    updated_at: datetime
    payload: dict[str, Any] | None


class SyncPullStreamResponseSchema(BaseModel):
    name: str
    next_cursor: str
    changes: list[SyncChangeSchema]


class SyncPullResponseSchema(BaseModel):
    server_time: datetime
    streams: list[SyncPullStreamResponseSchema]


class SyncPushOperationSchema(BaseModel):
    operation_id: str
    entity_type: str
    entity_local_id: str
    entity_remote_id: str | None = None
    operation_type: Literal[
        "create",
        "update",
        "delete",
        "upload_file",
        "transition_status",
        "confirm_reservation",
        "cancel_reservation",
    ]
    base_version: int | None = None
    idempotency_key: str
    payload: dict[str, Any]


class SyncPushRequestSchema(BaseModel):
    operations: list[SyncPushOperationSchema]


class SyncOperationErrorSchema(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class SyncPushResultSchema(BaseModel):
    operation_id: str
    status: Literal["applied", "conflict", "rejected"]
    entity_type: str
    entity_local_id: str
    entity_remote_id: str | None = None
    version: int | None = None
    updated_at: datetime | None = None
    payload: dict[str, Any] | None = None
    error: SyncOperationErrorSchema | None = None


class SyncPushResponseSchema(BaseModel):
    results: list[SyncPushResultSchema]
