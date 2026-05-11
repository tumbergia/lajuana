from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.agents.reservation_tools import (
    AvailabilityCheckInput,
    CreateReservationInput,
    ExperienceListInput,
    KnowledgeSearchInput,
    MissingReservationFieldsOutput,
    ReservationConversationInput,
    SuggestedDatesInput,
    UpdateReservationKnowledgeInput,
    check_availability,
    collect_missing_reservation_fields,
    create_reservation,
    list_experiences,
    search_knowledge,
    suggest_available_dates,
    update_reservation_knowledge,
    _extract_customer_name,
    _parse_people_count,
    _parse_relative_date,
)
from app.agents.state import GraphState

BOOKING_INTENTS = {"create_reservation", "check_availability", "list_experiences"}


def _last_user_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if message.type == "human":
            return str(message.content)
    return ""


def _normalize_messages(state: GraphState) -> list[BaseMessage]:
    messages = list(state.get("messages", []))
    return messages


def _best_experience_match(query: str, options: list[Any]) -> Any | None:
    normalized_query = query.lower().strip()
    best_score = 0.0
    best_option = None
    for option in options:
        name = str(getattr(option, "name", "")).lower()
        description = str(getattr(option, "description", "")).lower()
        haystack = " ".join(part for part in (name, description) if part)
        if not haystack:
            continue
        score = 0.0
        if normalized_query in haystack or haystack in normalized_query:
            score = 0.95
        else:
            from difflib import SequenceMatcher

            score = SequenceMatcher(None, normalized_query, haystack).ratio()
        if score > best_score:
            best_score = score
            best_option = option
    if best_score >= 0.45:
        return best_option
    return None


def _classification_for_text(text: str) -> str:
    normalized = text.lower()
    
    # Palabras clave para reserva (más amplio)
    reservation_keywords = (
        "reserv", "reserva", "apartar", "agendar", "programar", "separar", "cupo",
        "cabalgata", "fecha", "personas", "pax", "quiero", "quisiera", "me gustaria",
        "puedo", "podemos", "ir", "visitar", "conocer", "paseo", "tour", "plan"
    )
    
    # Palabras clave para disponibilidad
    availability_keywords = ("disponib", "hay lugar", "fecha libre", "libre", "pueden", "hay cupo")
    
    # Palabras clave para listar experiencias
    experience_keywords = ("experiencia", "experiencias", "que ofrecen", "qué ofrecen", "catalogo", "catálogo", "opciones", "que tienen", "qué tienen")
    
    # Saludos y conversación general (no forzar a reserva inmediatamente)
    greeting_keywords = ("hola", "buenos dias", "buenas tardes", "buenas noches", "saludos", "hey", "alo")
    
    # Si es solo un saludo sin más contexto, tratarlo como knowledge_query
    if any(keyword in normalized for keyword in greeting_keywords) and len(normalized.split()) <= 3:
        return "knowledge_query"
    
    # Priorizar intención de reserva
    if any(keyword in normalized for keyword in reservation_keywords):
        return "create_reservation"
    
    if any(keyword in normalized for keyword in availability_keywords):
        return "check_availability"
    
    if any(keyword in normalized for keyword in experience_keywords):
        return "list_experiences"
    
    return "knowledge_query"


async def receive_message_node(state: GraphState, deps: Any) -> dict[str, Any]:
    messages = _normalize_messages(state)
    last_user_text = state.get("user_message") or _last_user_text(messages)
    booking_intent = bool(state.get("booking_intent", False)) or _classification_for_text(last_user_text) in BOOKING_INTENTS
    return {
        "user_message": last_user_text,
        "booking_intent": booking_intent,
        "source": state.get("source", "whatsapp"),
        "errors": list(state.get("errors", [])),
    }


async def classify_intent_node(state: GraphState, deps: Any) -> dict[str, Any]:
    text = str(state.get("user_message") or _last_user_text(_normalize_messages(state)))
    intent = _classification_for_text(text)
    return {
        "intent": intent,
        "booking_intent": intent in BOOKING_INTENTS,
    }


