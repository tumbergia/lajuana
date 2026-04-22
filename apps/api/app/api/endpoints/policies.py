"""Router de pólizas asociadas a reservas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.policy import PolicyCreateSchema, PolicyResponseSchema, PolicyUpdateSchema
from app.services import PolicyService
from app.services.mappers import policy_to_response

router = APIRouter(prefix="/policies", tags=["Polizas"])
service = PolicyService()


@router.post(
    "",
    response_model=PolicyResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["policies_create"]["summary"],
    description=endpoint_description("policies_create"),
    operation_id="createPolicy",
    responses=endpoint_responses("policies_create"),
)
async def create_policy(
    payload: PolicyCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.POLICY_CREATE))],
) -> PolicyResponseSchema:
    return policy_to_response(await service.create(payload))


@router.get(
    "/{policy_id}",
    response_model=PolicyResponseSchema,
    summary=ENDPOINT_DOCS["policies_get"]["summary"],
    description=endpoint_description("policies_get"),
    operation_id="getPolicyById",
    responses=endpoint_responses("policies_get"),
)
async def get_policy(
    policy_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.POLICY_READ))],
) -> PolicyResponseSchema:
    return policy_to_response(await service.get(policy_id))


@router.patch(
    "/{policy_id}",
    response_model=PolicyResponseSchema,
    summary=ENDPOINT_DOCS["policies_update"]["summary"],
    description=endpoint_description("policies_update"),
    operation_id="updatePolicyById",
    responses=endpoint_responses("policies_update"),
)
async def update_policy(
    policy_id: str,
    payload: PolicyUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.POLICY_UPDATE))],
) -> PolicyResponseSchema:
    return policy_to_response(await service.update(policy_id, payload))
