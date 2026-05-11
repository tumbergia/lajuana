from datetime import UTC, date, datetime
from difflib import SequenceMatcher
import json
import re

from fastapi import APIRouter
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agents import BeanieConversationCheckpointer, get_chat_graph
from app.core.config import settings
from app.services import BookingService, ExperienceService
from app.schemas.chat import ChatResponseSchema, WhatsAppChatRequestSchema

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
checkpointer = BeanieConversationCheckpointer()
graph = get_chat_graph()
experience_service = ExperienceService()
booking_service = BookingService()
reply_model = ChatOpenAI(
    base_url=settings.chat_llm_base_url,
    api_key=settings.chat_llm_api_key or "lm-studio",
    model=settings.chat_llm_model_name,
    temperature=0,
)


def _looks_like_booking_intent(text: str) -> bool:
    normalized = text.lower()
    return bool(
        re.search(
            r"\b(reserv|reserva|cabalgata|experienc|cupo|fecha|personas?|pax|hora|horario)\b",
            normalized,
        )
    )


def _parse_requested_date(text: str) -> date | None:
    iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if iso_match:
        try:
            return date.fromisoformat(iso_match.group(1))
        except ValueError:
            return None

    latin_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", text)
    if latin_match:
        day, month, year = latin_match.groups()
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None

    return None


