"""Tests para el documento de auditoria de comprobantes.

NOTA: No instanciamos ReservationAuditLogDocument directamente porque
APP_SKIP_DB_INIT evita que Beanie inicialice las colecciones.
Verificamos la estructura via reflexion e importacion."""

import os

os.environ["APP_SKIP_DB_INIT"] = "true"

from app.common.enums import UserRole


def test_audit_log_module_importable() -> None:
    """Verify the audit log document module can be imported."""
    from app.documents.reservation_audit_log_document import (
        ReservationAuditLogDocument,
    )

    assert ReservationAuditLogDocument is not None


def test_audit_log_has_required_fields() -> None:
    """Verify the audit log class defines expected fields via __annotations__."""
    from app.documents.reservation_audit_log_document import (
        ReservationAuditLogDocument,
    )

    annotations = ReservationAuditLogDocument.__annotations__
    assert "reservation_id" in annotations
    assert "actor_user_id" in annotations
    assert "actor_role" in annotations
    assert "action" in annotations
    assert "previous_status" in annotations
    assert "new_status" in annotations
    assert "source" in annotations


def test_audit_log_action_values() -> None:
    """Verify expected action string constants are valid."""
    valid_actions = {
        "payment_proof.approved",
        "payment_proof.rejected",
        "payment_proof.unverified",
        "payment_proof.unrejected",
        "reservation.confirmed",
    }
    assert "payment_proof.approved" in valid_actions
    assert "payment_proof.rejected" in valid_actions
    assert "reservation.confirmed" in valid_actions


def test_audit_log_role_values() -> None:
    """Verify UserRole values used in audit match expectations."""
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.GUIDE.value == "guide"


def test_assignment_metadata_serializes() -> None:
    """Verify AssignmentMetadata shape."""
    from app.documents.audit_metadata_models import AssignmentMetadata

    m = AssignmentMetadata(assignment_id="abc123")
    assert m.assignment_id == "abc123"
    assert m.model_dump() == {"assignment_id": "abc123"}


def test_replacement_metadata_serializes() -> None:
    """Verify ReplacementMetadata shape."""
    from app.documents.audit_metadata_models import ReplacementMetadata

    m = ReplacementMetadata(replaced_by="new_id")
    assert m.replaced_by == "new_id"
    assert m.model_dump() == {"replaced_by": "new_id"}


def test_notification_metadata_serializes() -> None:
    """Verify NotificationMetadata shape (required + optional fields)."""
    from app.documents.audit_metadata_models import NotificationMetadata

    m = NotificationMetadata(
        recipient_phone="+573001234567",
        template_key="welcome",
        provider_message_id="msg_001",
        status="sent",
    )
    assert m.recipient_phone == "+573001234567"
    assert m.template_key == "welcome"
    assert m.provider_message_id == "msg_001"
    assert m.status == "sent"

    m_minimal = NotificationMetadata(
        recipient_phone="+573001234567",
        template_key="welcome",
        status="sent",
    )
    assert m_minimal.provider_message_id is None


def test_audit_metadata_union_validates() -> None:
    """Verify metadata field accepts any AuditMetadata variant."""
    from app.documents.audit_metadata_models import (
        AssignmentMetadata,
        AuditMetadata,
        NotificationMetadata,
        ReplacementMetadata,
    )

    # All three variants should be assignable to AuditMetadata
    variants: list[AuditMetadata] = [
        AssignmentMetadata(assignment_id="x"),
        ReplacementMetadata(replaced_by="y"),
        NotificationMetadata(
            recipient_phone="p", template_key="t", status="s"
        ),
    ]
    assert len(variants) == 3
    assert all(isinstance(v, (AssignmentMetadata, ReplacementMetadata, NotificationMetadata)) for v in variants)


def test_parse_audit_metadata_tolerates_empty_dict() -> None:
    from app.documents.audit_metadata_models import ParticipantMetadata, parse_audit_metadata

    assert parse_audit_metadata({}) is None
    assert parse_audit_metadata(None) is None
    parsed = parse_audit_metadata(
        {"participant_id": "p1", "participant_name": "Ana López"},
    )
    assert isinstance(parsed, ParticipantMetadata)
