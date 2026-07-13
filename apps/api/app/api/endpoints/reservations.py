from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import (
    get_participant_service,
    get_payment_proof_service,
    get_reservation_provider_service,
    get_reservation_service,
    get_reservation_timeline_service,
    require_permissions,
)
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import PaymentStatus, Permission
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ReservationDocument, UserDocument
from app.schemas.participant import (
    ParticipantCreateSchema,
    ParticipantResponseSchema,
)
from app.schemas.payment_proof import PaymentProofCreateSchema, PaymentProofResponseSchema
from app.schemas.reservation import (
    ReservationApprovePaymentSchema,
    ReservationAvailabilityResponseSchema,
    ReservationCancelSchema,
    ReservationConfirmSchema,
    ReservationCreateSchema,
    ReservationListItemSchema,
    ReservationResponseSchema,
    ReservationSelfCancelSchema,
    ReservationStatusTransitionSchema,
    ReservationUpdateSchema,
)
from app.schemas.reservation_provider import (
    ReservationProviderCreateSchema,
    ReservationProviderTabItemSchema,
    ReservationProviderUpdateSchema,
)
from app.schemas.reservation_timeline import ReservationTimelineEntrySchema
from app.services import (
    ParticipantService,
    PaymentProofService,
    ReservationProviderService,
    ReservationService,
)
from app.services.reservation_timeline_service import ReservationTimelineService
from beanie import PydanticObjectId

from app.documents import ExperienceDocument
from app.services.mappers import (
    participant_to_response,
    payment_proof_to_response,
    reservation_to_list_item,
    reservation_to_response,
)

router = APIRouter(prefix="/reservations", tags=["Reservas"])


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
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.create(payload.model_dump(), actor_id=current_user.id)
    return await reservation_to_response(doc)


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
    reservation_service: ReservationService = Depends(get_reservation_service),
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
    include_deleted: bool = Query(default=False, description="Incluir reservas borradas logicamente"),
    assistant_disabled: bool | None = Query(
        default=None,
        description="Filtrar por asistente desactivado en la reserva",
    ),
    limit: int = Query(default=200, ge=1, le=1000, description="Max items"),
    skip: int = Query(default=0, ge=0, description="Items to skip"),
    reservation_service: ReservationService = Depends(get_reservation_service),
    response: Response = None,
) -> list[ReservationListItemSchema]:
    total = await reservation_service.count(
        actor_role=current_user.role,
        include_deleted=include_deleted,
        assistant_disabled=assistant_disabled,
    )
    response.headers["X-Total-Count"] = str(total)

    docs = await reservation_service.list(
        actor_role=current_user.role,
        include_deleted=include_deleted,
        assistant_disabled=assistant_disabled,
        limit=limit,
        skip=skip,
    )
    if not docs:
        return []

    # Batch-resolve experience names.
    exp_ids = list({str(d.experience_id) for d in docs})
    exp_criteria = {"_id": {"$in": [PydanticObjectId(eid) for eid in exp_ids]}}
    experiences = {
        str(e.id): e.name
        for e in await ExperienceDocument.find(exp_criteria).to_list()
    }

    items: list[ReservationListItemSchema] = []
    for doc in docs:
        eid = str(doc.experience_id)
        enriched: dict[str, object] = {}
        name = experiences.get(eid)
        if name:
            enriched["experience_name"] = name
        if doc.requested_date:
            enriched["scheduled_date"] = doc.requested_date.isoformat()
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
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.get(reservation_id, actor_role=current_user.role)
    return await reservation_to_response(doc)


@router.get(
    "/{reservation_id}/timeline",
    response_model=list[ReservationTimelineEntrySchema],
    summary=ENDPOINT_DOCS["reservations_timeline"]["summary"],
    description=endpoint_description("reservations_timeline"),
    operation_id="getReservationTimeline",
    responses=endpoint_responses("reservations_timeline"),
)
async def get_reservation_timeline(
    reservation_id: str,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_READ)),
    ],
    timeline_service: ReservationTimelineService = Depends(get_reservation_timeline_service),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ReservationTimelineEntrySchema]:
    return await timeline_service.get_timeline(
        reservation_id,
        actor_role=current_user.role,
        limit=limit,
    )


@router.get(
    "/{reservation_id}/providers",
    response_model=list[ReservationProviderTabItemSchema],
    summary=ENDPOINT_DOCS["reservations_providers_list"]["summary"],
    description=endpoint_description("reservations_providers_list"),
    operation_id="listReservationProviders",
    responses=endpoint_responses("reservations_providers_list"),
)
async def list_reservation_providers(
    reservation_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))],
    service: ReservationProviderService = Depends(get_reservation_provider_service),
) -> list[ReservationProviderTabItemSchema]:
    return await service.list_for_reservation(reservation_id)


@router.post(
    "/{reservation_id}/providers",
    response_model=ReservationProviderTabItemSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["reservations_providers_create"]["summary"],
    description=endpoint_description("reservations_providers_create"),
    operation_id="createReservationProvider",
    responses=endpoint_responses("reservations_providers_create"),
)
async def create_reservation_provider(
    reservation_id: str,
    payload: ReservationProviderCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.RESERVATION_UPDATE))],
    service: ReservationProviderService = Depends(get_reservation_provider_service),
) -> ReservationProviderTabItemSchema:
    return await service.create_for_reservation(reservation_id, payload)


