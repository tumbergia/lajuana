"""Typed metadata models for ReservationAuditLogDocument.

Replaces bare ``metadata: dict`` with a discriminated union so each audit
action carries the exact fields it needs.

Actions without metadata simply leave ``metadata=None``.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError


class AssignmentMetadata(BaseModel):
    """Metadata for assignment.finalized / assignment.unfinalized actions."""

    assignment_id: str


class ReplacementMetadata(BaseModel):
    """Metadata for assignment.replaced action."""

    replaced_by: str


class NotificationMetadata(BaseModel):
    """Metadata for notification audit logs (backend_event source)."""

    recipient_phone: str
    template_key: str
    provider_message_id: str | None = None
    status: str


class ParticipantMetadata(BaseModel):
    """Metadata for participant.registered audit action."""

    participant_id: str
    participant_name: str


# Union of all known metadata shapes.
# Add new variants here as actions evolve.
AuditMetadata = (
    AssignmentMetadata
    | ReplacementMetadata
    | NotificationMetadata
    | ParticipantMetadata
)

_METADATA_MODELS: tuple[type[BaseModel], ...] = (
    AssignmentMetadata,
    ReplacementMetadata,
    NotificationMetadata,
    ParticipantMetadata,
)


def parse_audit_metadata(value: object) -> AuditMetadata | None:
    """Parse stored metadata tolerating legacy empty or partial documents."""
    if value is None:
        return None
    if isinstance(value, dict) and not value:
        return None
    if isinstance(value, _METADATA_MODELS):
        return value
    if isinstance(value, dict):
        for model in _METADATA_MODELS:
            try:
                return model.model_validate(value)
            except ValidationError:
                continue
        return None
    return None
