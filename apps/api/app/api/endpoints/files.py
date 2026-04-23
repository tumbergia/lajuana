from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user
from app.documents import UserDocument
from app.schemas.file_upload import (
    FileCompleteUploadResponseSchema,
    FileInitUploadRequestSchema,
    FileInitUploadResponseSchema,
)
from app.services.file_upload_service import FileUploadService

router = APIRouter(prefix="/files", tags=["Files"])
service = FileUploadService()


@router.post(
    "/init-upload",
    response_model=FileInitUploadResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="initFileUpload",
)
async def init_upload(
    body: FileInitUploadRequestSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> FileInitUploadResponseSchema:
    return await service.init_upload(current_user=current_user, body=body)


@router.post(
    "/{upload_id}/complete",
    response_model=FileCompleteUploadResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="completeFileUpload",
)
async def complete_upload(
    upload_id: str,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> FileCompleteUploadResponseSchema:
    return await service.complete_upload(current_user=current_user, upload_id=upload_id)