async def extract_entities_node(state: GraphState, deps: Any) -> dict[str, Any]:
    text = str(state.get("user_message") or _last_user_text(_normalize_messages(state)))
    extracted_data = dict(state.get("extracted_data", {}))

    # Mantener datos previos si ya existen
    requested_date = state.get("requested_date")
    if not requested_date:
        parsed_date = _parse_relative_date(text)
        if parsed_date is not None:
            requested_date = parsed_date.isoformat()

    people_count = state.get("people_count")
    if not people_count:
        people_count = _parse_people_count(text)

    customer_name = state.get("customer_name")
    if not customer_name:
        customer_name = _extract_customer_name(text)
    
    customer_phone = state.get("customer_phone") or state.get("whatsapp_phone")

    experience_options = list(state.get("experience_options", []))
    selected_experience_id = state.get("experience_id")
    selected_experience_name = state.get("experience_name")
    
    # Solo buscar experiencias si no tenemos una seleccionada o si el mensaje menciona una experiencia
    should_search_experiences = (
        not selected_experience_id 
        or any(keyword in text.lower() for keyword in ("experiencia", "cabalgata", "paseo", "tour"))
    )

    if should_search_experiences and hasattr(deps, "experience_service"):
        experience_query = selected_experience_name or text
        try:
            experiences = await list_experiences(
                ExperienceListInput(query=experience_query),
                experience_service=deps.experience_service,
            )
            if experiences:
                experience_options = [experience.model_dump() for experience in experiences[:5]]
                
                # Intentar match solo si no tenemos experiencia seleccionada
                if not selected_experience_id:
                    best_match = _best_experience_match(text, experiences)
                    if best_match is None and len(experiences) == 1:
                        best_match = experiences[0]
                    if best_match is not None:
                        selected_experience_id = best_match.id
                        selected_experience_name = best_match.name
        except Exception:
            pass  # Mantener valores previos si falla

    extracted_data.update(
        {
            "experience_id": selected_experience_id,
            "experience_name": selected_experience_name,
            "requested_date": requested_date,
            "people_count": people_count,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
        }
    )

    return {
        "experience_id": selected_experience_id,
        "experience_name": selected_experience_name,
        "requested_date": requested_date,
        "people_count": people_count,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "experience_options": experience_options,
        "extracted_data": extracted_data,
    }


async def retrieve_context_node(state: GraphState, deps: Any) -> dict[str, Any]:
    text = str(state.get("user_message") or _last_user_text(_normalize_messages(state)))
    intent = state.get("intent") or "knowledge_query"
    knowledge_docs = []
    experience_options = state.get("experience_options", [])
    
    # Solo buscar conocimiento si no es una intención de reserva clara
    # o si el usuario está haciendo una pregunta específica
    should_search_knowledge = (
        intent == "knowledge_query" 
        or "?" in text 
        or any(keyword in text.lower() for keyword in ("qué", "que", "cómo", "como", "cuál", "cual", "dónde", "donde", "cuándo", "cuando"))
    )

    if should_search_knowledge:
        try:
            knowledge_docs = [
                document.model_dump()
                for document in await search_knowledge(
                    KnowledgeSearchInput(query=text, top_k=3),  # Reducir a 3 para ser más eficiente
                    vector_client=getattr(deps, "vector_client", None),
                )
            ]
        except Exception as exc:
            # No agregar error si es una reserva, solo si es consulta de conocimiento
            if intent == "knowledge_query":
                errors = list(state.get("errors", []))
                errors.append(f"knowledge_search_failed:{exc.__class__.__name__}")
                return {"errors": errors, "rag_context": ""}

    rag_lines = []
    
    # Agregar contexto de conocimiento solo si es relevante
    if knowledge_docs:
        for document in knowledge_docs[:3]:
            title = document.get("title") or document.get("type") or "Información"
            content = document.get("content") or ""
            if content:  # Solo agregar si hay contenido
                rag_lines.append(f"{title}: {content}")

    # Agregar experiencias disponibles si es relevante
    if experience_options and (intent in {"create_reservation", "list_experiences", "check_availability"}):
        exp_names = [item.get("name", "") for item in experience_options if item.get("name")]
        if exp_names:
            rag_lines.append(f"Experiencias disponibles: {', '.join(exp_names)}")

    return {
        "knowledge_context": knowledge_docs,
        "rag_context": "\n".join(line for line in rag_lines if line),
    }


