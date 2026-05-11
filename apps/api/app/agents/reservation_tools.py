from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from difflib import SequenceMatcher
import locale
from typing import Any, Literal

from beanie import PydanticObjectId
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator
from pymongo import UpdateOne
from pymongo.errors import DuplicateKeyError

from app.agents.tools import MongoDBVectorClient
from app.common.enums import Channel, ReservationStatus
from app.common.labels import ErrorCode
from app.core.config import settings
from app.core.errors import ApiError
from app.documents import ExperienceDocument, KnowledgeDocument, ReservationDocument
from app.services import ExperienceService, ReservationService

# Configurar locale para español (fallback a C si no está disponible)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass  # Usar locale por defecto

# Mapeo de meses en español para fallback
MONTH_NAMES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def _format_date_spanish(date_obj: date) -> str:
    """Formatea una fecha en español de forma robusta."""
    try:
        # Intentar usar locale
        return date_obj.strftime("%d de %B")
    except:
        # Fallback manual
        day = date_obj.day
        month = MONTH_NAMES_ES.get(date_obj.month, str(date_obj.month))
        return f"{day} de {month}"

ACTIVE_RESERVATION_STATUSES = {
    ReservationStatus.QUOTED,
    ReservationStatus.PENDING_PAYMENT,
    ReservationStatus.PAYMENT_RECEIVED,
    ReservationStatus.CONFIRMED,
}

WEEKDAY_NAMES = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}


class KnowledgeSearchInput(BaseModel):
    query: str = Field(min_length=2, max_length=512)
    top_k: int = Field(default=5, ge=1, le=10)


class KnowledgeSearchDocument(BaseModel):
    type: str
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperienceListInput(BaseModel):
    query: str | None = Field(default=None, max_length=256)


class ExperienceListDocument(BaseModel):
    id: str
    name: str
    description: str
    duration: str | None = None
    price: int | None = None
    capacity: int | None = None
    status: str


class AvailabilityCheckInput(BaseModel):
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        _parse_iso_date(value)
        return value


class AvailabilityCheckOutput(BaseModel):
    available: bool
    date: str
    blocking_reservation_id: str | None = None
    reason: str | None = None


class SuggestedDatesInput(BaseModel):
    requested_date: str
    days_forward: int = Field(default=14, ge=1, le=90)
    limit: int = Field(default=3, ge=1, le=5)

    @field_validator("requested_date")
    @classmethod
    def validate_requested_date(cls, value: str) -> str:
        _parse_iso_date(value)
        return value


class SuggestedDatesOutput(BaseModel):
    dates: list[str] = Field(default_factory=list)


class CreateReservationInput(BaseModel):
    experience_id: str
    date: str
    customer_name: str
    customer_phone: str
    people_count: int = Field(gt=0)
    notes: str | None = None
    source: Literal["whatsapp"] = "whatsapp"

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        _parse_iso_date(value)
        return value


class CreateReservationOutput(BaseModel):
    created: bool
    reservation_id: str | None = None
    status: str | None = None
    summary: str
    suggested_dates: list[str] = Field(default_factory=list)
    blocking_reservation_id: str | None = None


class UpdateReservationKnowledgeInput(BaseModel):
    reservation_id: str


class UpdateReservationKnowledgeOutput(BaseModel):
    updated: bool


class ReservationConversationInput(BaseModel):
    conversation_id: str | None = None
    whatsapp_phone: str | None = None
    experience_id: str | None = None
    experience_name: str | None = None
    requested_date: str | None = None
    people_count: int | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    notes: str | None = None
    intent: str | None = None
    booking_intent: bool = False
    availability: AvailabilityCheckOutput | None = None


class MissingReservationFieldsOutput(BaseModel):
    missing_fields: list[str] = Field(default_factory=list)
    next_question: str | None = None
    ready_to_create: bool = False


class ToolReply(BaseModel):
    text: str


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("date must be in YYYY-MM-DD format") from exc


def _today() -> date:
    return datetime.now(UTC).date()


