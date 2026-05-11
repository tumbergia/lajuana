from datetime import date
from typing import Literal, Sequence

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from openai import AsyncOpenAI

from app.agents.handlers import (
    EquineHandler,
    ReservationHandler,
    SaddleHandler,
    ScheduleHandler,
    ServiceLogHandler,
)
from app.core.config import settings
from app.core.errors import ApiError
from app.services import (
    BookingService,
    EquineService,
    OpsService,
    ParticipantService,
    ReservationService,
    SaddleService,
    ScheduleService,
)

RAG_UNAVAILABLE_MESSAGE = (
    "No pude consultar la base de conocimientos en este momento. "
    "Sigue con el flujo de reserva usando disponibilidad, fecha, número de personas y datos de contacto."
)


def _normalize_embedding_input(text: str | Sequence[str]) -> str | list[str]:
    if isinstance(text, str):
        return text
    if isinstance(text, (list, tuple)):
        if not all(isinstance(item, str) for item in text):
            raise ValueError("Embedding query list items must all be strings.")
        return list(text)
    raise ValueError("Vector search query must be a string or a list of strings.")


class MongoDBVectorClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.chat_embedding_api_key,
            base_url=settings.chat_embedding_base_url,
        )

    async def search(
        self,
        query: str | list[str],
        scope: Literal["public", "ops"] | list[Literal["public", "ops"]] = "public",
    ) -> str:
        try:
            from app.documents import KnowledgeDocument

            query = _normalize_embedding_input(query)

            response = await self.client.embeddings.create(
                model=settings.chat_embedding_model,
                input=query,
            )
            query_vector = response.data[0].embedding
            allowed_scopes = [scope] if isinstance(scope, str) else scope

            pipeline = [
                {
                    "$vectorSearch": {
                        "index": settings.chat_vector_index_name,
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": settings.chat_vector_top_k * 10,
                        "limit": settings.chat_vector_top_k,
                        "filter": {"scope": {"$in": allowed_scopes}},
                    }
                },
                {
                    "$project": {
                        "text": 1,
                        "source": 1,
                        "scope": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]

            collection = KnowledgeDocument.get_motor_collection()
            results = await collection.aggregate(pipeline).to_list(length=settings.chat_vector_top_k)

            if not results:
                return "No se encontró información relevante en la base de conocimientos."

            texts = [
                f"Fuente ({res.get('scope', 'unknown')}): {res.get('text', '')}" for res in results
            ]
            return "\n\n".join(texts)
        except ValueError:
            raise
        except Exception:
            return RAG_UNAVAILABLE_MESSAGE


def get_last_user_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if message.type == "human":
            return str(message.content)
    return ""


def create_ops_tools(
    ops_service: OpsService,
    reservation_service: ReservationService,
    participant_service: ParticipantService,
    equine_service: EquineService,
    schedule_service: ScheduleService,
    saddle_service: SaddleService,
    vector_client: MongoDBVectorClient,
):
    handlers = {
        "equinos": EquineHandler(equine_service),
        "reservas": ReservationHandler(reservation_service, participant_service),
        "sillas": SaddleHandler(saddle_service),
        "bitacora": ServiceLogHandler(ops_service, reservation_service),
        "agendas": ScheduleHandler(schedule_service),
    }

    @tool
    async def ejecutar_accion_administrativa(
        entidad: Literal["equinos", "reservas", "sillas", "bitacora", "agendas"],
        accion: Literal["crear", "consultar", "actualizar", "anular"],
        parametros_busqueda: dict,
        datos_cambio: dict,
    ) -> str:
        """
        Usa esta herramienta cuando un administrador o guía solicite registrar, modificar,
        consultar o anular cualquier dato del sistema (equinos, sillas, pagos, novedades, agendas).
        Traduce el lenguaje coloquial a la acción técnica correspondiente.
        - entidad: El tipo de registro a afectar ("equinos", "reservas", "sillas", "bitacora", "agendas").
        - accion: Lo que se desea hacer ("crear", "consultar", "actualizar", "anular").
        - parametros_busqueda: Diccionario para localizar el registro (Ej: {"nombre": "Rayo"}, {"codigo": "RES-123"}).
        - datos_cambio: Diccionario con la nueva información o parámetros extraídos del texto
          (Ej: {"is_available": false, "health_notes": "cojo", "event_type": "INCIDENT", "notes": "Equino desbocó"}).
        """
        try:
            handler = handlers.get(entidad)
            if not handler:
                return f"No sé cómo manejar la entidad '{entidad}'."

            method = getattr(handler, accion, None)
            if not method:
                return f"La acción '{accion}' no está disponible para '{entidad}'."

            return await method(parametros_busqueda, datos_cambio)
        except Exception as e:
            return f"Error al ejecutar la acción: {str(e)}"

    @tool
    async def search_ops_information(query: str) -> str:
        """Busca información operativa, reglas de negocio o detalles de equinos y operaciones."""
        return await vector_client.search(query, scope=["public", "ops"])

    return [ejecutar_accion_administrativa, search_ops_information]


def create_tourist_tools(
    booking_service: BookingService,
    vector_client: MongoDBVectorClient,
    include_rag: bool = True,
):
    tools = []

    if include_rag:
        @tool
        async def search_information(query: str) -> str:
            """
            Busca información de contexto o RAG para responder preguntas
            sobre La Juana, equinos o el campo.
            """
            return await vector_client.search(query, scope="public")

        tools.append(search_information)

    @tool
    async def get_available_schedule(
        experience_id: str, participant_count: int, requested_date: str
    ) -> dict:
        """Consulta la disponibilidad de agenda para una experiencia."""
        parsed_date = date.fromisoformat(requested_date) if requested_date else None
        schedule = await booking_service.get_available_schedule(
            experience_id=experience_id,
            requested_date=parsed_date,
            participant_count=participant_count,
        )
        if not schedule:
            return {"success": False, "reason": "no_free_date"}
        return {
            "success": True,
            "schedule_id": str(schedule.id),
            "reason": "free_date_found",
        }

    @tool
    async def create_pending_reservation(
        experience_id: str,
        schedule_id: str,
        participant_count: int,
        requested_date: str,
        holder_name: str,
        holder_email: str,
        holder_phone: str,
        actor_id: str | None = None,
    ) -> str:
        """Crea una reserva en estado pendiente usando schedule_id previamente verificado."""
        try:
            import re

            from beanie import PydanticObjectId

            parsed_actor_id = None
            if actor_id and re.fullmatch(r"[a-fA-F0-9]{24}", actor_id):
                parsed_actor_id = PydanticObjectId(actor_id)

            reservation = await booking_service.create_pending_reservation(
                experience_id=experience_id,
                schedule_id=schedule_id,
                participant_count=participant_count,
                requested_date=date.fromisoformat(requested_date) if requested_date else None,
                holder_name=holder_name,
                holder_email=holder_email,
                holder_phone=holder_phone,
                actor_id=parsed_actor_id,
            )
            return f"Reserva {reservation.code} creada en estado pendiente con id {reservation.id}."
        except ApiError as exc:
            return f"No pude crear la reserva pendiente. Código: {exc.code}."
        except Exception as e:
            return f"Error en creación: {str(e)}"

    tools.extend([get_available_schedule, create_pending_reservation])
    return tools
