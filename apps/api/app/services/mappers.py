"""Schema mappers: document_to_schema helper + thin wrappers + complex mappers."""

import logging

from app.documents import (
    ParticipantDocument,
    ParticipantFormLinkDocument,
    PaymentProofDocument,
    ReservationDocument,
)
from app.schemas.assignment import AssignmentResponseSchema
from app.schemas.auth import UserResponseSchema
from app.schemas.equine import EquineListItemSchema, EquineResponseSchema
from app.schemas.experience import ExperienceResponseSchema
from app.schemas.participant import ParticipantResponseSchema
from app.schemas.participant_form_link import ParticipantFormLinkStatusResponse
from app.schemas.payment_proof import PaymentProofResponseSchema
from app.schemas.policy import PolicyResponseSchema
from app.schemas.provider import ProviderResponseSchema
from app.schemas.reservation import ReservationListItemSchema, ReservationResponseSchema
from app.schemas.saddle import SaddleResponseSchema
from app.schemas.schedule import ScheduleResponseSchema
from app.schemas.service_log import ServiceLogResponseSchema

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core helper
# ---------------------------------------------------------------------------

def document_to_schema(
    doc: object,
    schema_cls: type,
    *,
    scalar_fields: dict[str, str] | None = None,
    optional_scalar_fields: dict[str, str] | None = None,
    exclude_fields: set[str] | None = None,
) -> object:
    """Build a Pydantic schema from a Beanie Document via model_dump.

    Usage::

        schema = document_to_schema(
            equine_doc, EquineResponseSchema,
            scalar_fields={"id": "id"},
            optional_scalar_fields={"saddle_id": "saddle_id"},
        )
    """
    model_dump = getattr(doc, "model_dump", None)
    if model_dump is None:
        raise TypeError(f"doc has no model_dump (got {type(doc).__name__})")
    data = model_dump(exclude=exclude_fields or {"revision_id"})
    if scalar_fields:
        for target, source in scalar_fields.items():
            val = getattr(doc, source, None)
            data[target] = str(val) if val is not None else None
    if optional_scalar_fields:
        for target, source in optional_scalar_fields.items():
            val = getattr(doc, source, None)
            data[target] = str(val) if val is not None else None
    return schema_cls(**data)


# ---------------------------------------------------------------------------
# Thin wrappers — document_to_schema delegates (no custom logic)
# ---------------------------------------------------------------------------

user_to_response = lambda u: document_to_schema(u, UserResponseSchema, scalar_fields={"id": "id"})
experience_to_response = lambda d: document_to_schema(d, ExperienceResponseSchema, scalar_fields={"id": "id"})
schedule_to_response = lambda d: document_to_schema(d, ScheduleResponseSchema, scalar_fields={"id": "id", "experience_id": "experience_id"})
payment_proof_to_response = lambda d: document_to_schema(d, PaymentProofResponseSchema, scalar_fields={"id": "id", "reservation_id": "reservation_id"})
equine_to_response = lambda d: document_to_schema(d, EquineResponseSchema, scalar_fields={"id": "id"})
equine_to_list_item = lambda d: document_to_schema(d, EquineListItemSchema, scalar_fields={"id": "id"})
saddle_to_response = lambda d: document_to_schema(d, SaddleResponseSchema, scalar_fields={"id": "id"})
assignment_to_response = lambda d: document_to_schema(
    d, AssignmentResponseSchema,
    scalar_fields={"id": "id", "reservation_id": "reservation_id", "participant_id": "participant_id", "equine_id": "equine_id"},
    optional_scalar_fields={"saddle_id": "saddle_id"},
)
service_log_to_response = lambda d: document_to_schema(
    d, ServiceLogResponseSchema,
    scalar_fields={"id": "id", "reservation_id": "reservation_id"},
    optional_scalar_fields={"related_participant_id": "related_participant_id", "related_equine_id": "related_equine_id"},
)
provider_to_response = lambda d: document_to_schema(d, ProviderResponseSchema, scalar_fields={"id": "id"})
policy_to_response = lambda d: document_to_schema(
    d, PolicyResponseSchema,
    scalar_fields={"id": "id", "reservation_id": "reservation_id"},
    optional_scalar_fields={"provider_id": "provider_id"},
)


# ---------------------------------------------------------------------------
# Complex mappers — custom resolution or nested structures
# ---------------------------------------------------------------------------

async def reservation_to_response(doc: ReservationDocument) -> ReservationResponseSchema:
    participants: list[ParticipantResponseSchema] = []
    if doc.participant_ids:
        participant_docs = await ParticipantDocument.find(
            {"_id": {"$in": doc.participant_ids}}
        ).to_list()
        for p in participant_docs:
            try:
                participants.append(participant_to_response(p))
            except Exception:
                logger.warning(
                    "[mapper] Failed to map participant | reservation=%s | participant=%s",
                    doc.id, p.id, exc_info=True,
                )

    payment_proofs: list[PaymentProofResponseSchema] = []
    if doc.payment_proof_ids:
        proof_docs = await PaymentProofDocument.find(
            {"_id": {"$in": doc.payment_proof_ids}}
        ).to_list()
        payment_proofs = [payment_proof_to_response(p) for p in proof_docs]

    data = doc.model_dump(exclude={"revision_id", "id", "participant_ids", "payment_proof_ids"})
    data["id"] = str(doc.id)
    data["experience_id"] = str(doc.experience_id) if doc.experience_id else None
    data["schedule_id"] = str(doc.schedule_id) if doc.schedule_id else None
    data["participants"] = participants
    data["payment_proofs"] = payment_proofs
    data["form_sent"] = doc.participant_form_sent_at is not None
    data["confirmation_message_sent"] = doc.confirmation_message_sent_at is not None
    return ReservationResponseSchema(**data)


def reservation_to_list_item(
    doc: ReservationDocument,
    enriched: dict | None = None,
) -> ReservationListItemSchema:
    data = doc.model_dump(exclude={"revision_id", "id"})
    data["id"] = str(doc.id)
    data["experience_id"] = str(doc.experience_id)
    data["schedule_id"] = str(doc.schedule_id) if doc.schedule_id else None
    if enriched:
        for key in ("experience_name", "scheduled_date", "start_time"):
            if key in enriched:
                data[key] = enriched[key]
    return ReservationListItemSchema(**data)


def participant_to_response(doc: ParticipantDocument) -> ParticipantResponseSchema:
    ec_raw = doc.emergency_contact
    ec_dict = ec_raw.model_dump() if hasattr(ec_raw, "model_dump") else ec_raw
    data = doc.model_dump(exclude={"revision_id", "id", "emergency_contact"})
    data["id"] = str(doc.id)
    data["emergency_contact"] = ec_dict
    data["experience_level"] = doc.experience_level.value if doc.experience_level else None
    return ParticipantResponseSchema.model_validate(data)


def form_link_to_status_response(
    doc: ParticipantFormLinkDocument,
) -> ParticipantFormLinkStatusResponse:
    data = doc.model_dump(exclude={"revision_id", "id", "reservation_id"})
    data["id"] = str(doc.id)
    data["reservation_id"] = str(doc.reservation_id)
    data["completed_participants"] = doc.used_count
    return ParticipantFormLinkStatusResponse(**data)
