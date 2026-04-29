import datetime

from app.common.enums import ReservationStatus
from app.documents import ServiceLogEventType
from app.schemas.service_log import ServiceLogCreateSchema
from app.services import (
    EquineService,
    OpsService,
    ParticipantService,
    ReservationService,
    SaddleService,
    ScheduleService,
)


class EquineHandler:
    def __init__(self, equine_service: EquineService):
        self.equine_service = equine_service

    async def consultar(self, parametros_busqueda: dict, datos_cambio: dict) -> str:
        name = parametros_busqueda.get("nombre")
        if not name:
            equines = await self.equine_service.list()
            if not equines:
                return "No hay equinos registrados."
            info = ["Lista de equinos:"]
            for e in equines:
                estado = "disponible" if e.is_available else "NO disponible"
                info.append(f"- {e.name} ({estado})")
            return "\n".join(info)

        equine = await self.equine_service.find_by_name(name)
        if not equine:
            return f"No encontré al equino {name}."
        estado = "disponible" if equine.is_available else "NO disponible"
        notas = equine.availability_notes if equine.availability_notes else "Sin notas adicionales."
        return f"Equino: {equine.name}. Estado: {estado}. Notas de salud/disponibilidad: {notas}."

    async def actualizar(self, parametros_busqueda: dict, datos_cambio: dict) -> str:
        name = parametros_busqueda.get("nombre")
        if not name:
            equines = await self.equine_service.list()
            if not equines:
                return "No hay equinos registrados para actualizar."
            info = ["Falta el nombre. ¿A cuál de estos equinos te refieres?:"]
            for e in equines:
                info.append(f"- {e.name}")
            return "\n".join(info)
        equine = await self.equine_service.find_by_name(name)
        if not equine:
            return f"No encontré al equino {name}."

        if "is_available" in datos_cambio:
            equine.is_available = datos_cambio["is_available"]
        if "health_notes" in datos_cambio:
            equine.availability_notes = datos_cambio["health_notes"]
        await equine.save()
        return f"Entendido, he actualizado a {equine.name}. Ahora está {'disponible' if equine.is_available else 'inactivo'}. Notas: {equine.availability_notes}."


class ReservationHandler:
    def __init__(
        self, reservation_service: ReservationService, participant_service: ParticipantService
    ):
        self.reservation_service = reservation_service
        self.participant_service = participant_service

    async def consultar(self, parametros_busqueda: dict, datos_cambio: dict) -> str:
        codigo = parametros_busqueda.get("codigo") or parametros_busqueda.get("id")

        if not codigo:
            from app.common.enums import UserRole

            reservas = await self.reservation_service.list(actor_role=UserRole.ADMIN)
            if not reservas:
                return "No hay reservas registradas."
            info = ["Lista de reservas registradas:"]
            for r in reservas:
                info.append(
                    f"- Código: {r.code} | Estado: {r.status.value} | Participantes: {r.participant_count}"
                )
            return "\n".join(info)

        reservation = await self.reservation_service.find_by_code_or_id(codigo)
        if not reservation:
            return f"No encontré ninguna reserva con código {codigo}."

        participants_info = []
        for p_id in reservation.participant_ids:
            try:
                p = await self.participant_service.get(str(p_id))
                info = f"- {p.first_name} {p.last_name}"
                notes = []
                if getattr(p, "medical_conditions", None):
                    notes.append(f"Condición médica: {p.medical_conditions}")
                if getattr(p, "dietary_restrictions", None):
                    notes.append(f"Restricción alimentaria: {p.dietary_restrictions}")
                if getattr(p, "functional_conditions", None):
                    notes.append(f"Condición funcional: {p.functional_conditions}")
                if getattr(p, "diet", None):
                    notes.append(f"Dieta: {p.diet}")
                if notes:
                    info += f" (Notas: {', '.join(notes)})"
                participants_info.append(info)
            except Exception:
                pass

        details = (
            f"Reserva {reservation.code} (Estado: {reservation.status.value}).\nParticipantes:\n"
        )
        if participants_info:
            details += "\n".join(participants_info)
        else:
            details += "Sin participantes registrados."
        return details

    async def actualizar(self, parametros_busqueda: dict, datos_cambio: dict) -> str:
        codigo = parametros_busqueda.get("codigo")
        if not codigo:
            from app.common.enums import UserRole

            reservas = await self.reservation_service.list(actor_role=UserRole.ADMIN)
            if not reservas:
                return "No hay reservas registradas para actualizar."
            info = ["Falta el código. ¿A cuál de estas reservas te refieres?:"]
            for r in reservas:
                info.append(f"- {r.code} | {r.status.value}")
            return "\n".join(info)
        reservation = await self.reservation_service.find_by_code_or_id(codigo)
        if not reservation:
            return f"No encontré reserva {codigo}."

        if "status" in datos_cambio:
            try:
                target_status = ReservationStatus[datos_cambio["status"].upper()]
                await self.reservation_service.set_status(str(reservation.id), target_status)
                return f"Entendido, he actualizado el estado de la reserva {reservation.code} a {target_status.value}."
            except Exception as e:
                return f"No pude actualizar el estado: {str(e)}"
        return "No sé qué actualizar en la reserva."


