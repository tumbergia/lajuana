"""Endpoints de solicitudes de rol."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_current_user, get_role_request_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission, RoleRequestStatus
from app.documents import UserDocument
from app.schemas.role_request import (
    RoleRequestCreateSchema,
    RoleRequestDecisionSchema,
    RoleRequestResponseSchema,
)
from app.services.role_request_service import RoleRequestService

router = APIRouter(prefix="/role-requests", tags=["Solicitudes de rol"])


@router.post(
    "",
    summary=ENDPOINT_DOCS["role_requests_create"]["summary"],
    description=endpoint_description("role_requests_create"),
    response_model=RoleRequestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    operation_id="createRoleRequest",
    responses=endpoint_responses("role_requests_create"),
)
async def create_role_request(
    payload: RoleRequestCreateSchema,
    actor: Annotated[
        UserDocument, Depends(require_permissions(Permission.ROLE_REQUEST_CREATE_SELF))
    ],
    service: RoleRequestService = Depends(get_role_request_service),
) -> RoleRequestResponseSchema:
    doc = await service.create_self_request(actor, payload)
    return await service.to_response(doc)


@router.get(
    "/me",
    summary=ENDPOINT_DOCS["role_requests_me"]["summary"],
    description=endpoint_description("role_requests_me"),
    response_model=RoleRequestResponseSchema | None,
    status_code=status.HTTP_200_OK,
    operation_id="getMyRoleRequest",
    responses=endpoint_responses("role_requests_me"),
)
async def get_my_role_request(
    actor: Annotated[UserDocument, Depends(get_current_user)],
    service: RoleRequestService = Depends(get_role_request_service),
) -> RoleRequestResponseSchema | None:
    doc = await service.get_my_request(actor)
    if doc is None:
        return None
    return await service.to_response(doc)


@router.get(
    "",
    summary=ENDPOINT_DOCS["role_requests_list"]["summary"],
    description=endpoint_description("role_requests_list"),
    response_model=list[RoleRequestResponseSchema],
    status_code=status.HTTP_200_OK,
    operation_id="listRoleRequests",
    responses=endpoint_responses("role_requests_list"),
)
async def list_role_requests(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.ROLE_REQUEST_READ))],
    response: Response,
    status_filter: RoleRequestStatus | None = Query(
        default=RoleRequestStatus.PENDING,
        alias="status",
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    service: RoleRequestService = Depends(get_role_request_service),
) -> list[RoleRequestResponseSchema]:
    total = await service.count_requests(status=status_filter)
    response.headers["X-Total-Count"] = str(total)
    docs = await service.list_requests(status=status_filter, limit=limit, skip=skip)
    return [await service.to_response(doc) for doc in docs]


@router.post(
    "/{request_id}/decide",
    summary=ENDPOINT_DOCS["role_requests_decide"]["summary"],
    description=endpoint_description("role_requests_decide"),
    response_model=RoleRequestResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="decideRoleRequest",
    responses=endpoint_responses("role_requests_decide"),
)
async def decide_role_request(
    request_id: str,
    payload: RoleRequestDecisionSchema,
    actor: Annotated[UserDocument, Depends(require_permissions(Permission.ROLE_REQUEST_MANAGE))],
    service: RoleRequestService = Depends(get_role_request_service),
) -> RoleRequestResponseSchema:
    doc = await service.decide(request_id, actor, payload)
    return await service.to_response(doc)
