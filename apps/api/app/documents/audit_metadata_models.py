"""Typed metadata models for ReservationAuditLogDocument.

Replaces bare ``metadata: dict`` with a discriminated union so each audit
action carries the exact fields it needs.

Actions without metadata simply leave ``metadata=None``.
"""

from __future__ import annotations

from pydantic import BaseModel


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


# Union of all known metadata shapes.
# Add new variants here as actions evolve.
AuditMetadata = AssignmentMetadata | ReplacementMetadata | NotificationMetadata
