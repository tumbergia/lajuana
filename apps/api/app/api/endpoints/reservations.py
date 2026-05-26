from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.participant import (
    ParticipantCreateSchema,
    ParticipantResponseSchema,
)
from app.schemas.payment_proof import PaymentProofCreateSchema, PaymentProofResponseSchema
from app.schemas.reservation import (
    ReservationAvailabilityResponseSchema,
    ReservationCancelSchema,
    ReservationConfirmSchema,
    ReservationCreateSchema,
    ReservationListItemSchema,
    ReservationResponseSchema,
    ReservationStatusTransitionSchema,
    ReservationUpdateSchema,
)
from app.services import (
    ParticipantService,
    PaymentProofService,
    ReservationService,
)
from beanie import PydanticObjectId

from app.documents import ExperienceDocument, ScheduleDocument
from app.services.mappers import (
    participant_to_response,
    payment_proof_to_response,
    reservation_to_list_item,
    reservation_to_response,
)

router = APIRouter(prefix="/reservations", tags=["Reservas"])
reservation_service = ReservationService()
participant_service = ParticipantService()
payment_proof_service = PaymentProofService()


@router.post(
    "",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["reservations_create"]["summary"],
    description=endpoint_description("reservations_create"),
    operation_id="createReservation",
    responses=endpoint_responses("reservations_create"),
)
async def create_reservation(
    payload: ReservationCreateSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_CREATE)),
    ],
) -> ReservationResponseSchema:
    doc = await reservation_service.create(payload.model_dump(), actor_id=current_user.id)
    return reservation_to_response(doc)


@router.get(
    "/availability",
    response_model=ReservationAvailabilityResponseSchema,
    summary=ENDPOINT_DOCS["reservations_availability"]["summary"],
    description=endpoint_description("reservations_availability"),
    operation_id="checkReservationAvailability",
    responses=endpoint_responses("reservations_availability"),
)
async def check_reservation_availability(
    date: date,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))],
) -> ReservationAvailabilityResponseSchema:
    availability = await reservation_service.check_availability(requested_date=date)
    return ReservationAvailabilityResponseSchema.model_validate(availability)


@router.get(
    "",
    response_model=list[ReservationListItemSchema],
    summary=ENDPOINT_DOCS["reservations_list"]["summary"],
    description=endpoint_description("reservations_list"),
    operation_id="listReservations",
    responses=endpoint_responses("reservations_list"),
)
async def list_reservations(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_READ)),
    ],
) -> list[ReservationListItemSchema]:
    docs = await reservation_service.list(actor_role=current_user.role)
    if not docs:
        return []

    # Batch-resolve experience names.
    exp_ids = list({str(d.experience_id) for d in docs})
    exp_criteria = {"_id": {"$in": [PydanticObjectId(eid) for eid in exp_ids]}}
    experiences = {
        str(e.id): e.name
        for e in await ExperienceDocument.find(exp_criteria).to_list()
    }

    # Batch-resolve schedule dates / times.
    sched_ids = list(
        {str(d.schedule_id) for d in docs if d.schedule_id}
    )
    schedule_map: dict[str, tuple[str, str]] = {}
    if sched_ids:
        sched_criteria = {"_id": {"$in": [PydanticObjectId(sid) for sid in sched_ids]}}
        for s in await ScheduleDocument.find(sched_criteria).to_list():
            schedule_map[str(s.id)] = (
                s.date.isoformat() if s.date else "",
                s.start_time.isoformat() if s.start_time else "",
            )

    items: list[ReservationListItemSchema] = []
    for doc in docs:
        eid = str(doc.experience_id)
        sid = str(doc.schedule_id) if doc.schedule_id else None
        sched_date, start_time = schedule_map.get(sid, ("", "")) if sid else ("", "")
        enriched: dict[str, object] = {}
        name = experiences.get(eid)
        if name:
            enriched["experience_name"] = name
        if sched_date:
            enriched["scheduled_date"] = sched_date
        if start_time:
            enriched["start_time"] = start_time
        items.append(reservation_to_list_item(doc, enriched=enriched))
    return items


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponseSchema,
    summary=ENDPOINT_DOCS["reservations_get"]["summary"],
    description=endpoint_description("reservations_get"),
    operation_id="getReservationById",
    responses=endpoint_responses("reservations_get"),
)
async def get_reservation(
    reservation_id: str,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_READ)),
    ],
) -> ReservationResponseSchema:
    doc = await reservation_service.get(reservation_id, actor_role=current_user.role)
    return reservation_to_response(doc)


