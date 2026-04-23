import re
from datetime import date

from langchain_core.messages import BaseMessage

from app.documents import ServiceLogEventType


def get_last_user_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if message.type == "human":
            return str(message.content)
    return ""


def extract_service_log_payload(text: str) -> dict[str, object]:
    payload: dict[str, object] = {}

    reservation_match = re.search(r"\b[a-f0-9]{24}\b", text, flags=re.IGNORECASE)
    if reservation_match:
        payload["reservation_id"] = reservation_match.group(0)

    lowered = text.lower()
    event_map = {
        "arrival": ServiceLogEventType.ARRIVAL,
        "arribo": ServiceLogEventType.ARRIVAL,
        "llegada": ServiceLogEventType.ARRIVAL,
        "departure": ServiceLogEventType.DEPARTURE,
        "salida": ServiceLogEventType.DEPARTURE,
        "checkpoint": ServiceLogEventType.CHECKPOINT,
        "cierre": ServiceLogEventType.CLOSURE,
        "closure": ServiceLogEventType.CLOSURE,
        "incidente": ServiceLogEventType.INCIDENT,
        "incident": ServiceLogEventType.INCIDENT,
        "nota": ServiceLogEventType.NOTE,
        "note": ServiceLogEventType.NOTE,
    }
    for keyword, event_type in event_map.items():
        if keyword in lowered:
            payload["event_type"] = event_type
            break

    timestamp_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})", text)
    if timestamp_match:
        payload["happened_at"] = timestamp_match.group(0)

    checkpoint_match = re.search(r"checkpoint\s*[:=]\s*([^,.;\n]+)", text, flags=re.IGNORECASE)
    if checkpoint_match:
        payload["checkpoint_name"] = checkpoint_match.group(1).strip()

    equine_match = re.search(r"equine[_\s-]?id\s*[:=]\s*([a-f0-9]{24})", text, flags=re.IGNORECASE)
    if equine_match:
        payload["related_equine_id"] = equine_match.group(1)

    description_match = re.search(r"description\s*[:=]\s*([^\n]+)", text, flags=re.IGNORECASE)
    if description_match:
        payload["notes"] = description_match.group(1).strip()
    elif "description" not in lowered and len(text.strip()) > 0:
        payload["notes"] = text.strip()

    return payload


def classify_booking_intent(text: str) -> bool:
    lowered = text.lower()
    hard_signals = (
        "reservar",
        "reserva",
        "confirmar fecha",
        "confirmo fecha",
        "agendar",
        "quiero ir",
        "separar cupo",
        "cupo",
    )
    if any(signal in lowered for signal in hard_signals):
        return True

    has_date = bool(re.search(r"\d{4}-\d{2}-\d{2}", lowered))
    asks_price = any(token in lowered for token in ("precio", "cost", "tarifa", "valor"))
    return has_date and not asks_price


def extract_booking_request(text: str) -> dict[str, object]:
    lowered = text.lower()
    payload: dict[str, object] = {"participant_count": 1, "requested_date": None}

    experience_match = re.search(r"experience[_\s-]?id\s*[:=]\s*([a-f0-9]{24})", text, flags=re.IGNORECASE)
    if experience_match:
        payload["experience_id"] = experience_match.group(1)

    participants_match = re.search(
        r"(\d+)\s*(?:persona|personas|participante|participantes|cupo|cupos)",
        lowered,
    )
    if participants_match:
        payload["participant_count"] = int(participants_match.group(1))

    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", lowered)
    if date_match:
        payload["requested_date"] = date.fromisoformat(date_match.group(1))

    name_match = re.search(r"nombre\s*[:=]\s*([^\n,.;]+)", text, flags=re.IGNORECASE)
    if name_match:
        payload["holder_name"] = name_match.group(1).strip()

    email_match = re.search(r"\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b", text)
    if email_match:
        payload["holder_email"] = email_match.group(0)

    phone_match = re.search(r"\b(?:\+?57)?\s?3\d{9}\b", text)
    if phone_match:
        payload["holder_phone"] = phone_match.group(0).replace(" ", "")

    asks_price = any(token in lowered for token in ("precio", "tarifa", "valor", "costo"))
    payload["asks_price_only"] = asks_price
    return payload


class StubVectorClient:
    _knowledge_base = [
        "Las experiencias se operan sobre fechas en agenda con control de cupos y estado operativo.",
        "Las reservas pueden crearse sin confirmación y avanzar a pending_payment cuando se concreta intención de compra.",
        "La confirmación final requiere reglas de negocio: cupos, anticipación mínima y, si aplica, comprobante de pago.",
    ]

    async def search(self, query: str, top_k: int = 3) -> str:
        if not query.strip():
            return "No se recibió una consulta para buscar contexto."
        snippets = self._knowledge_base[:max(1, top_k)]
        return "\n".join(f"- {snippet}" for snippet in snippets)
