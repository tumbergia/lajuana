from __future__ import annotations

from typing import Any

from app.ai.mcp.tools.admin_assignments import (
    admin_create_assignment,
    admin_delete_assignment,
    admin_finalize_all_assignments,
    admin_finalize_assignment,
    admin_get_assignment_board,
    admin_update_assignment,
)
from app.ai.mcp.tools.admin_equine_events import (
    admin_create_equine_event,
    admin_list_equine_events,
    admin_update_equine_event,
)
from app.ai.mcp.tools.admin_providers import (
    admin_create_provider,
    admin_deactivate_provider,
    admin_get_provider,
    admin_list_providers,
    admin_update_provider,
)
from app.ai.mcp.tools.admin_saddles import (
    admin_create_saddle,
    admin_deactivate_saddle,
    admin_get_saddle,
    admin_list_available_saddles_for_reservation,
    admin_list_saddles,
    admin_update_saddle,
)
from app.ai.mcp.tools.admin_config import (
    admin_get_emergency_contacts,
    admin_get_payment_instructions,
    admin_get_system_config,
    admin_update_reservation_rules,
)
from app.ai.mcp.tools.admin_equines import (
    admin_create_equine,
    admin_deactivate_equine,
    admin_get_equine,
    admin_list_equines,
    admin_update_equine,
)
from app.ai.mcp.tools.admin_experiences import (
    admin_create_experience,
    admin_deactivate_experience,
    admin_list_experiences_admin,
    admin_update_experience,
)
from app.ai.mcp.tools.admin_participants import (
    admin_get_participant,
    admin_update_participant,
)
from app.ai.mcp.tools.admin_payment_proofs import (
    admin_approve_payment,
    admin_get_payment_proof,
    admin_reject_payment_proof,
    admin_unreject_payment_proof,
    admin_unverify_payment_proof,
)
from app.ai.mcp.tools.admin_reservations import (
    admin_cancel_reservation,
    admin_confirm_reservation,
    admin_get_reservation_detail,
    admin_list_reservations,
)
from app.ai.mcp.tools.admin_reviews import admin_list_human_review_requests
from app.ai.mcp.tools.admin_users import (
    admin_create_user,
    admin_deactivate_user,
    admin_list_users,
    admin_update_user,
)
from app.ai.mcp.tools.analytics import (
    admin_get_channel_performance,
    admin_get_equine_workload_report,
    admin_get_occupancy_report,
    admin_get_reservation_funnel,
    admin_get_sales_summary,
)
from app.ai.mcp.tools.automations import (
    schedule_birthday_automation,
    schedule_visit_anniversary_automation,
    send_post_service_message,
)
from app.ai.mcp.tools.availability import check_experience_availability
from app.ai.mcp.tools.catalog import list_experiences
from app.ai.mcp.tools.client_reservations import (
    cancel_reservation,
    update_reservation_date,
    update_reservation_participants,
)
from app.ai.mcp.tools.operations import (
    admin_add_equine_health_event,
    admin_close_service_execution,
    admin_get_equine_workload,
    admin_get_logistics_checklist,
    admin_update_equine_availability,
    guide_create_service_log,
    guide_report_incident,
)
from app.ai.mcp.tools.participant_forms import (
    generate_participant_form_link,
    get_participant_form_status,
)
from app.ai.mcp.tools.payment_instructions import get_payment_instructions
from app.ai.mcp.tools.quote import quote_experience
from app.ai.mcp.tools.reservation_draft import (
    attach_payment_proof_to_reservation,
    create_reservation_draft,
    get_reservation_public_summary,
    get_reservation_status_by_phone,
)
from app.ai.mcp.tools.schedules import list_available_schedules, suggest_alternative_dates


