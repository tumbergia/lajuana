"""Router de asignaciones operativas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_assignment_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.assignment import (
    AssignmentCreateSchema,
    AssignmentResponseSchema,
    AssignmentUpdateSchema,
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
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_CREATE))],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return assignment_to_response(await service.create(payload))


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
    return assignment_to_response(await service.get(assignment_id))


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
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))],
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponseSchema:
    return assignment_to_response(await service.update(assignment_id, payload))