def _normalize_text(value: str) -> str:
    return (
        value.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ü", "u")
    )


def _parse_relative_date(text: str, reference_date: date | None = None) -> date | None:
    normalized = _normalize_text(text)
    reference = reference_date or _today()

    iso_match = None
    for token in normalized.split():
        if len(token) == 10 and token[4] == "-" and token[7] == "-":
            try:
                iso_match = date.fromisoformat(token)
                break
            except ValueError:
                continue
    if iso_match is not None:
        return iso_match

    slash_match = None
    for token in normalized.split():
        if token.count("/") == 2:
            try:
                day, month, year = token.split("/")
                slash_match = date(int(year), int(month), int(day))
                break
            except ValueError:
                continue
    if slash_match is not None:
        return slash_match

    if "hoy" in normalized:
        return reference
    if "manana" in normalized:
        return reference + timedelta(days=1)

    for weekday_name, weekday_index in WEEKDAY_NAMES.items():
        if weekday_name in normalized:
            offset = (weekday_index - reference.weekday() + 7) % 7
            if offset == 0:
                offset = 7
            return reference + timedelta(days=offset)

    return None


def _parse_people_count(text: str) -> int | None:
    normalized = _normalize_text(text)
    for marker in ("personas", "pax", "participantes", "somos", "para"):
        match = None
        if marker in {"somos", "para"}:
            import re

            match = re.search(rf"\b{marker}\s+(\d{{1,3}})\b", normalized)
        else:
            import re

            match = re.search(rf"\b(\d{{1,3}})\s*{marker}\b", normalized)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    return None


def _extract_customer_name(text: str) -> str | None:
    import re

    patterns = [
        r"\bsoy\s+([a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+){0,3})\b",
        r"\bme\s+llamo\s+([a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+){0,3})\b",
        r"\bmi\s+nombre\s+es\s+([a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+){0,3})\b",
    ]
    normalized = _normalize_text(text)
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                return " ".join(part.capitalize() for part in candidate.split())
    return None


def _experience_duration_text(experience: ExperienceDocument) -> str | None:
    if getattr(experience, "duration", None) is not None:
        duration = experience.duration
        display = getattr(duration, "display_text", None)
        if display:
            return str(display)
        activity_minutes = getattr(duration, "activity_minutes", None)
        route_minutes = getattr(duration, "route_minutes", None)
        if activity_minutes and route_minutes:
            return f"{activity_minutes} min totales / {route_minutes} min de ruta"
    duration_hours = getattr(experience, "duration_hours", None)
    if duration_hours is not None:
        return f"{duration_hours} horas"
    duration_days = getattr(experience, "duration_days", None)
    if duration_days is not None:
        return f"{duration_days} días"
    return None


def _experience_price(experience: ExperienceDocument) -> int | None:
    pricing = getattr(experience, "pricing", None)
    if pricing is None:
        return None
    tiers = getattr(pricing, "tiers", None) or []
    prices = [getattr(tier, "price_per_person", None) for tier in tiers]
    prices = [price for price in prices if isinstance(price, int)]
    if prices:
        return min(prices)
    return None


def _experience_capacity(experience: ExperienceDocument) -> int | None:
    capacity = getattr(experience, "standard_max_participants", None)
    if capacity is not None:
        return capacity
    return getattr(experience, "base_capacity", None)


def _match_score(query: str, candidate: str) -> float:
    if not query or not candidate:
        return 0.0
    normalized_query = _normalize_text(query)
    normalized_candidate = _normalize_text(candidate)
    score = SequenceMatcher(None, normalized_query, normalized_candidate).ratio()
    if normalized_query in normalized_candidate or normalized_candidate in normalized_query:
        score = max(score, 0.9)
    return score