async def check_availability_node(state: GraphState, deps: Any) -> dict[str, Any]:
    intent = state.get("intent")
    
    # Solo verificar disponibilidad si es necesario
    if intent not in {"create_reservation", "check_availability"}:
        return {}
    
    requested_date = state.get("requested_date")
    if not requested_date:
        return {}

    try:
        availability = await check_availability(
            AvailabilityCheckInput(date=requested_date),
            reservation_service=getattr(deps, "reservation_service", None),
        )
        update: dict[str, Any] = {"availability": availability.model_dump()}
        
        # Solo sugerir fechas alternativas si la fecha no está disponible Y es una intención de crear reserva
        if not availability.available and intent == "create_reservation":
            try:
                suggestions = await suggest_available_dates(
                    SuggestedDatesInput(requested_date=requested_date),
                    reservation_service=getattr(deps, "reservation_service", None),
                )
                update["suggested_dates"] = suggestions.dates
            except Exception:
                update["suggested_dates"] = []
        
        return update
    except Exception as exc:
        # Si falla la verificación, registrar error pero continuar
        errors = list(state.get("errors", []))
        errors.append(f"availability_check_failed:{exc.__class__.__name__}")
        return {"errors": errors}


async def collect_missing_data_node(state: GraphState, deps: Any) -> dict[str, Any]:
    if state.get("intent") not in {"create_reservation", "check_availability"}:
        return {"missing_fields": [], "next_question": None, "ready_to_create": False}

    result: MissingReservationFieldsOutput = collect_missing_reservation_fields(
        ReservationConversationInput(
            conversation_id=state.get("conversation_id"),
            whatsapp_phone=state.get("whatsapp_phone"),
            experience_id=state.get("experience_id"),
            experience_name=state.get("experience_name"),
            requested_date=state.get("requested_date"),
            people_count=state.get("people_count"),
            customer_name=state.get("customer_name"),
            customer_phone=state.get("customer_phone"),
            notes=state.get("notes"),
            intent=state.get("intent"),
            booking_intent=bool(state.get("booking_intent", False)),
            availability=None,
        )
    )
    return result.model_dump()


async def create_reservation_node(state: GraphState, deps: Any) -> dict[str, Any]:
    if state.get("intent") != "create_reservation":
        return {}
    if state.get("missing_fields"):
        return {}
    availability = state.get("availability") or {}
    if availability and availability.get("available") is False:
        return {}

    result = await create_reservation(
        CreateReservationInput(
            experience_id=str(state.get("experience_id")),
            date=str(state.get("requested_date")),
            customer_name=str(state.get("customer_name")),
            customer_phone=str(state.get("customer_phone") or state.get("whatsapp_phone") or ""),
            people_count=int(state.get("people_count") or 0),
            notes=state.get("notes"),
        ),
        reservation_service=getattr(deps, "reservation_service", None),
        experience_service=getattr(deps, "experience_service", None),
    )

    update: dict[str, Any] = {
        "reservation_summary": result.summary,
        "reservation_id": result.reservation_id,
        "reservation_status": result.status,
        "suggested_dates": result.suggested_dates,
        "sync_knowledge_required": bool(result.created and result.reservation_id),
    }
    if result.blocking_reservation_id or result.suggested_dates:
        update["availability"] = {
            "available": False,
            "date": str(state.get("requested_date")),
            "blocking_reservation_id": result.blocking_reservation_id,
            "reason": None if result.created else result.summary,
        }
    if not result.created:
        update.setdefault("errors", [])
        update["errors"] = list(state.get("errors", [])) + ["reservation_create_rejected"]
    return update


