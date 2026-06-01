from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_sync_service
from app.documents import UserDocument
from app.schemas.sync import (
    SyncPullRequestSchema,
    SyncPullResponseSchema,
    SyncPushRequestSchema,
    SyncPushResponseSchema,
)
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.get("/bootstrap", status_code=status.HTTP_200_OK, operation_id="getSyncBootstrap")
async def get_sync_bootstrap(
    current_user: Annotated[UserDocument, Depends(get_current_user)],
    service: SyncService = Depends(get_sync_service),
) -> dict:
    return await service.build_bootstrap(current_user=current_user)


@router.post(
    "/pull",
    response_model=SyncPullResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="pullSyncChanges",
)
async def pull_sync_changes(
    body: SyncPullRequestSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
    service: SyncService = Depends(get_sync_service),
) -> SyncPullResponseSchema:
    return await service.pull_changes(current_user=current_user, body=body)


@router.post(
    "/push",
    response_model=SyncPushResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="pushSyncOperations",
)
async def push_sync_operations(
    body: SyncPushRequestSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
    service: SyncService = Depends(get_sync_service),
) -> SyncPushResponseSchema:
    return await service.push_operations(current_user=current_user, body=body)
