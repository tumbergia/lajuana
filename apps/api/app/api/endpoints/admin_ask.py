import traceback

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.api.deps import get_current_user
from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents import UserDocument
from app.schemas.ask import AskRequest, AskResponse


class AdminAskRequest(BaseModel):
    message: str = Field(min_length=1)
    from_phone: str | None = None
    conversation_id: str | None = None
    trace_id: str | None = None
    conversation_turn_id: str | None = None


router = APIRouter(tags=["Assistant"])


@router.post(
    "/admin/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat con acceso completo a herramientas administrativas",
    description=(
        "Endpoint protegido con JWT que permite usar todas las herramientas "
        "incluyendo las administrativas (admin_*, guide_*). "
        "Requiere autenticación con token de acceso válido y rol ADMIN. "
        "No disponible para clientes de WhatsApp."
    ),
)
async def admin_ask(
    request: AdminAskRequest,
    current_user: UserDocument = Depends(get_current_user),
) -> AskResponse:
    if current_user.role != UserRole.ADMIN:
        raise ApiError(
            status_code=403,
            code=ErrorCode.AUTH_FORBIDDEN,
            message="Se requiere rol de administrador para usar este endpoint.",
        )

    orchestrator = AssistantOrchestrator()
    try:
        ask_request = AskRequest(
            message=request.message,
            channel="admin_api",
            from_phone=request.from_phone or str(current_user.id),
            conversation_id=request.conversation_id,
            trace_id=request.trace_id,
            conversation_turn_id=request.conversation_turn_id,
        )
        return await orchestrator.ask(ask_request)
    except Exception:
        logger.error("Unhandled error in /admin/ask:\n%s", traceback.format_exc())
        raise