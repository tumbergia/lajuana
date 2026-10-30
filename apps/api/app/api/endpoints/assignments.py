"""Router de asignaciones operativas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_assignment_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.assignment import (
    AssignmentBoardResponseSchema,
    AssignmentCreateSchema,
    AssignmentReplaceSchema,
    AssignmentResponseSchema,
    AssignmentUpdateSchema,
    BatchUpdateSchema,
    BulkActionSchema,
)
from app.services import AssignmentService
from app.services.mappers import assignment_to_response

router = APIRouter(prefix="/assignments", tags=["Asignaciones"])


@router.post(
    "",
    response_model=AssignmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["assignments_create"]["summary"],
    description=endpoint_description("assignments_create"),
    operation_id="createAssignment",
    responses=endpoint_responses("assignments_create"),
)
async def create_assignment(
    payload: AssignmentCreateSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_CREATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return await assignment_to_response(
        await service.create(payload, actor_id=current_user.id, actor_role=current_user.role),
    )


@router.get(
    "/{assignment_id}",
    response_model=AssignmentResponseSchema,
    summary=ENDPOINT_DOCS["assignments_get"]["summary"],
    description=endpoint_description("assignments_get"),
    operation_id="getAssignmentById",
    responses=endpoint_responses("assignments_get"),
)
async def get_assignment(
    assignment_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_READ))],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return await assignment_to_response(await service.get(assignment_id))


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentResponseSchema,
    summary=ENDPOINT_DOCS["assignments_update"]["summary"],
    description=endpoint_description("assignments_update"),
    operation_id="updateAssignmentById",
    responses=endpoint_responses("assignments_update"),
)
async def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdateSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return await assignment_to_response(
        await service.update(assignment_id, payload, actor_id=current_user.id),
    )


@router.post(
    "/{assignment_id}/finalize",
    response_model=AssignmentResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Finalizar asignación",
    description="Cambia el estado de CONFIRMED a FINAL. Una vez finalizada, solo se permiten cambios de nota.",
    operation_id="finalizeAssignment",
    responses=endpoint_responses("assignments_finalize"),
)
async def finalize_assignment(
    assignment_id: str,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return await assignment_to_response(
        await service.finalize(assignment_id, actor_id=current_user.id),
    )


@router.post(
    "/{assignment_id}/unfinalize",
    response_model=AssignmentResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Revertir finalizacion de asignacion",
    description="Cambia el estado de FINAL a CONFIRMED. Solo administradores.",
    operation_id="unfinalizeAssignment",
    responses=endpoint_responses("assignments_unfinalize"),
)
async def unfinalize_assignment(
    assignment_id: str,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return await assignment_to_response(
        await service.unfinalize(assignment_id, actor_id=current_user.id),
    )


@router.delete(
    "/{assignment_id}",
    response_model=AssignmentResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Quitar asignacion",
    description="Marca la asignacion como cancelada y la saca del tablero. Solo administradores.",
    operation_id="deleteAssignment",
    responses=endpoint_responses("assignments_delete"),
)
async def delete_assignment(
    assignment_id: str,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return await assignment_to_response(
        await service.remove(assignment_id, actor_id=current_user.id),
    )


@router.post(
    "/{assignment_id}/replace",
    response_model=AssignmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Reemplazar asignación (admin)",
    description="Reemplaza una asignación finalizada: desactiva la actual y crea una nueva. Solo admin.",
    operation_id="replaceAssignment",
    responses=endpoint_responses("assignments_replace"),
)
async def replace_assignment(
    assignment_id: str,
    payload: AssignmentReplaceSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.ASSIGNMENT_CREATE, Permission.ASSIGNMENT_UPDATE)),
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return await assignment_to_response(
        await service.replace(
            assignment_id, payload, actor_id=current_user.id, actor_role=current_user.role
        ),
    )


@router.get(
    "/board/{reservation_id}",
    response_model=AssignmentBoardResponseSchema,
    summary="Tablero de asignación por reserva",
    description="Retorna participantes, asignaciones activas, equinos y sillas disponibles en una sola llamada.",
    operation_id="getAssignmentBoard",
    responses=endpoint_responses("assignments_board"),
)
async def get_assignment_board(
    reservation_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_READ))],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentBoardResponseSchema:
    return await service.get_board(reservation_id)


@router.post(
    "/reservation/{reservation_id}/finalize-all",
    response_model=AssignmentBoardResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Finalizar todas las asignaciones",
    description="Finaliza todas las asignaciones confirmadas de la reserva. Opcionalmente registra una observación.",
    operation_id="finalizeAllAssignments",
)
async def finalize_all_assignments(
    reservation_id: str,
    payload: BulkActionSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentBoardResponseSchema:
    return await service.finalize_all(
        reservation_id,
        actor_id=current_user.id,
        notes=payload.notes,
    )


@router.post(
    "/reservation/{reservation_id}/unfinalize-all",
    response_model=AssignmentBoardResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Revertir todas las finalizaciones",
    description="Revierte todas las asignaciones finalizadas de la reserva a confirmadas. Opcionalmente registra una observación.",
    operation_id="unfinalizeAllAssignments",
)
async def unfinalize_all_assignments(
    reservation_id: str,
    payload: BulkActionSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentBoardResponseSchema:
    return await service.unfinalize_all(
        reservation_id,
        actor_id=current_user.id,
        notes=payload.notes,
    )


@router.post(
    "/reservation/{reservation_id}/batch",
    response_model=AssignmentBoardResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Batch update assignments",
    description="Procesa asignaciones en batch (local-first flow): crea/actualiza y finaliza asignaciones, cancela removals, registra observación.",
    operation_id="batchUpdateAssignments",
)
async def batch_update_assignments(
    reservation_id: str,
    payload: BatchUpdateSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))
    ],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentBoardResponseSchema:
    return await service.batch_update(
        reservation_id,
        assignments=[a.model_dump() for a in payload.assignments],
        removals=payload.removals,
        notes=payload.notes,
        actor_id=current_user.id,
    )
