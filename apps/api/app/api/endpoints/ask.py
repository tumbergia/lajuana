from fastapi import APIRouter

from app.assistant.orchestrator import AssistantOrchestrator
from app.schemas.ask import AskRequest, AskResponse

router = APIRouter(tags=["Assistant"])


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Probar orquestador conversacional",
    description=(
        "Endpoint de prueba para validar intent detection, trazabilidad, ejecución de tools "
        "y composición de respuesta. No confirma reservas ni modifica cupos."
    ),
)
async def ask(request: AskRequest) -> AskResponse:
    orchestrator = AssistantOrchestrator()
    return await orchestrator.ask(request)
