import datetime
from datetime import date
from typing import Literal

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool

from app.documents import ServiceLogEventType
from app.schemas.service_log import ServiceLogCreateSchema
from app.services import BookingService, OpsService, ReservationService, ParticipantService, EquineService, ScheduleService, SaddleService
from app.core.errors import ApiError
from app.agents.handlers import (
    EquineHandler,
    ReservationHandler,
    SaddleHandler,
    ServiceLogHandler,
    ScheduleHandler,
)

class StubVectorClient:
    async def search(self, query: str) -> str:
        return "Respuesta RAG sobre equinos y campo."

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
        Usa esta herramienta cuando un administrador o guía solicite registrar, modificar, consultar o anular cualquier dato del sistema (equinos, sillas, pagos, novedades, agendas). Traduce el lenguaje coloquial a la acción técnica correspondiente.
        - entidad: El tipo de registro a afectar ("equinos", "reservas", "sillas", "bitacora", "agendas").
        - accion: Lo que se desea hacer ("crear", "consultar", "actualizar", "anular").
        - parametros_busqueda: Diccionario para localizar el registro (Ej: {"nombre": "Rayo"}, {"codigo": "RES-123"}).
        - datos_cambio: Diccionario con la nueva información o parámetros extraídos del texto (Ej: {"is_available": false, "health_notes": "está cojo", "event_type": "INCIDENT", "notes": "Equino se desbocó"}).
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

    return [ejecutar_accion_administrativa]

def create_tourist_tools(booking_service: BookingService, vector_client: StubVectorClient):
    @tool
    async def search_information(query: str) -> str:
        """Busca información de contexto o RAG para responder preguntas sobre La Juana, equinos o el campo."""
        return await vector_client.search(query)

    @tool
    async def get_available_schedule(experience_id: str, participant_count: int, requested_date: str) -> dict:
        """Consulta la disponibilidad de agenda para una experiencia."""
        parsed_date = date.fromisoformat(requested_date) if requested_date else None
        schedule = await booking_service.get_available_schedule(
            experience_id=experience_id,
            requested_date=parsed_date,
            participant_count=participant_count,
        )
        if not schedule:
            return {"success": False, "message": "No encontré cupo disponible."}
        return {"success": True, "schedule_id": str(schedule.id), "message": "Agenda disponible encontrada."}

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
    
    return [search_information, get_available_schedule, create_pending_reservation]