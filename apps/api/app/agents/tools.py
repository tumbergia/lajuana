import datetime
from datetime import date
from typing import Literal

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool

from app.documents import ServiceLogEventType
from app.schemas.service_log import ServiceLogCreateSchema
from app.services import BookingService, OpsService, ReservationService, ParticipantService, EquineService, ScheduleService, SaddleService
from app.core.errors import ApiError

class StubVectorClient:
    async def search(self, query: str) -> str:
        return "Respuesta RAG sobre caballos y campo."

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
    @tool
    async def ejecutar_accion_administrativa(
        entidad: Literal["equinos", "reservas", "sillas", "bitacora", "agendas"],
        accion: Literal["crear", "consultar", "actualizar", "anular"],
        parametros_busqueda: dict,
        datos_cambio: dict,
    ) -> str:
        """
        Usa esta herramienta cuando un administrador o guía solicite registrar, modificar, consultar o anular cualquier dato del sistema (caballos, sillas, pagos, novedades, agendas). Traduce el lenguaje coloquial a la acción técnica correspondiente.
        - entidad: El tipo de registro a afectar ("equinos", "reservas", "sillas", "bitacora", "agendas").
        - accion: Lo que se desea hacer ("crear", "consultar", "actualizar", "anular").
        - parametros_busqueda: Diccionario para localizar el registro (Ej: {"nombre": "Rayo"}, {"codigo": "RES-123"}).
        - datos_cambio: Diccionario con la nueva información o parámetros extraídos del texto (Ej: {"is_available": false, "health_notes": "está cojo", "event_type": "INCIDENT", "notes": "Caballo se desbocó"}).
        """
        try:
            if entidad == "equinos":
                if accion == "consultar":
                    name = parametros_busqueda.get("nombre")
                    if not name:
                        equines = await equine_service.list()
                        if not equines: return "No hay caballos registrados."
                        info = ["Lista de caballos:"]
                        for e in equines:
                            estado = "disponible" if e.is_available else "NO disponible"
                            info.append(f"- {e.name} ({estado})")
                        return "\n".join(info)

                    equine = await equine_service.find_by_name(name)
                    if not equine: return f"No encontré al caballo {name}."
                    estado = "disponible" if equine.is_available else "NO disponible"
                    notas = equine.availability_notes if equine.availability_notes else "Sin notas adicionales."
                    return f"Caballo: {equine.name}. Estado: {estado}. Notas de salud/disponibilidad: {notas}."
                
                elif accion == "actualizar":
                    name = parametros_busqueda.get("nombre")
                    if not name: return "Falta el nombre del caballo para actualizar."
                    equine = await equine_service.find_by_name(name)
                    if not equine: return f"No encontré al caballo {name}."
                    
                    if "is_available" in datos_cambio:
                        equine.is_available = datos_cambio["is_available"]
                    if "health_notes" in datos_cambio:
                        equine.availability_notes = datos_cambio["health_notes"]
                    await equine.save()
                    return f"Entendido, he actualizado a {equine.name}. Ahora está {'disponible' if equine.is_available else 'inactivo'}. Notas: {equine.availability_notes}."

            elif entidad == "reservas":
                if accion == "consultar":
                    codigo = parametros_busqueda.get("codigo") or parametros_busqueda.get("id")
                    if not codigo: return "Falta el código o ID de la reserva para consultar."
                    reservation = await reservation_service.find_by_code_or_id(codigo)
                    if not reservation: return f"No encontré ninguna reserva con código {codigo}."
                    
                    participants_info = []
                    for p_id in reservation.participant_ids:
                        try:
                            p = await participant_service.get(str(p_id))
                            info = f"- {p.first_name} {p.last_name}"
                            notes = []
                            if getattr(p, "medical_conditions", None): notes.append(f"Condición médica: {p.medical_conditions}")
                            if getattr(p, "dietary_restrictions", None): notes.append(f"Restricción alimentaria: {p.dietary_restrictions}")
                            if getattr(p, "functional_conditions", None): notes.append(f"Condición funcional: {p.functional_conditions}")
                            if getattr(p, "diet", None): notes.append(f"Dieta: {p.diet}")
                            if notes:
                                info += f" (Notas: {', '.join(notes)})"
                            participants_info.append(info)
                        except Exception:
                            pass
                    
                    details = f"Reserva {reservation.code} (Estado: {reservation.status.value}).\nParticipantes:\n"
                    if participants_info:
                        details += "\n".join(participants_info)
                    else:
                        details += "Sin participantes registrados."
                    return details

                elif accion == "actualizar":
                    codigo = parametros_busqueda.get("codigo")
                    if not codigo: return "Falta el código de reserva."
                    reservation = await reservation_service.find_by_code_or_id(codigo)
                    if not reservation: return f"No encontré reserva {codigo}."
                    
                    from app.common.enums import ReservationStatus
                    if "status" in datos_cambio:
                        try:
                            target_status = ReservationStatus[datos_cambio["status"].upper()]
                            await reservation_service.set_status(str(reservation.id), target_status)
                            return f"Entendido, he actualizado el estado de la reserva {reservation.code} a {target_status.value}."
                        except Exception as e:
                            return f"No pude actualizar el estado: {str(e)}"
                    return "No sé qué actualizar en la reserva."

            elif entidad == "sillas":
                if accion == "actualizar":
                    codigo = parametros_busqueda.get("codigo")
                    if not codigo: return "Falta el código de la silla."
                    saddle = await saddle_service.find_by_code(codigo)
                    if not saddle: return f"No encontré la silla {codigo}."
                    
                    issue = datos_cambio.get("issue_description", datos_cambio.get("notes", "Daño reportado sin detalle."))
                    saddle.is_available = False
                    saddle.notes = f"{saddle.notes} | Daño: {issue}" if saddle.notes else f"Daño: {issue}"
                    await saddle.save()
                    return f"Entendido, la silla {saddle.code} fue marcada con daño y enviada a mantenimiento. Daño: {issue}."

            elif entidad == "bitacora":
                if accion == "crear":
                    reservation_id = datos_cambio.get("reservation_id")
                    if not reservation_id:
                        res_code = parametros_busqueda.get("reserva_codigo")
                        if res_code:
                            res = await reservation_service.find_by_code_or_id(res_code)
                            if res: reservation_id = str(res.id)
                    if not reservation_id: return "Falta la reserva relacionada para la bitácora."
                    
                    try:
                        from app.documents import ServiceLogEventType
                        event_type_str = datos_cambio.get("event_type", "OTHER")
                        happened_at_str = datos_cambio.get("happened_at")
                        happened_at = datetime.datetime.fromisoformat(happened_at_str) if happened_at_str else datetime.datetime.now()
                        
                        payload = ServiceLogCreateSchema(
                            reservation_id=reservation_id,
                            event_type=ServiceLogEventType[event_type_str.upper()],
                            happened_at=happened_at,
                            notes=datos_cambio.get("notes"),
                            checkpoint_name=datos_cambio.get("checkpoint_name"),
                            related_equine_id=datos_cambio.get("related_equine_id")
                        )
                        doc = await ops_service.create_log(payload)
                        return f"Entendido, he registrado la bitácora con éxito. ID: {doc.id}."
                    except Exception as e:
                        return f"Error al registrar bitácora: {str(e)}"

            elif entidad == "agendas":
                if accion == "consultar":
                    today = datetime.date.today()
                    schedules = await schedule_service.list(date_from=today, date_to=today)
                    if not schedules:
                        return "No hay agendas operativas para hoy."
                    info = [f"Agenda de hoy ({today.isoformat()}):"]
                    for s in schedules:
                        info.append(f"- ID: {s.id} | Reservados: {s.reserved_slots} | Disponibles: {s.available_slots} | Estado: {s.status.value}")
                    return "\n".join(info)

            return f"Acción '{accion}' en entidad '{entidad}' no soportada o mal estructurada."
        except Exception as e:
            return f"Error al ejecutar la acción: {str(e)}"

    return [ejecutar_accion_administrativa]

def create_tourist_tools(booking_service: BookingService, vector_client: StubVectorClient):
    @tool
    async def search_information(query: str) -> str:
        """Busca información de contexto o RAG para responder preguntas sobre La Juana, caballos o el campo."""
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