# ── Real implementations for previously stubbed tools ────────
async def get_experience_detail(**kwargs: Any) -> dict[str, Any]:
    import re
    import time
    import unicodedata

    from app.ai.mcp.tool_contracts import ExperienceDetailOutput, ToolBlockingReason
    from app.documents import ExperienceDocument

    trace_id = kwargs.get("trace_id", "")
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()

    experience_id = kwargs.get("experience_id")
    experience_query = kwargs.get("experience_query")

    def _normalize(s: str) -> str:
        nfkd = unicodedata.normalize("NFKD", s)
        return nfkd.encode("ascii", "ignore").decode("ascii").lower().strip()

    _STOPWORDS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "en", "para", "por", "a", "y", "e", "o", "que", "con", "su", "al"}

    def _match_query(exp_name: str, query: str) -> bool:
        exp_normalized = _normalize(exp_name)
        query_normalized = _normalize(query)
        if query_normalized in exp_normalized:
            return True
        query_words = [w for w in query_normalized.split() if w not in _STOPWORDS]
        exp_words = exp_normalized.split()
        if not query_words:
            return False
        for qw in query_words:
            if not any(qw in ew for ew in exp_words):
                return False
        return True

    experience = None
    if experience_id:
        experience = await ExperienceDocument.get(experience_id)

    if experience is None and experience_query:
        all_experiences = await ExperienceDocument.find_all().to_list()
        for exp in all_experiences:
            if _match_query(exp.name, experience_query):
                experience = exp
                break
        if experience is None:
            for exp in all_experiences:
                if exp.aliases and any(_match_query(a, experience_query) for a in exp.aliases):
                    experience = exp
                    break
        if experience is None:
            for exp in all_experiences:
                if exp.tags and any(_match_query(t, experience_query) for t in exp.tags):
                    experience = exp
                    break

    if experience is None:
        output = ExperienceDetailOutput(
            found=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(
                    code="experience.not_found",
                    message="No encontré la experiencia solicitada.",
                )
            ],
        )
        return output.model_dump(mode="json")

    pricing = getattr(experience, "pricing", None)
    min_price = None
    if pricing and pricing.tiers:
        min_price = min(
            (t.price_per_person for t in pricing.tiers if hasattr(t, "price_per_person")),
            default=None,
        )

    duration = getattr(experience, "duration", None)
    duration_text = (
        getattr(duration, "display_text", None)
        or str(getattr(experience, "duration_hours", ""))
        or str(getattr(experience, "duration_days", ""))
    )

    inclusions_data = getattr(experience, "inclusions", None)
    inclusions = getattr(inclusions_data, "items", []) if inclusions_data else []

    output = ExperienceDetailOutput(
        found=True,
        trace_id=trace_id,
        experience_id=str(experience.id),
        name=experience.name,
        slug=experience.slug,
        description=experience.description,
        short_description=experience.subtitle or (experience.description or "")[:120],
        duration=duration_text or None,
        difficulty=str(getattr(experience, "difficulty", "")) or None,
        level=str(getattr(experience, "level", "")) or None,
        includes=inclusions,
        restrictions=[],
        starting_price=min_price,
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    from app.documents.tool_call_log_document import ToolCallLogDocument

    await ToolCallLogDocument(
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
        tool_name="get_experience_detail",
        input={"experience_id": experience_id, "experience_query": experience_query},
        output=output.model_dump(mode="json"),
        status="success",
        latency_ms=latency_ms,
    ).insert()

    return output.model_dump(mode="json")


async def get_public_business_rules(**kwargs: Any) -> dict[str, Any]:
    import time

    from app.ai.mcp.tool_contracts import PublicBusinessRulesOutput
    from app.core.di import Container
    from app.documents.tool_call_log_document import ToolCallLogDocument

    trace_id = kwargs.get("trace_id", "")
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    config_service = Container.get_instance().config_service
    reservation_rules = await config_service.get_reservation_rules()
    location = await config_service.get_business_location()

    output = PublicBusinessRulesOutput(
        trace_id=trace_id,
        family_focus=(
            "La Juana es una experiencia familiar y tranquila enfocada en la naturaleza "
            "y la cultura rural. No manejamos actividades orientadas al consumo de alcohol, "
            "fiesta o alboroto durante los recorridos."
        ),
        alcohol_policy=(
            "Prohibido el consumo de alcohol antes y durante el recorrido. "
            "Nos reservamos el derecho de admisión si detectamos estado de ebriedad."
        ),
        behavior_policy=(
            "Respeto por los animales, los guías y el entorno natural. "
            "Instrucciones de seguridad obligatorias. "
            "Comportamiento agresivo o irresponsable causa cancelación inmediata sin reembolso."
        ),
        reservation_notice_days=reservation_rules.min_days_in_advance,
        reservation_draft_ttl_minutes=reservation_rules.reservation_draft_ttl_minutes,
        require_payment_proof_for_confirmation=(
            reservation_rules.require_payment_proof_for_confirmation
        ),
        min_age=reservation_rules.min_age,
        max_age=reservation_rules.max_age,
        location_name=location.name,
        location_address=location.address,
        location_municipality=location.municipality,
        location_directions=location.directions,
        google_maps_url=location.google_maps_url,
        general_restrictions=[
            f"Edad permitida: {reservation_rules.min_age} a {reservation_rules.max_age} años.",
            "Máximo 8 participantes por reserva.",
            (
                f"Reserva con mínimo {reservation_rules.min_days_in_advance} días de anticipación."
                if reservation_rules.min_days_in_advance > 0
                else "Se permiten reservas para el mismo día, sujetas a disponibilidad."
            ),
            "No apto para personas con problemas de movilidad severos.",
        ],
        disclaimer=(
            "La Juana no se hace responsable por objetos personales perdidos o dañados. "
            "La experiencia incluye seguro de responsabilidad civil. "
            "En caso de lluvia intensa se puede reprogramar la salida."
        ),
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    await ToolCallLogDocument(
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
        tool_name="get_public_business_rules",
        input={},
        output=output.model_dump(mode="json"),
        status="success",
        latency_ms=latency_ms,
    ).insert()

    return output.model_dump(mode="json")


async def request_human_review(**kwargs: Any) -> dict[str, Any]:
    import time

    from app.ai.mcp.tool_contracts import RequestHumanReviewOutput, ToolBlockingReason
    from app.documents.human_review_request_document import HumanReviewRequestDocument
    from app.documents.tool_call_log_document import ToolCallLogDocument

    trace_id = kwargs.get("trace_id", "")
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()

    conversation_id = kwargs.get("conversation_id", "")
    reason_code = kwargs.get("reason_code", "other")
    summary = kwargs.get("summary", "Solicitud de revisión humana desde chat.")
    priority = kwargs.get("priority", "normal")

    try:
        doc = HumanReviewRequestDocument(
            conversation_id=conversation_id,
            reason_code=reason_code,
            summary=summary,
            priority=priority,
            status="open",
        )
        await doc.insert()

        try:
            from app.common.enums import NotificationEventType
            from app.core.di import Container

            phone_hint = conversation_id.split(":")[-1] if conversation_id else ""
            await Container.get_instance().notification_service.enqueue_admin_in_app(
                event_type=NotificationEventType.HUMAN_REVIEW_REQUESTED,
                title="Cliente solicita atención humana",
                body=f"{phone_hint or conversation_id}: {summary}",
                dedup_suffix=doc.review_id,
                contact_phone=phone_hint or None,
            )
        except Exception:
            from app.core.logging import logger

            logger.exception(
                "[human_review=%s] Failed to enqueue admin notification",
                doc.review_id,
            )

        output = RequestHumanReviewOutput(
            trace_id=trace_id,
            requested=True,
            review_id=doc.review_id,
            status="open",
            message="Solicitud de revisión humana creada. Un asesor revisará tu caso pronto.",
        )

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="request_human_review",
            input={
                "conversation_id": conversation_id,
                "reason_code": reason_code,
                "summary": summary,
                "priority": priority,
            },
            output=output.model_dump(mode="json"),
            status="success",
            latency_ms=latency_ms,
        ).insert()

        return output.model_dump(mode="json")

    except Exception as exc:
        output = RequestHumanReviewOutput(
            trace_id=trace_id,
            requested=False,
            review_id="",
            status="open",
            message="No se pudo crear la solicitud de revisión humana.",
            blocking_reasons=[
                ToolBlockingReason(
                    code="review.creation_failed",
                    message=str(exc),
                )
            ],
        )

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="request_human_review",
            input={
                "conversation_id": conversation_id,
                "reason_code": reason_code,
                "summary": summary,
                "priority": priority,
            },
            output=output.model_dump(mode="json"),
            status="error",
            error_code="review.creation_failed",
            latency_ms=latency_ms,
        ).insert()

        return output.model_dump(mode="json")


