import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from beanie import PydanticObjectId
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from app.agents.state import GraphState
from app.agents.tools import (
    StubVectorClient,
    classify_booking_intent,
    extract_booking_request,
    extract_service_log_payload,
    get_last_user_text,
)
from app.common.enums import UserRole
from app.core.errors import ApiError
from app.schemas.service_log import ServiceLogCreateSchema
from app.services import BookingService, OpsService


class StructuredExtractionLLM:
    def with_structured_output(self, schema_type: type[ServiceLogCreateSchema]):
        async def extractor(text: str) -> ServiceLogCreateSchema:
            payload = extract_service_log_payload(text)
            return schema_type(**payload)

        return extractor


@dataclass
class NodeDependencies:
    ops_llm: StructuredExtractionLLM
    ops_service: OpsService
    vector_client: StubVectorClient
    booking_service: BookingService


def default_dependencies() -> NodeDependencies:
    return NodeDependencies(
        ops_llm=StructuredExtractionLLM(),
        ops_service=OpsService(),
        vector_client=StubVectorClient(),
        booking_service=BookingService(),
    )


def route_initial_by_role(state: GraphState) -> str:
    role = state.get("role", "customer")
    if role in {"guide", "admin"}: # Solo personal autorizado va a operaciones
        return "ops"
    return "tourist" # Clientes e invitados van a RAG/Booking


async def extract_ops_node(state: GraphState, deps: NodeDependencies) -> dict[str, Any]:
    text = get_last_user_text(state.get("messages", []))
    extractor = deps.ops_llm.with_structured_output(ServiceLogCreateSchema)
    try:
        extracted = await extractor(text)
        return {
            "extracted_data": extracted.model_dump(mode="python"),
        }
    except ValidationError as exc:
        missing_fields = []
        for error in exc.errors():
            if error.get("type") == "missing":
                location = error.get("loc", [])
                if location:
                    missing_fields.append(str(location[-1]))
        return {
            "extracted_data": {
                "_error": "structured_extraction_failed",
                "_missing": sorted(set(missing_fields)),
            },
        }


async def validate_ops_node(state: GraphState) -> dict[str, Any]:
    data = dict(state.get("extracted_data", {}))
    required_fields = ("reservation_id", "event_type", "happened_at")
    missing = [field for field in required_fields if not data.get(field)]
    missing.extend(data.get("_missing", []))
    data["_missing"] = sorted(set(missing))
    data["_is_valid"] = len(data["_missing"]) == 0 and "_error" not in data
    return {"extracted_data": data}


def route_ops_validation(state: GraphState) -> str:
    extracted_data = state.get("extracted_data", {})
    return "save" if bool(extracted_data.get("_is_valid")) else "feedback"


async def ops_feedback_node(state: GraphState) -> dict[str, Any]:
    missing = state.get("extracted_data", {}).get("_missing", [])
    if not missing:
        missing = ["reservation_id", "event_type", "happened_at"]
    message = (
        "Necesito completar estos datos para registrar la bitácora: "
        + ", ".join(missing)
        + "."
    )
    return {"messages": [AIMessage(content=message)]}


async def save_ops_node(state: GraphState, deps: NodeDependencies) -> dict[str, Any]:
    raw_data = {
        key: value
        for key, value in state.get("extracted_data", {}).items()
        if not str(key).startswith("_")
    }

    try:
        payload = ServiceLogCreateSchema.model_validate(raw_data)
        document = await deps.ops_service.create_log(payload)
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Bitácora registrada exitosamente. "
                        f"ID del log: {document.id}."
                    )
                )
            ]
        }
    except ApiError as exc:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "No pude registrar la bitácora. "
                        f"Código: {exc.code}."
                    )
                )
            ]
        }


async def rag_node(state: GraphState, deps: NodeDependencies) -> dict[str, Any]:
    text = get_last_user_text(state.get("messages", []))
    context = await deps.vector_client.search(text)
    return {"rag_context": context}


async def classify_intent_node(state: GraphState) -> dict[str, Any]:
    text = get_last_user_text(state.get("messages", []))
    intent = classify_booking_intent(text)
    return {"booking_intent": intent}


def route_tourist_intent(state: GraphState) -> str:
    return "booking" if state.get("booking_intent") else "answer"


async def rag_answer_node(state: GraphState) -> dict[str, Any]:
    context = state.get("rag_context") or "No encontré contexto adicional para responder."
    return {
        "messages": [
            AIMessage(
                content=(
                    "Esto es lo que encontré para tu consulta:\n"
                    f"{context}"
                )
            )
        ]
    }


def _extract_actor_id(user_id: str | None) -> PydanticObjectId | None:
    if not user_id:
        return None
    if not re.fullmatch(r"[a-fA-F0-9]{24}", user_id):
        return None
    return PydanticObjectId(user_id)


async def booking_node(state: GraphState, deps: NodeDependencies) -> dict[str, Any]:
    text = get_last_user_text(state.get("messages", []))
    booking_input = extract_booking_request(text)

    experience_id = booking_input.get("experience_id")
    if not experience_id:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Para continuar con la reserva necesito experience_id "
                        "(formato ObjectId de 24 caracteres)."
                    )
                )
            ]
        }

    participant_count = int(booking_input.get("participant_count", 1))
    requested_date = booking_input.get("requested_date")

    schedule = await deps.booking_service.get_available_schedule(
        experience_id=str(experience_id),
        requested_date=requested_date,
        participant_count=participant_count,
    )
    if schedule is None:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "No encontré cupo disponible para esa experiencia con la fecha/cupos solicitados."
                    )
                )
            ]
        }

    try:
        reservation = await deps.booking_service.create_pending_reservation(
            experience_id=str(experience_id),
            schedule_id=str(schedule.id),
            participant_count=participant_count,
            requested_date=requested_date,
            holder_name=booking_input.get("holder_name"),
            holder_email=booking_input.get("holder_email"),
            holder_phone=booking_input.get("holder_phone"),
            actor_id=_extract_actor_id(state.get("user_id")),
        )
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Reserva creada en estado pending_payment. "
                        f"Código: {reservation.code}, reserva: {reservation.id}."
                    )
                )
            ],
            "booking_intent": True,
        }
    except ApiError as exc:
        return {
            "messages": [
                AIMessage(
                    content=(
                        "No pude crear la reserva pendiente. "
                        f"Código: {exc.code}."
                    )
                )
            ]
        }


def map_role_for_graph(user_role: UserRole) -> str:
    if user_role == UserRole.ADMIN:
        return "admin"
    if user_role == UserRole.GUIDE:
        return "guide"
    return "customer"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()
