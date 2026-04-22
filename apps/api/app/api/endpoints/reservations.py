from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.documents import UserDocument
from app.schemas.participant import ParticipantCreateSchema, ParticipantResponseSchema
from app.schemas.payment_proof import PaymentProofCreateSchema, PaymentProofResponseSchema
from app.schemas.reservation import (
    ReservationCancelSchema,
    ReservationConfirmSchema,
    ReservationCreateSchema,
    ReservationListItemSchema,
    ReservationResponseSchema,
    ReservationStatusTransitionSchema,
    ReservationUpdateSchema,
)
from app.services import ParticipantService, PaymentProofService, ReservationService
from app.services.mappers import (
    participant_to_response,
    payment_proof_to_response,
    reservation_to_list_item,
    reservation_to_response,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])
reservation_service = ReservationService()
participant_service = ParticipantService()
payment_proof_service = PaymentProofService()


@router.post("", response_model=ReservationResponseSchema, status_code=201)
async def create_reservation(
    payload: ReservationCreateSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ReservationResponseSchema:
    doc = await reservation_service.create(payload.model_dump(), actor_id=current_user.id)
    return reservation_to_response(doc)


@router.get("", response_model=list[ReservationListItemSchema])
async def list_reservations() -> list[ReservationListItemSchema]:
    docs = await reservation_service.list()
    return [reservation_to_list_item(doc) for doc in docs]


@router.get("/{reservation_id}", response_model=ReservationResponseSchema)
async def get_reservation(reservation_id: str) -> ReservationResponseSchema:
    doc = await reservation_service.get(reservation_id)
    return reservation_to_response(doc)


@router.patch("/{reservation_id}", response_model=ReservationResponseSchema)
async def update_reservation(
    reservation_id: str,
    payload: ReservationUpdateSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ReservationResponseSchema:
    doc = await reservation_service.update(
        reservation_id,
        payload.model_dump(exclude_none=True),
        actor_id=current_user.id,
    )
    return reservation_to_response(doc)


@router.post("/{reservation_id}/confirm", response_model=ReservationResponseSchema)
async def confirm_reservation(
    reservation_id: str,
    _: ReservationConfirmSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ReservationResponseSchema:
    doc = await reservation_service.confirm_reservation(reservation_id, actor_id=current_user.id)
    return reservation_to_response(doc)


@router.post("/{reservation_id}/status", response_model=ReservationResponseSchema)
async def transition_reservation_status(
    reservation_id: str,
    payload: ReservationStatusTransitionSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ReservationResponseSchema:
    doc = await reservation_service.set_status(
        reservation_id,
        payload.target_status,
        actor_id=current_user.id,
    )
    return reservation_to_response(doc)


@router.post("/{reservation_id}/cancel", response_model=ReservationResponseSchema)
async def cancel_reservation(
    reservation_id: str,
    _: ReservationCancelSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ReservationResponseSchema:
    doc = await reservation_service.cancel_reservation(reservation_id, actor_id=current_user.id)
    return reservation_to_response(doc)


@router.post(
    "/{reservation_id}/payment-proofs",
    response_model=PaymentProofResponseSchema,
    status_code=201,
)
async def add_payment_proof(
    reservation_id: str,
    payload: PaymentProofCreateSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> PaymentProofResponseSchema:
    doc = await payment_proof_service.create(reservation_id, payload, actor_id=current_user.id)
    return payment_proof_to_response(doc)


@router.post(
    "/{reservation_id}/participants",
    response_model=ParticipantResponseSchema,
    status_code=201,
)
async def create_participant(
    reservation_id: str,
    payload: ParticipantCreateSchema,
) -> ParticipantResponseSchema:
    doc = await participant_service.create(reservation_id, payload)
    return participant_to_response(doc)
