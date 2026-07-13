import traceback

from fastapi import APIRouter

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.core.logging import logger
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
    try:
        public_request = request.model_copy(update={"channel": "test"})
        return await orchestrator.ask(public_request)
    except Exception:
        logger.error("Unhandled error in /ask:\n%s", traceback.format_exc())
        raise