@router.patch(
    "/{reservation_id}",
    response_model=ReservationResponseSchema,
    summary=ENDPOINT_DOCS["reservations_update"]["summary"],
    description=endpoint_description("reservations_update"),
    operation_id="updateReservationById",
    responses=endpoint_responses("reservations_update"),
)
async def update_reservation(
    reservation_id: str,
    payload: ReservationUpdateSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_UPDATE)),
    ],
) -> ReservationResponseSchema:
    doc = await reservation_service.update(
        reservation_id,
        payload.model_dump(exclude_none=True),
        actor_id=current_user.id,
    )
    return reservation_to_response(doc)


@router.post(
    "/{reservation_id}/confirm",
    response_model=ReservationResponseSchema,
    summary=ENDPOINT_DOCS["reservations_confirm"]["summary"],
    description=endpoint_description("reservations_confirm"),
    operation_id="confirmReservationById",
    responses=endpoint_responses("reservations_confirm"),
)
async def confirm_reservation(
    reservation_id: str,
    _: ReservationConfirmSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_CONFIRM)),
    ],
) -> ReservationResponseSchema:
    doc = await reservation_service.confirm_reservation(reservation_id, actor_id=current_user.id)
    return reservation_to_response(doc)


@router.post(
    "/{reservation_id}/status",
    response_model=ReservationResponseSchema,
    summary=ENDPOINT_DOCS["reservations_transition"]["summary"],
    description=endpoint_description("reservations_transition"),
    operation_id="transitionReservationStatusById",
    responses=endpoint_responses("reservations_transition"),
)
async def transition_reservation_status(
    reservation_id: str,
    payload: ReservationStatusTransitionSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_UPDATE)),
    ],
) -> ReservationResponseSchema:
    doc = await reservation_service.set_status(
        reservation_id,
        payload.target_status,
        actor_id=current_user.id,
    )
    return reservation_to_response(doc)


@router.post(
    "/{reservation_id}/cancel",
    response_model=ReservationResponseSchema,
    summary=ENDPOINT_DOCS["reservations_cancel"]["summary"],
    description=endpoint_description("reservations_cancel"),
    operation_id="cancelReservationById",
    responses=endpoint_responses("reservations_cancel"),
)
async def cancel_reservation(
    reservation_id: str,
    _: ReservationCancelSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_CANCEL)),
    ],
) -> ReservationResponseSchema:
    doc = await reservation_service.cancel_reservation(reservation_id, actor_id=current_user.id)
    return reservation_to_response(doc)


@router.post(
    "/{reservation_id}/payment-proofs",
    response_model=PaymentProofResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["reservation_payment_proofs_create"]["summary"],
    description=endpoint_description("reservation_payment_proofs_create"),
    operation_id="createPaymentProofForReservation",
    responses=endpoint_responses("reservation_payment_proofs_create"),
)
async def add_payment_proof(
    reservation_id: str,
    payload: PaymentProofCreateSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.PAYMENT_PROOF_CREATE)),
    ],
) -> PaymentProofResponseSchema:
    doc = await payment_proof_service.create(reservation_id, payload, actor_id=current_user.id)
    return payment_proof_to_response(doc)


@router.post(
    "/{reservation_id}/participants",
    response_model=ParticipantResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["participants_create"]["summary"],
    description=endpoint_description("participants_create"),
    operation_id="createParticipantForReservation",
    responses=endpoint_responses("participants_create"),
)
async def create_participant(
    reservation_id: str,
    payload: ParticipantCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PARTICIPANT_CREATE))],
) -> ParticipantResponseSchema:
    doc = await participant_service.create(reservation_id, payload)
    return participant_to_response(doc)