def _parse_participant_count(text: str) -> int | None:
    match = re.search(r"\b(\d{1,2})\s*(personas?|pax|participantes?)\b", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _experience_label(experience: object) -> str:
    return str(getattr(experience, "name", "experiencia"))


def _best_experience_match(text: str, experiences: list[object]) -> object | None:
    normalized_text = text.lower()
    best_score = 0.0
    best_experience = None

    for experience in experiences:
        name = str(getattr(experience, "name", ""))
        slug = str(getattr(experience, "slug", ""))
        subtitle = str(getattr(experience, "subtitle", "") or "")
        haystack = " ".join(part for part in (name, slug, subtitle) if part).lower()
        if not haystack:
            continue

        score = SequenceMatcher(None, normalized_text, haystack).ratio()
        if haystack in normalized_text or normalized_text in haystack:
            score = max(score, 0.9)
        if score > best_score:
            best_score = score
            best_experience = experience

    if best_score >= 0.45:
        return best_experience
    return None


async def _resolve_contextual_experience(
    restored: dict[str, object] | None,
    experiences: list[object],
) -> object | None:
    extracted_data = (restored or {}).get("extracted_data", {})
    if not isinstance(extracted_data, dict):
        return None

    experience_id = extracted_data.get("experience_id")
    if experience_id:
        try:
            return await experience_service.get(str(experience_id))
        except Exception:
            pass

    experience_name = extracted_data.get("experience_name")
    if experience_name:
        name_text = str(experience_name)
        for experience in experiences:
            if str(getattr(experience, "name", "")).lower() == name_text.lower():
                return experience
        return _best_experience_match(name_text, experiences)

    return None


def _format_schedule(schedule: object) -> str:
    schedule_date = getattr(schedule, "date", None)
    schedule_time = getattr(schedule, "start_time", None)
    if schedule_date is None:
        return "una fecha disponible"
    text = schedule_date.strftime("%d/%m/%Y")
    if schedule_time is not None:
        text = f"{text} a las {schedule_time.strftime('%H:%M')}"
    return text


async def _compose_booking_reply(context: dict[str, object]) -> str:
    prompt = HumanMessage(
        content=(
            "Redacta un solo mensaje de WhatsApp en español, natural y breve, sin saludos forzados, "
            "sin listas, sin markdown y sin mencionar procesos internos. Usa solo este contexto JSON:\n"
            f"{json.dumps(context, ensure_ascii=False)}"
        )
    )
    response = await reply_model.ainvoke(
        [
            SystemMessage(
                content=(
                    "Eres un asistente de reservas de La Juana. "
                    "Responde con un solo mensaje útil, directo y humano. "
                    "No inventes disponibilidad. "
                    "Si hay una fecha libre, proponla y pide los datos para continuar. "
                    "Si no hay una coincidencia exacta, ofrece otra fecha libre o pide que te indiquen otra experiencia o fecha, sin decir que no hay disponibilidad."
                )
            ),
            prompt,
        ]
    )
    return _clean_model_reply(str(response.content))


def _restored_extracted_data(restored: dict[str, object] | None) -> dict[str, object]:
    extracted_data = (restored or {}).get("extracted_data", {})
    if isinstance(extracted_data, dict):
        return extracted_data
    return {}


def _optional_email(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or "@" not in text:
        return None
    return text


async def _first_free_schedule_for_experience(
    experience_id: str,
    requested_date: date | None = None,
) -> object | None:
    schedules = await booking_service.schedule_service.list(
        experience_id=experience_id,
        date_from=requested_date,
        date_to=requested_date,
        is_active=True,
    )
    schedules.sort(
        key=lambda schedule: (
            getattr(schedule, "date", date.max),
            getattr(schedule, "start_time", None) or datetime.max.time(),
        )
    )
    for schedule in schedules:
        if not await booking_service.reservation_service.has_active_reservation_for_schedule(
            str(getattr(schedule, "id"))
        ):
            return schedule
    return None


async def _first_any_free_schedule_for_experience(experience_id: str) -> object | None:
    return await _first_free_schedule_for_experience(experience_id, requested_date=None)


async def _first_free_schedule_among_experiences(
    experiences: list[object],
    requested_date: date | None = None,
) -> tuple[object, object] | None:
    for experience in experiences:
        schedule = await _first_free_schedule_for_experience(
            str(getattr(experience, "id")),
            requested_date=requested_date,
        )
        if schedule is not None:
            return experience, schedule
    return None


async def _fast_booking_reply(
    message_text: str,
    restored: dict[str, object] | None = None,
) -> tuple[str, dict[str, object]]:
    experiences = await experience_service.list(is_active=True)
    extracted_data = _restored_extracted_data(restored)
    matched_experience = await _resolve_contextual_experience(restored, experiences)
    if matched_experience is None:
        matched_experience = _best_experience_match(message_text, experiences)
    participant_count = _parse_participant_count(message_text) or 1
    requested_date = _parse_requested_date(message_text)
    holder_name = extracted_data.get("holder_name")
    holder_email = _optional_email(extracted_data.get("holder_email"))
    holder_phone = extracted_data.get("holder_phone")

    if matched_experience is None:
        if not experiences:
            return (
                await _compose_booking_reply({"kind": "no_experiences"}),
                {"booking_intent": True},
            )

        free_slot = await _first_free_schedule_among_experiences(experiences, requested_date=requested_date)
        if free_slot is not None:
            experience, schedule = free_slot
            reservation = await booking_service.create_pending_reservation(
                experience_id=str(getattr(experience, "id")),
                schedule_id=str(getattr(schedule, "id")),
                participant_count=participant_count,
                requested_date=requested_date,
                holder_name=str(holder_name) if holder_name else None,
                holder_email=holder_email,
                holder_phone=str(holder_phone) if holder_phone else None,
            )
            reply_text = await _compose_booking_reply(
                {
                    "kind": "reservation_created",
                    "experience_name": _experience_label(experience),
                    "schedule_date": _format_schedule(schedule),
                    "participant_count": participant_count,
                    "reservation_code": reservation.code,
                }
            )
            return (
                reply_text,
                {
                    "booking_intent": True,
                    "extracted_data": {
                        "experience_id": str(getattr(experience, "id")),
                        "experience_name": _experience_label(experience),
                        "participant_count": participant_count,
                        "schedule_id": str(getattr(schedule, "id")),
                        "reservation_id": str(reservation.id),
                        "reservation_code": reservation.code,
                    },
                },
            )

        reply_text = await _compose_booking_reply(
            {
                "kind": "need_experience",
                "options": [_experience_label(experience) for experience in experiences[:4]],
            }
        )
        return reply_text, {"booking_intent": True}

    if requested_date is not None:
        schedule = await _first_free_schedule_for_experience(
            str(getattr(matched_experience, "id")),
            requested_date=requested_date,
        )
        schedule_source = "requested_date"
        if schedule is None:
            schedule = await _first_any_free_schedule_for_experience(str(getattr(matched_experience, "id")))
            schedule_source = "alternate_date"
        if schedule is not None:
            reservation = await booking_service.create_pending_reservation(
                experience_id=str(getattr(matched_experience, "id")),
                schedule_id=str(getattr(schedule, "id")),
                participant_count=participant_count,
                requested_date=requested_date,
                holder_name=str(holder_name) if holder_name else None,
                holder_email=holder_email,
                holder_phone=str(holder_phone) if holder_phone else None,
            )
            reply_text = await _compose_booking_reply(
                {
                    "kind": "reservation_created",
                    "experience_name": _experience_label(matched_experience),
                    "schedule_date": _format_schedule(schedule),
                    "participant_count": participant_count,
                    "requested_date": requested_date.isoformat(),
                    "schedule_source": schedule_source,
                    "reservation_code": reservation.code,
                }
            )
            return (
                reply_text,
                {
                    "booking_intent": True,
                    "extracted_data": {
                        "experience_id": str(getattr(matched_experience, "id")),
                        "experience_name": _experience_label(matched_experience),
                        "requested_date": requested_date.isoformat(),
                        "participant_count": participant_count,
                        "schedule_id": str(getattr(schedule, "id")),
                        "schedule_source": schedule_source,
                        "reservation_id": str(reservation.id),
                        "reservation_code": reservation.code,
                    },
                },
            )

    schedule = await _first_free_schedule_for_experience(
        str(getattr(matched_experience, "id")),
    )
    if schedule is not None:
        reservation = await booking_service.create_pending_reservation(
            experience_id=str(getattr(matched_experience, "id")),
            schedule_id=str(getattr(schedule, "id")),
            participant_count=participant_count,
            requested_date=requested_date,
            holder_name=str(holder_name) if holder_name else None,
            holder_email=holder_email,
            holder_phone=str(holder_phone) if holder_phone else None,
        )
        reply_text = await _compose_booking_reply(
            {
                "kind": "reservation_created",
                "experience_name": _experience_label(matched_experience),
                "schedule_date": _format_schedule(schedule),
                "participant_count": participant_count,
                "reservation_code": reservation.code,
            }
        )
        return (
            reply_text,
            {
                "booking_intent": True,
                "extracted_data": {
                    "experience_id": str(getattr(matched_experience, "id")),
                    "experience_name": _experience_label(matched_experience),
                    "participant_count": participant_count,
                    "schedule_id": str(getattr(schedule, "id")),
                    "reservation_id": str(reservation.id),
                    "reservation_code": reservation.code,
                },
            },
        )

    reply_text = await _compose_booking_reply(
        {
            "kind": "need_more_details",
            "experience_name": _experience_label(matched_experience),
            "participant_count": participant_count,
        }
    )
    return (
        reply_text,
        {
            "booking_intent": True,
            "extracted_data": {
                "experience_id": str(getattr(matched_experience, "id")),
                "experience_name": _experience_label(matched_experience),
                "participant_count": participant_count,
            },
        },
    )


def _latest_ai_reply(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if message.type == "ai":
            return _clean_model_reply(str(message.content))
    return ""


def _clean_model_reply(text: str) -> str:
    clean = text.strip()
    if not clean:
        return ""

    if "</thought>" in clean.lower():
        clean = re.split(r"</thought>", clean, flags=re.IGNORECASE)[-1].strip()
    elif "<thought>" in clean.lower():
        clean = re.split(r"<thought>", clean, flags=re.IGNORECASE)[-1].strip()

    lowered = clean.lower()
    for marker in (
        "final json construction:",
        "final answer:",
        "answer:",
        "response:",
        "thinking:",
        "reasoning:",
        "analysis:",
    ):
        index = lowered.rfind(marker)
        if index != -1:
            clean = clean[index + len(marker):].strip(" *:\n\t")
            lowered = clean.lower()

    if len(clean) >= 40:
        midpoint = len(clean) // 2
        if clean[:midpoint] == clean[midpoint:]:
            clean = clean[:midpoint].strip()

    if "}{" in clean:
        parts = clean.split("}{", maxsplit=1)
        if len(parts) == 2 and parts[0].strip() == parts[1].strip():
            clean = parts[0].strip()

    clean = "\n".join(segment.strip() for segment in clean.splitlines() if segment.strip())
    return clean.strip()


@router.post(
    "/chat",
    response_model=ChatResponseSchema,
    summary="Responder WhatsApp con el orquestador",
    description=(
        "Procesa un mensaje entrante de WhatsApp usando el grafo conversacional de La Juana. "
        "La conversación se persiste por wa_user_id o conversation_id para mantener continuidad."
    ),
    operation_id="whatsappChatWithAgent",
)
async def post_whatsapp_message(payload: WhatsAppChatRequestSchema) -> ChatResponseSchema:
    conversation_id = payload.conversation_id or payload.wa_user_id
    user_id = payload.wa_user_id

    try:
        restored = await checkpointer.load(conversation_id=conversation_id, user_id=user_id)
        messages = list((restored or {}).get("messages", []))
        messages.append(HumanMessage(content=payload.message))

        initial_state = {
            "messages": messages,
            "role": "unassigned",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "source": "whatsapp",
            "whatsapp_phone": payload.wa_user_id,
            "user_message": payload.message,
            "intent": (restored or {}).get("intent"),
            "experience_id": (restored or {}).get("experience_id"),
            "experience_name": (restored or {}).get("experience_name"),
            "experience_options": (restored or {}).get("experience_options", []),
            "requested_date": (restored or {}).get("requested_date"),
            "people_count": (restored or {}).get("people_count"),
            "customer_name": (restored or {}).get("customer_name"),
            "customer_phone": (restored or {}).get("customer_phone") or payload.wa_user_id,
            "notes": (restored or {}).get("notes"),
            "next_question": (restored or {}).get("next_question"),
            "missing_fields": (restored or {}).get("missing_fields", []),
            "availability": (restored or {}).get("availability"),
            "suggested_dates": (restored or {}).get("suggested_dates", []),
            "reservation_id": (restored or {}).get("reservation_id"),
            "reservation_status": (restored or {}).get("reservation_status"),
            "reservation_summary": (restored or {}).get("reservation_summary"),
            "sync_knowledge_required": bool((restored or {}).get("sync_knowledge_required", False)),
            "reservation_knowledge_synced": bool((restored or {}).get("reservation_knowledge_synced", False)),
            "knowledge_context": (restored or {}).get("knowledge_context", []),
            "extracted_data": (restored or {}).get("extracted_data", {}),
            "rag_context": (restored or {}).get("rag_context", ""),
            "booking_intent": bool((restored or {}).get("booking_intent", False))
            or _looks_like_booking_intent(payload.message),
            "errors": (restored or {}).get("errors", []),
        }

        result = await graph.ainvoke(initial_state)
        reply = _latest_ai_reply(result.get("messages", []))

        # Si no hay respuesta, usar fallback
        if not reply:
            reply = "Disculpa, estoy teniendo problemas técnicos. ¿Puedes intentar de nuevo? 🙏"

        await checkpointer.save(
            conversation_id=conversation_id,
            user_id=user_id,
            role="unassigned",
            state=result,
        )

        return ChatResponseSchema(
            conversation_id=conversation_id,
            role="unassigned",
            reply=reply,
            booking_intent=bool(result.get("booking_intent", False)),
            rag_context=result.get("rag_context"),
            processed_at=datetime.now(UTC),
        )
    
    except Exception as exc:
        # Log del error para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing WhatsApp message from {user_id}: {exc}", exc_info=True)
        
        # Respuesta de fallback humana
        fallback_reply = "Disculpa, estoy teniendo problemas técnicos en este momento. ¿Puedes intentar de nuevo en unos minutos? 🙏"
        
        # Intentar guardar el estado con el error
        try:
            error_state = {
                "messages": messages if 'messages' in locals() else [HumanMessage(content=payload.message)],
                "role": "unassigned",
                "user_id": user_id,
                "conversation_id": conversation_id,
                "errors": ["system_error"],
            }
            await checkpointer.save(
                conversation_id=conversation_id,
                user_id=user_id,
                role="unassigned",
                state=error_state,
            )
        except:
            pass  # Si falla guardar, no importa
        
        return ChatResponseSchema(
            conversation_id=conversation_id,
            role="unassigned",
            reply=fallback_reply,
            booking_intent=False,
            rag_context="",
            processed_at=datetime.now(UTC),
        )