class SaddleHandler:
    def __init__(self, saddle_service: SaddleService):
        self.saddle_service = saddle_service

    async def actualizar(self, parametros_busqueda: dict, datos_cambio: dict) -> str:
        codigo = parametros_busqueda.get("codigo")
        if not codigo:
            saddles = await self.saddle_service.list()
            if not saddles:
                return "No hay sillas registradas para actualizar."
            info = ["Falta el código de la silla. ¿A cuál de estas te refieres?:"]
            for s in saddles:
                name_str = f" ({s.name})" if getattr(s, "name", None) else ""
                info.append(f"- {s.code}{name_str}")
            return "\n".join(info)
        saddle = await self.saddle_service.find_by_code(codigo)
        if not saddle:
            return f"No encontré la silla {codigo}."

        issue = datos_cambio.get(
            "issue_description", datos_cambio.get("notes", "Daño reportado sin detalle.")
        )
        saddle.is_available = False
        saddle.notes = f"{saddle.notes} | Daño: {issue}" if saddle.notes else f"Daño: {issue}"
        await saddle.save()
        return f"Entendido, la silla {saddle.code} fue marcada con daño y enviada a mantenimiento. Daño: {issue}."


class ServiceLogHandler:
    def __init__(self, ops_service: OpsService, reservation_service: ReservationService):
        self.ops_service = ops_service
        self.reservation_service = reservation_service

    async def crear(self, parametros_busqueda: dict, datos_cambio: dict) -> str:
        reservation_id = datos_cambio.get("reservation_id")
        if not reservation_id:
            res_code = parametros_busqueda.get("reserva_codigo")
            if res_code:
                res = await self.reservation_service.find_by_code_or_id(res_code)
                if res:
                    reservation_id = str(res.id)
        if not reservation_id:
            from app.common.enums import UserRole

            reservas = await self.reservation_service.list(actor_role=UserRole.ADMIN)
            info = [
                "Falta la reserva relacionada para la bitácora. Selecciona una de estas reservas:"
            ]
            for r in reservas:
                info.append(f"- {r.code} | {r.status.value}")
            return "\n".join(info)

        try:
            event_type_str = datos_cambio.get("event_type", "OTHER")
            happened_at_str = datos_cambio.get("happened_at")
            happened_at = (
                datetime.datetime.fromisoformat(happened_at_str)
                if happened_at_str
                else datetime.datetime.now()
            )

            payload = ServiceLogCreateSchema(
                reservation_id=reservation_id,
                event_type=ServiceLogEventType[event_type_str.upper()],
                happened_at=happened_at,
                notes=datos_cambio.get("notes"),
                checkpoint_name=datos_cambio.get("checkpoint_name"),
                related_equine_id=datos_cambio.get("related_equine_id"),
            )
            doc = await self.ops_service.create_log(payload)
            return f"Entendido, he registrado la bitácora con éxito. ID: {doc.id}."
        except Exception as e:
            return f"Error al registrar bitácora: {str(e)}"


class ScheduleHandler:
    def __init__(self, schedule_service: ScheduleService):
        self.schedule_service = schedule_service

    async def consultar(self, parametros_busqueda: dict, datos_cambio: dict) -> str:
        today = datetime.date.today()
        schedules = await self.schedule_service.list(date_from=today, date_to=today)
        if not schedules:
            return "No hay agendas operativas para hoy."
        info = [f"Agenda de hoy ({today.isoformat()}):"]
        for s in schedules:
            info.append(
                f"- ID: {s.id} | Reservados: {s.reserved_slots} | Disponibles: {s.available_slots} | Estado: {s.status.value}"
            )
        return "\n".join(info)