async def search_knowledge(
    payload: KnowledgeSearchInput,
    *,
    vector_client: MongoDBVectorClient | None = None,
) -> list[KnowledgeSearchDocument]:
    try:
        client = vector_client or MongoDBVectorClient()
        query = payload.query.strip()

        response = await client.client.embeddings.create(  # type: ignore[attr-defined]
            model=settings.chat_embedding_model,
            input=query,
        )
        query_vector = response.data[0].embedding

        collection = KnowledgeDocument.get_motor_collection()
        pipeline = [
            {
                "$vectorSearch": {
                    "index": settings.chat_vector_index_name,
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": payload.top_k * 10,
                    "limit": payload.top_k,
                    "filter": {"scope": {"$in": ["public", "ops"]}},
                }
            },
            {
                "$project": {
                    "type": 1,
                    "title": 1,
                    "content": 1,
                    "text": 1,
                    "metadata": 1,
                    "source": 1,
                    "scope": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        results = await collection.aggregate(pipeline).to_list(length=payload.top_k)
        documents: list[KnowledgeSearchDocument] = []
        for result in results:
            metadata = result.get("metadata") or {}
            if not isinstance(metadata, dict):
                metadata = {"value": metadata}
            metadata = {
                **metadata,
                "source": result.get("source"),
                "scope": result.get("scope"),
                "score": result.get("score"),
            }
            content = str(result.get("content") or result.get("text") or "").strip()
            documents.append(
                KnowledgeSearchDocument(
                    type=str(result.get("type") or metadata.get("type") or "knowledge"),
                    title=str(result.get("title") or metadata.get("title") or result.get("source") or ""),
                    content=content,
                    metadata={key: value for key, value in metadata.items() if value is not None},
                )
            )
        return documents
    except Exception:
        return []


async def list_experiences(
    payload: ExperienceListInput | None = None,
    *,
    experience_service: ExperienceService | None = None,
) -> list[ExperienceListDocument]:
    try:
        service = experience_service or ExperienceService()
        query = payload.query.strip() if payload and payload.query else None
        experiences = await service.list(is_active=True)

        mapped = [
            ExperienceListDocument(
                id=str(experience.id),
                name=experience.name,
                description=experience.description,
                duration=_experience_duration_text(experience),
                price=_experience_price(experience),
                capacity=_experience_capacity(experience),
                status=experience.status.value,
            )
            for experience in experiences
        ]

        if not query:
            return mapped

        scored = []
        for item in mapped:
            score = max(
                _match_score(query, item.name),
                _match_score(query, item.description),
            )
            scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        filtered = [item for score, item in scored if score >= 0.25]
        return filtered or mapped
    except Exception:
        return []


async def check_availability(
    payload: AvailabilityCheckInput,
    *,
    reservation_service: ReservationService | None = None,
) -> AvailabilityCheckOutput:
    service = reservation_service or ReservationService()
    requested_date = _parse_iso_date(payload.date)
    availability = await service.check_availability(requested_date)
    return AvailabilityCheckOutput.model_validate(availability)


async def suggest_available_dates(
    payload: SuggestedDatesInput,
    *,
    reservation_service: ReservationService | None = None,
) -> SuggestedDatesOutput:
    service = reservation_service or ReservationService()
    requested_date = _parse_iso_date(payload.requested_date)
    suggestions: list[str] = []
    current_date = requested_date + timedelta(days=1)

    while len(suggestions) < payload.limit and (current_date - requested_date).days <= payload.days_forward:
        availability = await service.check_availability(current_date)
        if availability["available"]:
            suggestions.append(current_date.isoformat())
        current_date += timedelta(days=1)

    return SuggestedDatesOutput(dates=suggestions)


async def create_reservation(
    payload: CreateReservationInput,
    *,
    reservation_service: ReservationService | None = None,
    experience_service: ExperienceService | None = None,
) -> CreateReservationOutput:
    reservation_service = reservation_service or ReservationService()
    experience_service = experience_service or ExperienceService()

    try:
        experience = await experience_service.get(payload.experience_id)
        if not getattr(experience, "is_active", True):
            return CreateReservationOutput(
                created=False,
                summary="Esa experiencia no está disponible en este momento. ¿Te gustaría ver otras opciones?",
            )
    except ApiError:
        return CreateReservationOutput(
            created=False,
            summary="No encontré esa experiencia. ¿Me puedes decir cuál te interesa?",
        )

    requested_date = _parse_iso_date(payload.date)
    availability = await reservation_service.check_availability(requested_date)
    if not availability["available"]:
        suggestions = await suggest_available_dates(
            SuggestedDatesInput(requested_date=payload.date),
            reservation_service=reservation_service,
        )
        
        # Mensaje más natural cuando la fecha está ocupada
        date_str = _format_date_spanish(requested_date)
        alt_dates_text = ""
        if suggestions.dates:
            formatted_dates = []
            for date_iso in suggestions.dates[:3]:
                try:
                    alt_date = _parse_iso_date(date_iso)
                    formatted_dates.append(_format_date_spanish(alt_date))
                except:
                    pass
            if formatted_dates:
                if len(formatted_dates) == 1:
                    alt_dates_text = f" Pero tengo disponible el {formatted_dates[0]}. ¿Te sirve?"
                elif len(formatted_dates) == 2:
                    alt_dates_text = f" Pero tengo disponible el {formatted_dates[0]} o el {formatted_dates[1]}. ¿Cuál te acomoda mejor?"
                else:
                    alt_dates_text = f" Pero tengo disponible el {formatted_dates[0]}, {formatted_dates[1]} o el {formatted_dates[2]}. ¿Alguno te sirve?"
        
        summary = f"El {date_str} ya está reservado.{alt_dates_text}" if alt_dates_text else f"El {date_str} ya está reservado. ¿Tienes otra fecha en mente?"
        
        return CreateReservationOutput(
            created=False,
            summary=summary,
            blocking_reservation_id=availability["blocking_reservation_id"],
            suggested_dates=suggestions.dates,
        )

    reservation_payload = {
        "experience_id": payload.experience_id,
        "requested_date": requested_date,
        "participant_count": payload.people_count,
        "channel": Channel.WHATSAPP,
        "holder_name": payload.customer_name,
        "holder_phone": payload.customer_phone,
    }

    try:
        reservation = await reservation_service.create(
            reservation_payload,
            initial_status=ReservationStatus.QUOTED,
        )
        reservation = await reservation_service.set_status(
            str(reservation.id),
            ReservationStatus.PENDING_PAYMENT,
        )
    except ApiError:
        suggestions = await suggest_available_dates(
            SuggestedDatesInput(requested_date=payload.date),
            reservation_service=reservation_service,
        )
        return CreateReservationOutput(
            created=False,
            summary="Ups, esa fecha se acaba de ocupar. ¿Quieres que te proponga otras fechas?",
            suggested_dates=suggestions.dates,
        )
    except DuplicateKeyError:
        suggestions = await suggest_available_dates(
            SuggestedDatesInput(requested_date=payload.date),
            reservation_service=reservation_service,
        )
        return CreateReservationOutput(
            created=False,
            summary="Esa fecha se acaba de reservar. ¿Te sirve otra fecha?",
            suggested_dates=suggestions.dates,
        )

    # Mensaje de confirmación más cálido y humano
    date_str = _format_date_spanish(requested_date)
    people_text = f"{payload.people_count} persona" if payload.people_count == 1 else f"{payload.people_count} personas"
    experience_name = getattr(experience, "name", "la experiencia")
    
    summary = (
        f"¡Listo {payload.customer_name}! 🎉 Tu reserva está confirmada para {experience_name} "
        f"el {date_str} para {people_text}. "
        f"Tu código de reserva es {reservation.code}. "
        f"Ahora te envío los detalles de pago para asegurar tu cupo ✨"
    )
    
    return CreateReservationOutput(
        created=True,
        reservation_id=str(reservation.id),
        status=reservation.status.value,
        summary=summary,
    )


async def update_reservation_knowledge(
    payload: UpdateReservationKnowledgeInput,
    *,
    reservation_service: ReservationService | None = None,
    experience_service: ExperienceService | None = None,
) -> UpdateReservationKnowledgeOutput:
    reservation_service = reservation_service or ReservationService()
    experience_service = experience_service or ExperienceService()
    try:
        reservation = await reservation_service.get(payload.reservation_id)
        experience = await experience_service.get(str(reservation.experience_id))
        requested_date = reservation.requested_date
        if requested_date is None and reservation.schedule_id is not None:
            from app.documents import ScheduleDocument

            schedule = await ScheduleDocument.get(reservation.schedule_id)
            if schedule is not None:
                requested_date = schedule.date

        if requested_date is None:
            return UpdateReservationKnowledgeOutput(updated=False)

        blocks_day = reservation.status in ACTIVE_RESERVATION_STATUSES
        if blocks_day:
            content = f"La fecha {requested_date.isoformat()} está ocupada por una reserva activa."
        else:
            content = f"La fecha {requested_date.isoformat()} no está ocupada por una reserva activa."

        knowledge_document = {
            "source": f"reservation_availability:{reservation.id}",
            "type": "reservation_availability",
            "title": f"Disponibilidad {requested_date.isoformat()}",
            "content": content,
            "text": content,
            "scope": "public",
            "metadata": {
                "reservation_id": str(reservation.id),
                "date": requested_date.isoformat(),
                "experience_id": str(reservation.experience_id),
                "experience_name": experience.name,
                "status": reservation.status.value,
                "blocks_day": blocks_day,
            },
        }

        collection = KnowledgeDocument.get_motor_collection()
        await collection.update_one(
            {"source": knowledge_document["source"]},
            {"$set": knowledge_document},
            upsert=True,
        )
        return UpdateReservationKnowledgeOutput(updated=True)
    except Exception:
        return UpdateReservationKnowledgeOutput(updated=False)


def collect_missing_reservation_fields(
    payload: ReservationConversationInput,
) -> MissingReservationFieldsOutput:
    missing_fields: list[str] = []

    if not payload.experience_id:
        missing_fields.append("experience_id")
    if not payload.requested_date:
        missing_fields.append("requested_date")
    if not payload.people_count or payload.people_count <= 0:
        missing_fields.append("people_count")
    if not payload.customer_name:
        missing_fields.append("customer_name")
    if not (payload.customer_phone or payload.whatsapp_phone):
        missing_fields.append("customer_phone")

    if missing_fields:
        next_field = missing_fields[0]
        # Preguntas más naturales y conversacionales
        question_map = {
            "experience_id": "¿Qué experiencia te gustaría vivir? Tenemos cabalgatas y paseos increíbles 🐴",
            "requested_date": "Perfecto, ¿para qué fecha te gustaría la experiencia?",
            "people_count": "¿Para cuántas personas sería?",
            "customer_name": "¡Genial! ¿Me compartes tu nombre para la reserva?",
            "customer_phone": "Y por último, ¿me confirmas tu número de contacto?",
        }
        return MissingReservationFieldsOutput(
            missing_fields=missing_fields,
            next_question=question_map.get(next_field),
            ready_to_create=False,
        )

    return MissingReservationFieldsOutput(
        missing_fields=[],
        next_question=None,
        ready_to_create=True,
    )


__all__ = [
    "AvailabilityCheckInput",
    "AvailabilityCheckOutput",
    "CreateReservationInput",
    "CreateReservationOutput",
    "ExperienceListDocument",
    "ExperienceListInput",
    "KnowledgeSearchDocument",
    "KnowledgeSearchInput",
    "MissingReservationFieldsOutput",
    "ReservationConversationInput",
    "SuggestedDatesInput",
    "SuggestedDatesOutput",
    "ToolReply",
    "UpdateReservationKnowledgeInput",
    "UpdateReservationKnowledgeOutput",
    "check_availability",
    "collect_missing_reservation_fields",
    "create_reservation",
    "list_experiences",
    "search_knowledge",
    "suggest_available_dates",
    "update_reservation_knowledge",
]
