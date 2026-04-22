"""Router de asignaciones operativas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.assignment import (
    AssignmentCreateSchema,
    AssignmentResponseSchema,
    AssignmentUpdateSchema,
)
from app.services import AssignmentService
from app.services.mappers import assignment_to_response

router = APIRouter(prefix="/assignments", tags=["Assignments"])
service = AssignmentService()


@router.post(
    "",
    response_model=AssignmentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_AUTH_RESPONSES,
)
async def create_assignment(
    payload: AssignmentCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_CREATE))],
) -> AssignmentResponseSchema:
    return assignment_to_response(await service.create(payload))


@router.get(
    "/{assignment_id}",
    response_model=AssignmentResponseSchema,
    responses=COMMON_AUTH_RESPONSES,
)
async def get_assignment(
    assignment_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_READ))],
) -> AssignmentResponseSchema:
    return assignment_to_response(await service.get(assignment_id))


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentResponseSchema,
    responses=COMMON_AUTH_RESPONSES,
)
async def update_assignment(
    assignment_id: str,
    payload: AssignmentUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ASSIGNMENT_UPDATE))],
) -> AssignmentResponseSchema:
    return assignment_to_response(await service.update(assignment_id, payload))
