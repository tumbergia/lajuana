"""Router de pólizas asociadas a reservas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.policy import PolicyCreateSchema, PolicyResponseSchema, PolicyUpdateSchema
from app.services import PolicyService
from app.services.mappers import policy_to_response

router = APIRouter(prefix="/policies", tags=["Policies"])
service = PolicyService()


@router.post(
    "",
    response_model=PolicyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_AUTH_RESPONSES,
)
async def create_policy(
    payload: PolicyCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.POLICY_CREATE))],
) -> PolicyResponseSchema:
    return policy_to_response(await service.create(payload))


@router.get("/{policy_id}", response_model=PolicyResponseSchema, responses=COMMON_AUTH_RESPONSES)
async def get_policy(
    policy_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.POLICY_READ))],
) -> PolicyResponseSchema:
    return policy_to_response(await service.get(policy_id))


@router.patch("/{policy_id}", response_model=PolicyResponseSchema, responses=COMMON_AUTH_RESPONSES)
async def update_policy(
    policy_id: str,
    payload: PolicyUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.POLICY_UPDATE))],
) -> PolicyResponseSchema:
    return policy_to_response(await service.update(policy_id, payload))