async def sync_knowledge_node(state: GraphState, deps: Any) -> dict[str, Any]:
    if not state.get("sync_knowledge_required") or not state.get("reservation_id"):
        return {}
    result = await update_reservation_knowledge(
        UpdateReservationKnowledgeInput(reservation_id=str(state.get("reservation_id"))),
        reservation_service=getattr(deps, "reservation_service", None),
        experience_service=getattr(deps, "experience_service", None),
    )
    return {
        "sync_knowledge_required": False,
        "reservation_knowledge_synced": result.updated,
    }


async def respond_to_user_node(state: GraphState, deps: Any) -> dict[str, Any]:
    intent = state.get("intent") or "knowledge_query"
    availability = state.get("availability") or {}
    
    # Validación robusta de mensajes
    try:
        messages = _normalize_messages(state)
    except Exception:
        messages = []
    
    user_message = state.get("user_message") or _last_user_text(messages) if messages else ""
    
    # Construir contexto conversacional más rico
    context_payload = {
        "mensaje_usuario": user_message,
        "intent": intent,
        "booking_intent": bool(state.get("booking_intent", False)),
        "experience_id": state.get("experience_id"),
        "experience_name": state.get("experience_name"),
        "experience_options": state.get("experience_options", [])[:5],
        "requested_date": state.get("requested_date"),
        "people_count": state.get("people_count"),
        "customer_name": state.get("customer_name"),
        "customer_phone": state.get("customer_phone") or state.get("whatsapp_phone"),
        "availability": {
            "available": availability.get("available"),
            "date": availability.get("date"),
            "reason": availability.get("reason"),
        }
        if availability
        else None,
        "suggested_dates": state.get("suggested_dates", [])[:5],
        "missing_fields": state.get("missing_fields", []),
        "next_question": state.get("next_question"),
        "reservation_id": state.get("reservation_id"),
        "reservation_status": state.get("reservation_status"),
        "reservation_summary": state.get("reservation_summary"),
        "knowledge_context": state.get("knowledge_context", [])[:3],
        "rag_context": state.get("rag_context", ""),
        "errors": state.get("errors", []),
    }

    system_prompt = SystemMessage(
        content=(
            "Eres el asistente de La Juana, un lugar de cabalgatas y experiencias con caballos. "
            "Tu nombre es Juana y hablas por WhatsApp con los clientes de forma natural, cálida y cercana. "
            "\n\n"
            "PERSONALIDAD:\n"
            "- Habla como una persona real, no como un bot\n"
            "- Usa un tono amigable, campestre y acogedor\n"
            "- Sé breve pero completo en tus respuestas\n"
            "- Usa emojis ocasionalmente para dar calidez (🐴 🌄 ✨)\n"
            "- Tutea al cliente de forma natural\n"
            "\n"
            "REGLAS IMPORTANTES:\n"
            "- NUNCA inventes información que no esté en el contexto\n"
            "- Si falta un dato para reservar, pide SOLO ese dato de forma conversacional\n"
            "- Si la reserva se creó, confirma con entusiasmo y explica el siguiente paso\n"
            "- Si la fecha no está disponible, ofrece alternativas con naturalidad\n"
            "- No uses listas numeradas ni formato técnico\n"
            "- No menciones 'contexto', 'sistema', 'base de datos' ni términos técnicos\n"
            "- Responde siempre en español\n"
            "\n"
            "EJEMPLOS DE BUEN TONO:\n"
            "- '¡Hola! Claro que sí, te ayudo con tu reserva 🐴'\n"
            "- 'Perfecto, ¿para cuántas personas sería la cabalgata?'\n"
            "- 'Listo, tu reserva está confirmada para el 15 de mayo. Te voy a enviar los detalles de pago por acá mismo ✨'\n"
            "- 'Ese día ya está ocupado, pero tengo disponible el sábado 17 o el domingo 18. ¿Te sirve alguno?'\n"
        )
    )
    
    # Incluir historial reciente para contexto conversacional (con validación)
    conversation_history = ""
    if messages and len(messages) > 1:
        try:
            recent_messages = messages[-4:] if len(messages) > 4 else messages
            history_lines = []
            for msg in recent_messages[:-1]:  # Excluir el último mensaje
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    role = 'Cliente' if msg.type == 'human' else 'Juana'
                    history_lines.append(f"{role}: {msg.content}")
            conversation_history = "\n".join(history_lines)
        except Exception:
            conversation_history = ""
    
    user_prompt = HumanMessage(
        content=(
            f"Conversación previa:\n{conversation_history}\n\n"
            if conversation_history else ""
        ) + (
            f"Mensaje actual del cliente: {user_message}\n\n"
            f"Contexto de la conversación:\n{json.dumps(context_payload, ensure_ascii=False, indent=2)}\n\n"
            "Responde al cliente de forma natural y humana, como si fueras Juana hablando por WhatsApp. "
            "Un solo mensaje, directo y cálido."
        )
    )

    try:
        response = await deps.chat_model.ainvoke([system_prompt, user_prompt])
        reply = str(response.content).strip()
        
        # Si la respuesta es muy corta o parece incompleta, intentar mejorarla
        if len(reply) < 20 or not any(char in reply for char in ".!?"):
            refined = await deps.chat_model.ainvoke(
                [
                    system_prompt,
                    HumanMessage(
                        content=(
                            f"El mensaje '{reply}' es demasiado corto o incompleto. "
                            f"Reformúlalo para que sea más completo y natural, manteniendo el mismo contexto:\n"
                            f"{json.dumps(context_payload, ensure_ascii=False, indent=2)}"
                        )
                    ),
                ]
            )
            refined_text = str(refined.content).strip()
            if refined_text and len(refined_text) > len(reply):
                reply = refined_text
    except Exception as exc:
        # Fallback con respuestas más humanas según el contexto
        if state.get("next_question"):
            reply = state.get("next_question")
        elif state.get("reservation_summary"):
            reply = state.get("reservation_summary")
        elif state.get("missing_fields"):
            field_names = {
                "experience_id": "qué experiencia te interesa",
                "requested_date": "para qué fecha",
                "people_count": "para cuántas personas",
                "customer_name": "tu nombre",
                "customer_phone": "tu número de contacto",
            }
            missing_fields_list = state.get("missing_fields", [])
            if missing_fields_list:
                first_missing = missing_fields_list[0]
                reply = f"Para continuar con tu reserva, necesito saber {field_names.get(first_missing, 'un dato más')} 🐴"
            else:
                reply = "¡Hola! Estoy aquí para ayudarte con tu reserva. ¿Qué experiencia te gustaría vivir? 🐴"
        else:
            reply = "¡Hola! Estoy aquí para ayudarte con tu reserva. ¿Qué experiencia te gustaría vivir? 🐴"

    if not reply:
        reply = "¡Hola! Estoy aquí para ayudarte con tu reserva. ¿Qué experiencia te gustaría vivir? 🐴"

    return {
        "messages": [AIMessage(content=reply)],
        "booking_intent": bool(state.get("booking_intent", False) or intent in BOOKING_INTENTS),
        "rag_context": state.get("rag_context", ""),
    }


__all__ = [
    "BOOKING_INTENTS",
    "classify_intent_node",
    "check_availability_node",
    "collect_missing_data_node",
    "create_reservation_node",
    "extract_entities_node",
    "receive_message_node",
    "respond_to_user_node",
    "retrieve_context_node",
    "sync_knowledge_node",
]