__all__ = [
    "admin_add_equine_health_event",
    "admin_close_service_execution",
    "admin_get_channel_performance",
    "admin_get_equine_workload",
    "admin_get_equine_workload_report",
    "admin_get_logistics_checklist",
    "admin_get_occupancy_report",
    "admin_get_reservation_funnel",
    "admin_get_sales_summary",
    "admin_update_equine_availability",
    "admin_create_experience",
    "admin_update_experience",
    "admin_list_experiences_admin",
    "admin_deactivate_experience",
    "admin_list_users",
    "admin_create_user",
    "admin_update_user",
    "admin_deactivate_user",
    "admin_get_system_config",
    "admin_update_reservation_rules",
    "admin_get_payment_instructions",
    "admin_list_human_review_requests",
    "admin_list_equines",
    "admin_get_equine",
    "admin_create_equine",
    "admin_update_equine",
    "admin_deactivate_equine",
    "admin_get_participant",
    "admin_update_participant",
    "admin_get_payment_proof",
    "admin_approve_payment",
    "admin_reject_payment_proof",
    "admin_unverify_payment_proof",
    "admin_unreject_payment_proof",
    "admin_list_providers",
    "admin_get_provider",
    "admin_create_provider",
    "admin_update_provider",
    "admin_deactivate_provider",
    "admin_list_saddles",
    "admin_get_saddle",
    "admin_create_saddle",
    "admin_update_saddle",
    "admin_deactivate_saddle",
    "admin_list_available_saddles_for_reservation",
    "admin_get_assignment_board",
    "admin_create_assignment",
    "admin_update_assignment",
    "admin_delete_assignment",
    "admin_finalize_assignment",
    "admin_finalize_all_assignments",
    "admin_list_equine_events",
    "admin_create_equine_event",
    "admin_update_equine_event",
    "admin_get_emergency_contacts",
    "admin_list_reservations",
    "admin_get_reservation_detail",
    "admin_confirm_reservation",
    "admin_cancel_reservation",
    "check_experience_availability",
    "get_experience_detail",
    "get_public_business_rules",
    "guide_create_service_log",
    "guide_report_incident",
    "list_available_schedules",
    "list_experiences",
    "quote_experience",
    "schedule_birthday_automation",
    "schedule_visit_anniversary_automation",
    "send_post_service_message",
    "suggest_alternative_dates",
    "create_reservation_draft",
    "attach_payment_proof_to_reservation",
    "get_reservation_public_summary",
    "get_reservation_status_by_phone",
    "cancel_reservation",
    "update_reservation_date",
    "update_reservation_participants",
    "request_human_review",
    "generate_participant_form_link",
    "get_participant_form_status",
    "get_payment_instructions",
]
