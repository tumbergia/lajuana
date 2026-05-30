import time

from app.ai.assistant.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.ai.providers.factory import get_llm_provider
from app.core.logging import logger
from app.core.time import format_colombia_today_es, now_colombia
from app.schemas.assistant_plan import AssistantPlan


class GeminiPlanner:
    async def plan(
        self,
        *,
        user_message: str,
        channel: str,
        conversation_context: str | None = None,
        conversation_id: str | None = None,
    ) -> AssistantPlan:
        logger.info(
            "[conversation_id=%s] LLM receives message | channel=%s",
            conversation_id,
            channel,
        )

        started = time.perf_counter()

        now = now_colombia()
        today_formatted = format_colombia_today_es()

        admin_tools_section = ""
        if channel == "admin_api":
            admin_tools_section = """
HERRAMIENTAS ADMINISTRATIVAS - CANAL ADMIN:
Eres un asistente administrativo de La Juana. Tienes acceso a todas las herramientas del sistema.
Puedes usar las siguientes herramientas administrativas cuando el usuario las solicite:

- admin_list_users: Lista todos los usuarios del sistema (email, nombre, rol, estado).
- admin_create_user: Crea un nuevo usuario. Requiere email, full_name, password, role.
- admin_update_user: Actualiza un usuario. Requiere user_id. Puede cambiar full_name, role, is_active.
- admin_deactivate_user: Desactiva un usuario. Requiere user_id.
- admin_list_experiences_admin: Lista experiencias con datos completos.
- admin_create_experience: Crea experiencia. Requiere name, slug, description, pricing tiers, etc.
- admin_update_experience: Actualiza experiencia. Requiere experience_id.
- admin_deactivate_experience: Desactiva experiencia. Requiere experience_id.
- admin_list_schedules_admin: Lista schedules con capacidad, slots, estado.
- admin_create_schedule: Crea schedule. Requiere experience_id, date, capacity_total.
- admin_update_schedule: Actualiza schedule. Requiere schedule_id.
- admin_deactivate_schedule: Desactiva schedule. Requiere schedule_id.
- admin_get_sales_summary: Reporte de ventas por rango de fechas.
- admin_get_reservation_funnel: Embudo de conversión de reservas.
- admin_get_channel_performance: Rendimiento por canal.
- admin_get_occupancy_report: Ocupación por fecha/experiencia.
- admin_get_equine_workload_report: Carga de trabajo equina.
- admin_get_logistics_checklist: Checklist operativo de una reserva.
- admin_close_service_execution: Cierra ejecución de servicio (reserva → COMPLETED).
- admin_add_equine_health_event: Registra evento de salud equina.
- admin_update_equine_availability: Cambia disponibilidad de un equino.
- admin_get_system_config: Muestra configuración del sistema (reglas de reserva, pagos).
- admin_update_reservation_rules: Actualiza reglas de reserva.
- admin_get_payment_instructions: Muestra instrucciones de pago configuradas.
- admin_list_human_review_requests: Lista solicitudes de revisión humana.
- schedule_birthday_automation: Activa/desactiva mensajes de cumpleaños.
- schedule_visit_anniversary_automation: Activa/desactiva mensajes de aniversario.

Reglas para canal admin:
- Si el usuario pide "listar usuarios", "ver usuarios", "quién trabaja aquí" → admin_list_users.
- Si pide "crear experiencia", "nueva experiencia" → admin_create_experience (pide datos faltantes).
- Si pide "reporte de ventas", "dashboard", "estadísticas" → usa la tool analítica correspondiente.
- Puedes usar herramientas de lectura (READ) sin restricciones.
- Herramientas de escritura (CREATE/UPDATE/DELETE) requieren confirmación implícita del usuario.
- NUNCA confirmes reservas ni verifiques pagos (siempre bloqueado por policy).
"""

        system_prompt = PLANNER_SYSTEM_PROMPT.format(
            today_formatted=today_formatted,
            today_year=str(now.year),
            admin_tools_section=admin_tools_section,
        )

        context = {
            "today": now.date().isoformat(),
            "today_description": today_formatted,
            "current_time": now.strftime("%H:%M"),
            "timezone": "America/Bogota",
            "channel": channel,
            "conversation_context": conversation_context or "",
            "user_message": user_message,
        }

        result = await get_llm_provider().generate_structured(
            system=system_prompt,
            user=str(context),
            response_model=AssistantPlan,
            temperature=0.1,
            telemetry_context={"channel": channel, "conversation_id": conversation_id},
        )

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "[conversation_id=%s] LLM response | elapsed_ms=%d",
            conversation_id,
            elapsed_ms,
        )

        return result
