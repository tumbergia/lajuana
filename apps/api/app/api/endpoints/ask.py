from fastapi import APIRouter

from app.assistant.orchestrator import AssistantOrchestrator
from app.schemas.ask import AskRequest, AskResponse

router = APIRouter(tags=["Assistant"])


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Probar assistant planner con Gemini y tools",
    description=(
        "Ejecuta el flujo conversacional: Gemini planner, policy engine, tool MCP de prueba "
        "y respuesta final. No confirma reservas ni modifica cupos."
    ),
)
async def ask(request: AskRequest) -> AskResponse:
    orchestrator = AssistantOrchestrator()
    return await orchestrator.ask(request)
