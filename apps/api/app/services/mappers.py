"""Schema mappers: document_to_schema helper + thin wrappers + complex mappers."""

import asyncio
import logging

from beanie import PydanticObjectId

from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ParticipantDocument,
    ParticipantFormLinkDocument,
    PaymentProofDocument,
    ReservationDocument,
    SaddleDocument,
)
from app.schemas.assignment import AssignmentResponseSchema
from app.schemas.auth import UserResponseSchema
from app.schemas.equine import EquineListItemSchema, EquineResponseSchema
from app.schemas.experience import ExperienceResponseSchema
from app.schemas.participant import ParticipantResponseSchema
from app.schemas.participant_form_link import ParticipantFormLinkStatusResponse
from app.schemas.payment_proof import PaymentProofResponseSchema
from app.schemas.policy import PolicyResponseSchema
from app.schemas.provider import ProviderListItemSchema, ProviderResponseSchema
from app.schemas.reservation import ReservationListItemSchema, ReservationResponseSchema
from app.schemas.saddle import SaddleListItemSchema, SaddleResponseSchema
from app.schemas.equine_event import EquineEventResponseSchema
from app.schemas.service_log import ServiceLogPhotoSchema, ServiceLogResponseSchema

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
payment_proof_to_response = lambda d: document_to_schema(d, PaymentProofResponseSchema, scalar_fields={"id": "id", "reservation_id": "reservation_id"})
equine_to_response = lambda d: document_to_schema(d, EquineResponseSchema, scalar_fields={"id": "id"})
equine_to_list_item = lambda d: document_to_schema(d, EquineListItemSchema, scalar_fields={"id": "id"})
saddle_to_response = lambda d: document_to_schema(d, SaddleResponseSchema, scalar_fields={"id": "id"})
saddle_to_list_item = lambda d: document_to_schema(d, SaddleListItemSchema, scalar_fields={"id": "id"})


async def batch_assignments_to_response(
    assignments: list[AssignmentDocument],
) -> list[AssignmentResponseSchema]:
    """Resuelve N assignments → 3 queries $in (participant, equine, saddle).

    Sin N+1. Colecta todos los IDs, hace queries batch, construye lookup maps.
    """
    if not assignments:
        return []

    # Colectar IDs únicos
    p_ids = list({
        a.participant_id for a in assignments if a.participant_id
    })
    e_ids = list({
        a.equine_id for a in assignments if a.equine_id
    })
    s_ids = list({
        a.saddle_id for a in assignments if a.saddle_id
    })

    # 3 queries $in en paralelo
    participants, equines, saddles = await asyncio.gather(
        ParticipantDocument.find({"_id": {"$in": p_ids}}).to_list() if p_ids else [],
        EquineDocument.find({"_id": {"$in": e_ids}}).to_list() if e_ids else [],
        SaddleDocument.find({"_id": {"$in": s_ids}}).to_list() if s_ids else [],
    )

    # Lookup maps
    p_map: dict[str, ParticipantDocument] = {str(p.id): p for p in participants}
    e_map: dict[str, EquineDocument] = {str(e.id): e for e in equines}
    s_map: dict[str, SaddleDocument] = {str(s.id): s for s in saddles}

    return [_map_assignment(a, p_map, e_map, s_map) for a in assignments]


def _map_assignment(
    doc: AssignmentDocument,
    p_map: dict[str, ParticipantDocument],
    e_map: dict[str, EquineDocument],
    s_map: dict[str, SaddleDocument],
) -> AssignmentResponseSchema:
    """Mapper sincrónico — construye schema desde documentos y lookups."""
    data = doc.model_dump(exclude={"revision_id"})
    data["id"] = str(doc.id)
    data["reservation_id"] = str(doc.reservation_id) if doc.reservation_id else None
    data["participant_id"] = str(doc.participant_id) if doc.participant_id else None
    data["equine_id"] = str(doc.equine_id) if doc.equine_id else None
    data["saddle_id"] = str(doc.saddle_id) if doc.saddle_id else None
    data["assigned_by_user_id"] = str(doc.assigned_by_user_id) if doc.assigned_by_user_id else None
    data["finalized_by_user_id"] = str(doc.finalized_by_user_id) if doc.finalized_by_user_id else None

    # Resolve names from lookup maps
    if doc.participant_id:
        p = p_map.get(str(doc.participant_id))
        data["participant_name"] = f"{p.first_name} {p.last_name}" if p else None
    if doc.equine_id:
        e = e_map.get(str(doc.equine_id))
        data["equine_name"] = e.name if e else None
    if doc.saddle_id:
        s = s_map.get(str(doc.saddle_id))
        data["saddle_label"] = (
            f"{s.code} - {s.name}" if s and s.code else (s.name if s else None)
        )

    return AssignmentResponseSchema(**data)


async def assignment_to_response(doc: AssignmentDocument) -> AssignmentResponseSchema:
    """Delega a batch (1 assignment → misma lógica, sin N+1)."""
    return (await batch_assignments_to_response([doc]))[0]
equine_event_to_response = lambda d: document_to_schema(
    d,
    EquineEventResponseSchema,
    scalar_fields={"id": "id", "equine_id": "equine_id"},
    optional_scalar_fields={
        "reservation_id": "reservation_id",
        "assignment_id": "assignment_id",
        "participant_id": "participant_id",
    },
)
def service_log_to_response(doc) -> ServiceLogResponseSchema:
    base = document_to_schema(
        doc,
        ServiceLogResponseSchema,
        scalar_fields={"id": "id", "reservation_id": "reservation_id"},
        optional_scalar_fields={
            "related_participant_id": "related_participant_id",
            "related_equine_id": "related_equine_id",
            "created_by": "created_by",
        },
        exclude_fields={"revision_id", "photos"},
    )
    photos = [
        ServiceLogPhotoSchema(
            index=index,
            storage_key=photo.storage_key,
            filename=photo.filename,
            content_type=photo.content_type,
            size_bytes=photo.size_bytes,
        )
        for index, photo in enumerate(getattr(doc, "photos", []) or [])
    ]
    return base.model_copy(update={"photos": photos})
provider_to_response = lambda d: document_to_schema(d, ProviderResponseSchema, scalar_fields={"id": "id"})
provider_to_list_item = lambda d: document_to_schema(d, ProviderListItemSchema, scalar_fields={"id": "id"})
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
    participant_docs: list[ParticipantDocument] = []
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
    if doc.requested_date and "scheduled_date" not in (enriched or {}):
        data["scheduled_date"] = doc.requested_date.isoformat()
    if enriched:
        for key in ("experience_name", "scheduled_date"):
            if key in enriched:
                data[key] = enriched[key]
    return ReservationListItemSchema(**data)


def participant_to_response(doc: ParticipantDocument) -> ParticipantResponseSchema:
    ec_raw = doc.emergency_contact
    ec_dict = ec_raw.model_dump() if hasattr(ec_raw, "model_dump") else ec_raw
    data = doc.model_dump(exclude={"revision_id", "id", "emergency_contact"})
    data["id"] = str(doc.id)
    data["reservation_id"] = str(doc.reservation_id)
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
