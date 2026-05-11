from dataclasses import dataclass
from datetime import UTC, datetime
import re
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
from app.core.config import settings
from app.common.enums import UserRole
from app.services import (
    BookingService,
    EquineService,
    ExperienceService,
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
    experience_service: ExperienceService
    schedule_service: ScheduleService
    saddle_service: SaddleService


def default_dependencies() -> NodeDependencies:
    return NodeDependencies(
        chat_model=ChatOpenAI(
            base_url=settings.chat_llm_base_url,
            api_key=settings.chat_llm_api_key or "lm-studio",
            model=settings.chat_llm_model_name,
            temperature=0,
        ),
        ops_service=OpsService(),
        vector_client=MongoDBVectorClient(),
        booking_service=BookingService(),
        reservation_service=ReservationService(),
        participant_service=ParticipantService(),
        equine_service=EquineService(),
        experience_service=ExperienceService(),
        schedule_service=ScheduleService(),
        saddle_service=SaddleService(),
    )


def route_initial_by_role(state: GraphState) -> str:
    role = state.get("role", "unassigned")
    if role in {"guide", "admin"}:  # Solo personal autorizado va a operaciones
        return "ops_agent"
    return "reservation_receive_message"  # Clientes e invitados van al flujo de reservas


def _looks_like_booking_intent(text: str) -> bool:
    normalized = text.lower()
    return bool(
        re.search(
            r"\b(reserv|reserva|cabalgata|experienc|cupo|fecha|personas?|pax|hora|horario)\b",
            normalized,
        )
    )


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
    messages = state.get("messages", [])
    last_user_text = messages[-1].content if messages else ""
    booking_intent = bool(state.get("booking_intent", False)) or _looks_like_booking_intent(
        str(last_user_text)
    )

    tools = create_tourist_tools(
        deps.booking_service,
        deps.vector_client,
        include_rag=not booking_intent,
    )
    llm_with_tools = deps.chat_model.bind_tools(tools)

    system_prompt = SystemMessage(
        content=(
            "Eres el agente de atención de La Juana. "
            "Resuelve dudas sobre equinos/campo usando RAG y gestiona reservas. "
            "Si el usuario expresa intención de reservar, prioriza obtener fecha, cantidad de personas "
            "y experiencia, y usa primero las herramientas de disponibilidad y creación de reserva. "
            "No uses búsqueda de conocimiento para mensajes cuyo objetivo principal sea reservar."
        )
    )

    messages = [system_prompt] + messages
    response = await llm_with_tools.ainvoke(messages, config)
    return {"messages": [response], "booking_intent": booking_intent}


def map_role_for_graph(user_role: UserRole) -> str:
    if user_role == UserRole.ADMIN:
        return "admin"
    if user_role == UserRole.GUIDE:
        return "guide"
    return "unassigned"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
