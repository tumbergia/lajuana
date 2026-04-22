from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
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

router = APIRouter(prefix="/reservations", tags=["Reservations"])
reservation_service = ReservationService()
participant_service = ParticipantService()
payment_proof_service = PaymentProofService()


@router.post(
    "",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reserva",
    description="Crea una reserva dentro del flujo comercial y operativo.",
    operation_id="createReservation",
    responses=COMMON_AUTH_RESPONSES,
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
    "",
    response_model=list[ReservationListItemSchema],
    summary="Listar reservas",
    description="Lista reservas según alcance permitido por permisos.",
    operation_id="listReservations",
    responses=COMMON_AUTH_RESPONSES,
)
async def list_reservations(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_READ)),
    ],
) -> list[ReservationListItemSchema]:
    docs = await reservation_service.list(actor_role=current_user.role)
    return [reservation_to_list_item(doc) for doc in docs]


@router.get(
    "/{reservation_id}",
    response_model=ReservationResponseSchema,
    summary="Consultar reserva",
    description="Obtiene detalle consolidado de una reserva.",
    operation_id="getReservationById",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Actualizar reserva",
    description="Actualiza campos editables de la reserva.",
    operation_id="updateReservationById",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Confirmar reserva",
    description="Confirma reserva aplicando reglas de negocio críticas.",
    operation_id="confirmReservationById",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Transicionar estado de reserva",
    description="Cambia estado de reserva respetando máquina de estados.",
    operation_id="transitionReservationStatusById",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Cancelar reserva",
    description="Cancela reserva y revierte cupos si corresponde.",
    operation_id="cancelReservationById",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Adjuntar comprobante de pago",
    description="Asocia un comprobante de pago a la reserva.",
    operation_id="createPaymentProofForReservation",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Registrar participante en reserva",
    description="Crea participante vinculado a una reserva específica.",
    operation_id="createParticipantForReservation",
    responses=COMMON_AUTH_RESPONSES,
)
async def create_participant(
    reservation_id: str,
    payload: ParticipantCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PARTICIPANT_CREATE))],
) -> ParticipantResponseSchema:
    doc = await participant_service.create(reservation_id, payload)
    return participant_to_response(doc)
