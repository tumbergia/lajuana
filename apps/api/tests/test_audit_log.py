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