@router.patch(
    "/{reservation_id}/providers/{reservation_provider_id}",
    response_model=ReservationProviderTabItemSchema,
    summary=ENDPOINT_DOCS["reservations_providers_update"]["summary"],
    description=endpoint_description("reservations_providers_update"),
    operation_id="updateReservationProvider",
    responses=endpoint_responses("reservations_providers_update"),
)
async def update_reservation_provider(
    reservation_id: str,
    reservation_provider_id: str,
    payload: ReservationProviderUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.RESERVATION_UPDATE))],
    service: ReservationProviderService = Depends(get_reservation_provider_service),
) -> ReservationProviderTabItemSchema:
    return await service.update_for_reservation(
        reservation_id,
        reservation_provider_id,
        payload,
    )


@router.delete(
    "/{reservation_id}/providers/{reservation_provider_id}",
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["reservations_providers_delete"]["summary"],
    description=endpoint_description("reservations_providers_delete"),
    operation_id="deleteReservationProvider",
    responses=endpoint_responses("reservations_providers_delete"),
)
async def delete_reservation_provider(
    reservation_id: str,
    reservation_provider_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.RESERVATION_UPDATE))],
    service: ReservationProviderService = Depends(get_reservation_provider_service),
) -> None:
    await service.delete_for_reservation(reservation_id, reservation_provider_id)


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
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.update(
        reservation_id,
        payload.model_dump(exclude_none=True),
        actor_id=current_user.id,
    )
    return await reservation_to_response(doc)


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
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.confirm_reservation(reservation_id, actor_id=current_user.id)
    return await reservation_to_response(doc)


@router.post(
    "/{reservation_id}/approve-payment",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Aprobar pago sin comprobante (pago físico/externo)",
    description=(
        "Marca el pago de una reserva como verificado SIN requerir un comprobante "
        "subido. Útil para pagos físicos, transferencias externas o casos donde el "
        "cliente paga en sitio. Genera el form link y notifica al cliente por WhatsApp."
    ),
    operation_id="approvePaymentWithoutProofByReservationId",
)
async def approve_payment_without_proof(
    reservation_id: str,
    payload: ReservationApprovePaymentSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.PAYMENT_VERIFY)),
    ],
    payment_proof_service: PaymentProofService = Depends(get_payment_proof_service),
) -> ReservationResponseSchema:
    reservation = await payment_proof_service.approve_payment_without_proof(
        reservation_id,
        actor_id=current_user.id,
        actor_role=current_user.role,
        note=payload.note,
    )
    return await reservation_to_response(reservation)


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
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.set_status(
        reservation_id,
        payload.target_status,
        actor_id=current_user.id,
    )
    return await reservation_to_response(doc)


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
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.cancel_reservation(reservation_id, actor_id=current_user.id)
    return await reservation_to_response(doc)


@router.delete(
    "/{reservation_id}",
    response_model=ReservationResponseSchema,
    summary="Borrar reserva (borrado lógico)",
    description="Establece deleted_at para ocultar la reserva de listados activos. No la elimina físicamente.",
    operation_id="deleteReservation",
    responses={
        200: {"description": "Reserva borrada lógicamente."},
        401: {"description": "No autenticado."},
        404: {"description": "Reserva no encontrada."},
    },
)
async def delete_reservation(
    reservation_id: str,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_DELETE)),
    ],
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.soft_delete(reservation_id)
    return await reservation_to_response(doc)


@router.post(
    "/{reservation_id}/restore",
    response_model=ReservationResponseSchema,
    summary="Restaurar reserva borrada",
    description="Quita el deleted_at para que la reserva vuelva a aparecer en listados activos.",
    operation_id="restoreReservation",
    responses={
        200: {"description": "Reserva restaurada."},
        401: {"description": "No autenticado."},
        404: {"description": "Reserva no encontrada."},
    },
)
async def restore_reservation(
    reservation_id: str,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.RESERVATION_UPDATE)),
    ],
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    doc = await reservation_service.restore(reservation_id)
    return await reservation_to_response(doc)


@router.post(
    "/self-cancel",
    response_model=ReservationResponseSchema,
    summary="Cancelar reserva propia",
    description="Permite al titular de una reserva cancelarla por su propia cuenta si aún no ha realizado el pago.",
    operation_id="selfCancelReservation",
)
async def self_cancel_reservation(
    payload: ReservationSelfCancelSchema,
    reservation_service: ReservationService = Depends(get_reservation_service),
) -> ReservationResponseSchema:
    reservation = await ReservationDocument.find_one({
        "code": payload.reservation_code,
        "holder_phone": payload.holder_phone,
    })
    if reservation is None:
        raise ApiError(
            status_code=404,
            code=ErrorCode.RESERVATION_NOT_FOUND,
            message="Reserva no encontrada.",
        )
    if reservation.payment_status != PaymentStatus.PENDING:
        raise ApiError(
            status_code=409,
            code=ErrorCode.RESERVATION_INVALID_STATUS_TRANSITION,
            message="Solo se pueden cancelar reservas con pago pendiente.",
        )
    doc = await reservation_service.cancel_reservation(
        str(reservation.id),
        actor_id=None,
    )
    return await reservation_to_response(doc)


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
    payment_proof_service: PaymentProofService = Depends(get_payment_proof_service),
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
    participant_service: ParticipantService = Depends(get_participant_service),
) -> ParticipantResponseSchema:
    doc = await participant_service.create(reservation_id, payload)
    return participant_to_response(doc)



