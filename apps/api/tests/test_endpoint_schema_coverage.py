"""Verify all Document fields are mapped in response schemas.

Catches silent omissions when a field is added to a Document
but forgotten in the corresponding response Schema.
"""

from app.documents import (
    EquineDocument,
    ParticipantDocument,
    ReservationDocument,
    SaddleDocument,
    UserDocument,
)
from app.schemas.equine import EquineListItemSchema, EquineResponseSchema
from app.schemas.participant import ParticipantResponseSchema
from app.schemas.reservation import ReservationListItemSchema, ReservationResponseSchema
from app.schemas.saddle import SaddleResponseSchema
from app.schemas.auth import UserResponseSchema

# Fields that exist on the Document but are intentionally excluded
# from the response schema (e.g., internal bookkeeping).
KNOWN_EXCLUSIONS: dict[type, set[str]] = {
    ReservationDocument: {
        "revision_id", "id",
        # Internal/audit fields not exposed in response
        "created_by", "updated_by",
        "participant_ids", "payment_proof_ids", "provider_ids", "policy_ids",
        "quote_snapshot", "quote_trace_id",
        "pre_reserved_at", "confirmed_at", "cancelled_at", "completed_at", "expire_at",
        "participant_form_sent_at", "participant_form_sent_by",
        "participant_form_send_count", "participant_form_last_message_id",
        "confirmation_message_sent_at", "confirmation_message_sent_by",
        "availability_lock_key", "blocks_day",
    },
    ReservationListItemSchema: {
        "revision_id", "id",
        # Same as above for list items
        "created_by", "updated_by",
        "participant_ids", "payment_proof_ids", "provider_ids", "policy_ids",
        "quote_snapshot", "quote_trace_id",
        "pre_reserved_at", "confirmed_at", "cancelled_at", "completed_at", "expire_at",
        "participant_form_sent_at", "participant_form_sent_by",
        "participant_form_send_count", "participant_form_last_message_id",
        "confirmation_message_sent_at", "confirmation_message_sent_by",
        "availability_lock_key", "blocks_day",
        # Reserved fields intentionally omitted from list response
        "form_url", "quoted_total_amount",
        # Fields in list response that aren't Document fields
        "currency",
    },
    EquineDocument: {"revision_id", "id"},
    EquineListItemSchema: {
        "revision_id", "id",
        # EquineDocument fields intentionally omitted from list response
        "source_updated_at_label", "microchip", "availability_notes",
        "birth_date_raw", "last_weight_at", "birth_place", "source_row_number",
        "dam_name", "birth_date_is_approximate", "last_height_at", "rest_until",
        "location_notes", "sire_name", "registry_number", "source_sheet",
        "source_file", "approximate_age_years", "approximate_birth_date",
        "location_status", "availability_reasons",
    },
    SaddleDocument: {"revision_id", "id"},
    ParticipantDocument: {
        "revision_id", "id",
        # Internal fields
        "source_form_link_id", "submitted_at", "email",
    },
    UserDocument: {
        "revision_id", "id",
        # Security-sensitive fields never exposed
        "password_hash", "refresh_token_hash", "last_login_at",
    },
}


def _check_coverage(doc_cls: type, schema_cls: type, label: str) -> None:
    doc_fields = set(doc_cls.model_fields.keys())
    schema_fields = set(schema_cls.model_fields.keys())

    # Exclude fields that the Document has but the Schema
    # intentionally does not.
    known = KNOWN_EXCLUSIONS.get(doc_cls, set()) | KNOWN_EXCLUSIONS.get(schema_cls, set())
    unmapped = doc_fields - schema_fields - known

    assert not unmapped, (
        f"{label}: Document fields not in {schema_cls.__name__}: {unmapped}"
    )


def test_reservation_doc_coverage() -> None:
    _check_coverage(ReservationDocument, ReservationResponseSchema, "Reservation")


def test_reservation_list_item_coverage() -> None:
    _check_coverage(ReservationDocument, ReservationListItemSchema, "Reservation list")


def test_equine_doc_coverage() -> None:
    _check_coverage(EquineDocument, EquineResponseSchema, "Equine")


def test_equine_list_item_coverage() -> None:
    _check_coverage(EquineDocument, EquineListItemSchema, "Equine list")


def test_saddle_doc_coverage() -> None:
    _check_coverage(SaddleDocument, SaddleResponseSchema, "Saddle")


def test_participant_doc_coverage() -> None:
    _check_coverage(ParticipantDocument, ParticipantResponseSchema, "Participant")


def test_user_doc_coverage() -> None:
    _check_coverage(UserDocument, UserResponseSchema, "User")
