from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from app.agents.state import GraphState
from app.agents.tools import (
    MongoDBVectorClient,
    create_ops_tools,
    create_tourist_tools,
)
from app.common.enums import UserRole
from app.services import (
    BookingService,
    EquineService,
    OpsService,
    ParticipantService,
    ReservationService,
    SaddleService,
    ScheduleService,
)


@dataclass
class NodeDependencies:
    chat_model: BaseChatModel
    ops_service: OpsService
    vector_client: MongoDBVectorClient
    booking_service: BookingService
    reservation_service: ReservationService
    participant_service: ParticipantService
    equine_service: EquineService
    schedule_service: ScheduleService
    saddle_service: SaddleService


def default_dependencies() -> NodeDependencies:
    return NodeDependencies(
        chat_model=ChatOpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="lm-studio",
            model="local-model",
            temperature=0,
        ),
        ops_service=OpsService(),
        vector_client=MongoDBVectorClient(),
        booking_service=BookingService(),
        reservation_service=ReservationService(),
        participant_service=ParticipantService(),
        equine_service=EquineService(),
        schedule_service=ScheduleService(),
        saddle_service=SaddleService(),
    )


def route_initial_by_role(state: GraphState) -> str:
    role = state.get("role", "unassigned")
    if role in {"guide", "admin"}:  # Solo personal autorizado va a operaciones
        return "ops_agent"
    return "tourist_agent"  # Clientes e invitados van a RAG/Booking


async def ops_agent_node(
    state: GraphState, deps: NodeDependencies, config: RunnableConfig
) -> dict[str, Any]:
    tools = create_ops_tools(
        ops_service=deps.ops_service,
        reservation_service=deps.reservation_service,
        participant_service=deps.participant_service,
        equine_service=deps.equine_service,
        schedule_service=deps.schedule_service,
        saddle_service=deps.saddle_service,
        vector_client=deps.vector_client,
    )
    llm_with_tools = deps.chat_model.bind_tools(tools)

    system_prompt = SystemMessage(
        content=(
            "Eres el agente operativo y administrativo de La Juana. "
            "Tu tarea principal es traducir las instrucciones naturales (coloquiales o campesinas) "
            "de los guías y administradores a llamadas estructuradas usando tu "
            "herramienta de administración. Si te preguntan dudas generales, tienes "
            "a tu disposición la herramienta de búsqueda operativa. Infieres correctamente "
            "la entidad y la acción solicitada, y confirmas al usuario de forma humanizada."
        )
    )

    messages = [system_prompt] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages, config)
    return {"messages": [response]}


async def tourist_agent_node(
    state: GraphState, deps: NodeDependencies, config: RunnableConfig
) -> dict[str, Any]:
    tools = create_tourist_tools(deps.booking_service, deps.vector_client)
    llm_with_tools = deps.chat_model.bind_tools(tools)

    system_prompt = SystemMessage(
        content=(
            "Eres el agente de atención de La Juana. "
            "Resuelve dudas sobre equinos/campo usando RAG y gestiona reservas."
        )
    )

    messages = [system_prompt] + state.get("messages", [])
    response = await llm_with_tools.ainvoke(messages, config)
    return {"messages": [response]}


def map_role_for_graph(user_role: UserRole) -> str:
    if user_role == UserRole.ADMIN:
        return "admin"
    if user_role == UserRole.GUIDE:
        return "guide"
    return "unassigned"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
