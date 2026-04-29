"""Operational WhatsApp agent for La Juana reservations flow.

This module enforces business safeguards:
- it never confirms booking facts without backend tools;
- it asks for missing mandatory data explicitly;
- it escalates to human on backend conflicts and errors.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Protocol
from urllib import error, parse, request


SYSTEM_POLICY = """
Eres el agente conversacional operativo de La Juana para WhatsApp.

Tu funcion es asistir el flujo comercial y operativo de reservas,
pero NO eres la fuente de verdad del sistema.
La reserva es la entidad central.
Nunca inventas disponibilidad, precios, estados, pagos, confirmaciones
ni datos de participantes.
""".strip()


BACKEND_TO_BUSINESS_STATUS = {
    "contact": "contacto",
    "quoted": "cotizacion",
    "pending_payment": "pendiente_pago",
    "payment_received": "pago_recibido",
    "confirmed": "confirmada",
    "cancelled": "cancelada",
}

STATUS_TO_BACKEND = {
    "contacto": "contact",
    "cotizacion": "quoted",
    "cotizacion_": "quoted",
    "pendiente_pago": "pending_payment",
    "pago_recibido": "payment_received",
    "confirmada": "confirmed",
    "cancelada": "cancelled",
}

PAYMENT_STATUS_TO_SPANISH = {
    "pending": "pendiente",
    "received": "recibido",
    "verified": "verificado",
    "rejected": "rechazado",
}

TOOL_REQUIRED_INTENTS = {
    "availability_check",
    "quote_request",
    "reservation_create",
    "reservation_status_check",
    "payment_proof_received",
    "participant_data_request",
    "reservation_confirm",
}

RESERVATION_ID_PATTERN = re.compile(r"\b[a-f0-9]{24}\b", re.IGNORECASE)
RESERVATION_CODE_PATTERN = re.compile(r"\bRES-[A-Z0-9-]+\b", re.IGNORECASE)
ISO_DATE_PATTERN = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
LATAM_DATE_PATTERN = re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b")
PARTICIPANT_PATTERN = re.compile(r"\b(\d{1,2})\s*(personas?|pax|participantes?)\b", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-]{7,}\d")

RAG_STOPWORDS = {
    "de",
    "la",
    "el",
    "los",
    "las",
    "un",
    "una",
    "y",
    "en",
    "con",
    "para",
    "por",
    "que",
    "como",
    "del",
    "al",
    "se",
    "mi",
    "me",
    "te",
}


class BackendApiError(Exception):
    """Raised when the backend API returns an error response."""

    def __init__(self, status_code: int, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details or {}


class BackendToolsClient:
    """HTTP wrapper over the required reservation tools."""

    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        timeout_seconds: int = 20,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.timeout_seconds = timeout_seconds
        self.access_token: str | None = None

    def login(self) -> None:
        payload = {"email": self.email, "password": self.password}
        token_response = self._raw_request("POST", "/auth/login", payload=payload, auth=False)
        token = token_response.get("access_token")
        if not token:
            raise BackendApiError(500, "El backend no devolvio access_token.")
        self.access_token = str(token)

    def list_experiences(self, is_active: bool | None = True) -> list[dict[str, Any]]:
        query = None if is_active is None else {"is_active": str(is_active).lower()}
        return self._request("GET", "/experiences", query=query)

    def list_schedules(
        self,
        date_from: str | None = None,
        experience_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, str] = {}
        if date_from:
            query["date_from"] = date_from
        if experience_id:
            query["experience_id"] = experience_id
        return self._request("GET", "/schedules", query=query or None)

    def get_reservation_rules(self) -> dict[str, Any]:
        return self._request("GET", "/config/reservation-rules")

    def create_reservation(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/reservations", payload=payload)

    def get_reservation(self, reservation_id: str) -> dict[str, Any]:
        return self._request("GET", f"/reservations/{reservation_id}")

    def transition_reservation_status(
        self,
        reservation_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self._request("POST", f"/reservations/{reservation_id}/status", payload=payload)

    def create_payment_proof(self, reservation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/reservations/{reservation_id}/payment-proofs", payload=payload)

    def create_participant(self, reservation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/reservations/{reservation_id}/participants", payload=payload)

    def confirm_reservation(self, reservation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/reservations/{reservation_id}/confirm", payload=payload)

    def get_emergency_contacts(self) -> dict[str, Any]:
        return self._request("GET", "/config/emergency-contacts")

    def _request(
        self,
        method: str,
        path: str,
        query: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        if self.access_token is None:
            self.login()
        try:
            return self._raw_request(method, path, query=query, payload=payload, auth=True)
        except BackendApiError as exc:
            if exc.status_code != 401:
                raise
            self.login()
            return self._raw_request(method, path, query=query, payload=payload, auth=True)

    def _raw_request(
        self,
        method: str,
        path: str,
        query: dict[str, str] | None = None,
        payload: dict[str, Any] | None = None,
        auth: bool = True,
    ) -> Any:
        query_string = f"?{parse.urlencode(query)}" if query else ""
        url = f"{self.base_url}{path}{query_string}"
        body = None
        headers: dict[str, str] = {"Accept": "application/json"}

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        req = request.Request(url=url, data=body, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
        except error.HTTPError as exc:
            body_text = exc.read().decode("utf-8") if exc.fp else ""
            parsed = _safe_json(body_text)
            message = _extract_backend_error_message(parsed) or f"HTTP {exc.code}"
            details = parsed if isinstance(parsed, dict) else {"body": body_text}
            raise BackendApiError(exc.code, message, details=details) from exc
        except error.URLError as exc:
            raise BackendApiError(503, "No fue posible conectar con el backend.") from exc


class LocalRagRetriever:
    """Very simple lexical retriever over local markdown/text files."""

    def __init__(self, sources: list[Path]) -> None:
        self.chunks = self._build_chunks(sources)

    def retrieve(self, query: str, max_chunks: int = 2) -> list[str]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[int, str]] = []
        for chunk in self.chunks:
            chunk_tokens = _tokenize(chunk)
            overlap = len(query_tokens.intersection(chunk_tokens))
            if overlap > 0:
                scored.append((overlap, chunk))

        if not scored:
            return []

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [item[1] for item in scored[:max_chunks]]
        return selected

    def answer(self, query: str, max_chunks: int = 2) -> str | None:
        selected = self.retrieve(query, max_chunks=max_chunks)
        if not selected:
            return None
        return "\n".join(_trim_for_whatsapp(text) for text in selected)

    @staticmethod
    def _build_chunks(sources: list[Path]) -> list[str]:
        chunks: list[str] = []
        for source in sources:
            if not source.exists() or not source.is_file():
                continue
            text = source.read_text(encoding="utf-8", errors="ignore")
            paragraphs = [segment.strip() for segment in re.split(r"\n\s*\n", text)]
            chunks.extend(segment for segment in paragraphs if len(segment) > 40)
        return chunks


class RagAnswerer(Protocol):
    def answer(self, query: str) -> str | None:
        """Return a short WhatsApp-ready answer based on RAG context."""


class OpenAICompatibleChatClient:
    """Minimal chat-completions client for OpenAI-compatible APIs."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_seconds: int = 600,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
        except (TimeoutError, socket.timeout) as exc:
            msg = f"LLM timeout after {self.timeout_seconds}s: el modelo tardó demasiado en responder."
            raise BackendApiError(504, msg) from exc
        except error.HTTPError as exc:
            body_text = exc.read().decode("utf-8") if exc.fp else ""
            raise BackendApiError(exc.code, f"LLM HTTP error: {body_text[:200]}") from exc
        except error.URLError as exc:
            raise BackendApiError(503, "No fue posible conectar con el proveedor LLM.") from exc

        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices:
            raise BackendApiError(500, "LLM sin contenido de respuesta.")
        first = choices[0]
        message = first.get("message", {}) if isinstance(first, dict) else {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise BackendApiError(500, "LLM devolvio contenido vacio.")
        return content.strip()


class GemmaRagGenerator:
    """RAG answerer that uses retrieved chunks + Gemma/OpenAI-compatible chat model.
    
    Features circuit breaker: if LLM fails N consecutive times, falls back to lexical RAG.
    """

    def __init__(
        self,
        retriever: LocalRagRetriever,
        llm_client: OpenAICompatibleChatClient,
        circuit_breaker_threshold: int = 3,
    ) -> None:
        self.retriever = retriever
        self.llm_client = llm_client
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.llm_failure_count = 0
        self.llm_enabled = True

    def answer(self, query: str) -> str | None:
        """Answer query using the prompt-only model, with optional retrieved context."""
        if not self.llm_enabled:
            return None

        chunks = self.retriever.retrieve(query, max_chunks=3)
        context = "\n\n".join(f"- {chunk}" for chunk in chunks) if chunks else ""
        system_prompt = (
            "Eres asistente de WhatsApp de La Juana. "
            "Responde breve, claro y profesional en espanol natural. "
            "Devuelve solo la respuesta final para WhatsApp. "
            "No incluyas thinking, analisis, JSON, etiquetas, markdown ni texto duplicado. "
            "No cites documentos internos ni menciones fuentes del sistema. "
            "Si el contexto no alcanza, responde de forma natural sin explicar el proceso interno."
        )
        user_prompt = (
            "Pregunta del usuario:\n"
            f"{query}\n\n"
            "Contexto disponible:\n"
            f"{context or 'Sin contexto adicional.'}\n\n"
            "Responde con un solo mensaje natural para WhatsApp."
        )
        
        try:
            answer = self.llm_client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            self.llm_failure_count = 0  # Reset on success
            return _clean_model_reply(answer)
        except BackendApiError as exc:
            # Increment failure counter
            self.llm_failure_count += 1
            
            # Circuit breaker: disable LLM after N consecutive failures
            if self.llm_failure_count >= self.circuit_breaker_threshold:
                self.llm_enabled = False
                print(f"[Circuit Breaker] LLM disabled after {self.llm_failure_count} failures")

            return None


@dataclass
class ConversationState:
    experience_id: str | None = None
    requested_date: str | None = None
    participant_count: int | None = None
    holder_name: str | None = None
    holder_email: str | None = None
    holder_phone: str | None = None
    reservation_id: str | None = None
    reservation_code: str | None = None


@dataclass
class TraceContext:
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    source: str = "rule"


class TraceLogger:
    def __init__(self, output_file: Path) -> None:
        self.output_file = output_file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: dict[str, Any]) -> None:
        with self.output_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


class WhatsAppOperationalAgent:
    """Operational reservation assistant for WhatsApp conversations."""

    def __init__(
        self,
        tools_client: BackendToolsClient,
        rag_retriever: LocalRagRetriever,
        trace_logger: TraceLogger,
        rag_answerer: RagAnswerer | None = None,
    ) -> None:
        self.tools_client = tools_client
        self.rag_retriever = rag_retriever
        self.trace_logger = trace_logger
        self.rag_answerer = rag_answerer
        self.state = ConversationState()

    def handle_message(
        self,
        user_text: str,
        *,
        payment_proof_payload: dict[str, Any] | None = None,
        participant_payload: dict[str, Any] | None = None,
    ) -> str:
        message = user_text.strip()
        trace = TraceContext()
        self._extract_entities(message)
        intent = "rag_only"
        response = self._answer_with_rag_model(message) or ""

        self._log_turn(message, intent, response, trace)
        return response

    def _handle_experience_faq(self, message: str, trace: TraceContext) -> str:
        # Prefer Gemma-backed RAG for general discovery questions.
        rag_answer = self._answer_with_rag_model(message)
        trace.source = "rag"
        if rag_answer:
            return _trim_for_whatsapp(rag_answer)
        return ""

    def _handle_policy_faq(self, message: str, trace: TraceContext) -> str:
        lower = _normalize(message)
        if "emergencia" in lower or "contacto" in lower:
            contacts = self._call_tool(trace, "get_emergency_contacts", {})
            items = contacts.get("items", []) if isinstance(contacts, dict) else []
            if not items:
                return "No tengo contactos de emergencia disponibles ahora. Escalo con un asesor."
            top = items[0]
            return (
                "Contacto principal de emergencia: "
                f"{top.get('name', 'N/A')} ({top.get('phone_number', 'N/A')})."
            )

        rules = self._call_tool(trace, "get_reservation_rules", {})
        min_days = rules.get("min_days_in_advance")
        require_payment = rules.get("require_payment_proof_for_confirmation")
        if min_days is None or require_payment is None:
            rag_answer = self._answer_with_rag_model(message)
            trace.source = "rag"
            return rag_answer or ""

        payment_text = "si" if require_payment else "no"
        return (
            "Reglas vigentes: "
            f"minimo {min_days} dias de anticipacion y comprobante de pago para confirmar: {payment_text}."
        )

    def _handle_availability(self, message: str, trace: TraceContext) -> str:
        missing_prompt = self._ensure_booking_context(message, trace)
        if missing_prompt:
            return missing_prompt

        schedules = self._call_tool(
            trace,
            "list_schedules",
            {
                "date_from": self.state.requested_date,
                "experience_id": self.state.experience_id,
            },
        )
        available = _filter_available_schedules(
            schedules,
            requested_date=self.state.requested_date,
            participant_count=self.state.participant_count,
        )

        if not available:
            return (
                f"No veo cupos para {self.state.requested_date}. "
                "Si quieres, te propongo otra fecha."
            )

        options = ", ".join(
            f"{item.get('start_time')} ({item.get('available_slots')} cupos)" for item in available[:3]
        )
        return (
            f"Para {self.state.requested_date} tengo: {options}. "
            "Si te sirve, te ayudo a avanzar la reserva."
        )

    def _handle_quote_request(self, message: str, trace: TraceContext) -> str:
        missing_prompt = self._ensure_booking_context(message, trace)
        if missing_prompt:
            return missing_prompt

        schedule = self._pick_schedule(trace)
        if schedule is None:
            return (
                f"No tengo disponibilidad real para {self.state.requested_date}. "
                "Te ayudo a revisar otra fecha."
            )

        reservation = self._call_tool(
            trace,
            "create_reservation",
            {
                "experience_id": self.state.experience_id,
                "schedule_id": schedule.get("id"),
                "requested_date": self.state.requested_date,
                "participant_count": self.state.participant_count,
                "channel": "whatsapp",
                "holder_name": self.state.holder_name,
                "holder_email": self.state.holder_email,
                "holder_phone": self.state.holder_phone,
            },
        )
        reservation_id = str(reservation.get("id"))
        self.state.reservation_id = reservation_id

        self._safe_transition(reservation_id, "quoted", trace)
        code = reservation.get("code", reservation_id)
        return (
            f"Listo, deje tu solicitud en cotizacion con codigo {code}. "
            "Cuando quieras continuamos con la reserva."
        )

    def _handle_reservation_create(self, message: str, trace: TraceContext) -> str:
        missing_prompt = self._ensure_booking_context(message, trace)
        if missing_prompt:
            return missing_prompt

        schedule = self._pick_schedule(trace)
        if schedule is None:
            return (
                f"No hay cupos confirmables para {self.state.requested_date}. "
                "Te ayudo con otra fecha disponible."
            )

        reservation = self._call_tool(
            trace,
            "create_reservation",
            {
                "experience_id": self.state.experience_id,
                "schedule_id": schedule.get("id"),
                "requested_date": self.state.requested_date,
                "participant_count": self.state.participant_count,
                "channel": "whatsapp",
                "holder_name": self.state.holder_name,
                "holder_email": self.state.holder_email,
                "holder_phone": self.state.holder_phone,
            },
        )
        reservation_id = str(reservation.get("id"))
        self.state.reservation_id = reservation_id

        self._safe_transition(reservation_id, "quoted", trace)
        self._safe_transition(reservation_id, "pending_payment", trace)

        code = reservation.get("code", reservation_id)
        return (
            f"Reserva creada con codigo {code}. "
            "Queda pendiente de pago. Cuando tengas comprobante, te ayudo a registrarlo."
        )

    def _handle_reservation_status(self, trace: TraceContext) -> str:
        if not self.state.reservation_id:
            if self.state.reservation_code:
                return (
                    "Recibi el codigo, pero para consultar estado necesito el ID interno "
                    "de la reserva (24 caracteres)."
                )
            return "Comparteme el ID de la reserva (24 caracteres) para revisar estado."

        reservation = self._call_tool(
            trace,
            "get_reservation",
            {"reservation_id": self.state.reservation_id},
        )
        backend_status = str(reservation.get("status", ""))
        payment_status = str(reservation.get("payment_status", ""))
        status_name = BACKEND_TO_BUSINESS_STATUS.get(backend_status, backend_status)
        payment_name = PAYMENT_STATUS_TO_SPANISH.get(payment_status, payment_status)
        return f"La reserva esta en {status_name}. Estado de pago: {payment_name}."

    def _handle_payment_proof(
        self,
        payment_proof_payload: dict[str, Any] | None,
        trace: TraceContext,
    ) -> str:
        if not self.state.reservation_id:
            return "Para registrar el comprobante, comparteme primero el ID de la reserva."

        if payment_proof_payload is None:
            return (
                "Listo. Enviame el comprobante con estos datos: "
                "filename, content_type, size_bytes, sha256 y content_base64."
            )

        _validate_payment_proof_payload(payment_proof_payload)
        self._call_tool(
            trace,
            "create_payment_proof",
            {
                "reservation_id": self.state.reservation_id,
                "payload": payment_proof_payload,
            },
        )

        reservation = self._call_tool(
            trace,
            "get_reservation",
            {"reservation_id": self.state.reservation_id},
        )
        if reservation.get("status") == "pending_payment":
            self._safe_transition(self.state.reservation_id, "payment_received", trace)

        return "Comprobante registrado. Tu reserva queda en pago_recibido y pasa a validacion."

    def _handle_participant(
        self,
        participant_payload: dict[str, Any] | None,
        trace: TraceContext,
    ) -> str:
        if not self.state.reservation_id:
            return "Para registrar participantes, comparteme primero el ID de la reserva."
        if participant_payload is None:
            return (
                "Enviame los datos del participante. "
                "Si quieres, te comparto el formato exacto para registrarlo en un mensaje."
            )

        missing_fields = _missing_participant_fields(participant_payload)
        if missing_fields:
            field_name = missing_fields[0]
            return f"Me falta un dato obligatorio del participante: {field_name}."

        participant = self._call_tool(
            trace,
            "create_participant",
            {
                "reservation_id": self.state.reservation_id,
                "payload": participant_payload,
            },
        )
        full_name = f"{participant.get('first_name', '')} {participant.get('last_name', '')}".strip()
        return f"Participante registrado: {full_name}."

    def _handle_confirm_request(self, trace: TraceContext) -> str:
        if not self.state.reservation_id:
            return "Para confirmar, comparteme el ID interno de la reserva."

        reservation = self._call_tool(
            trace,
            "get_reservation",
            {"reservation_id": self.state.reservation_id},
        )
        status = reservation.get("status")
        payment_status = reservation.get("payment_status")

        if status == "confirmed":
            return "La reserva ya esta confirmada."

        if payment_status not in {"received", "verified"}:
            return "Aun no puedo confirmar: falta pago validado o comprobante asociado."

        if status == "pending_payment":
            self._safe_transition(self.state.reservation_id, "payment_received", trace)

        confirmed = self._call_tool(
            trace,
            "confirm_reservation",
            {
                "reservation_id": self.state.reservation_id,
                "payload": {"notes": "Confirmada desde flujo WhatsApp"},
            },
        )
        code = confirmed.get("code", self.state.reservation_id)
        return f"Reserva confirmada correctamente. Codigo: {code}."

    def _ensure_booking_context(self, message: str, trace: TraceContext) -> str | None:
        if not self.state.experience_id:
            experiences = self._call_tool(trace, "list_experiences", {})
            match = _resolve_experience_id(message, experiences)
            if match:
                self.state.experience_id = match
            else:
                options = ", ".join(item.get("name", "") for item in experiences[:4] if item.get("name"))
                if options:
                    return f"Que experiencia te interesa? Opciones: {options}."
                return "Que experiencia quieres reservar?"

        if not self.state.requested_date:
            return "Para avanzar, que fecha deseas? Usa formato AAAA-MM-DD."

        if not self.state.participant_count:
            return "Cuantas personas serian para la reserva?"

        return None

    def _pick_schedule(self, trace: TraceContext) -> dict[str, Any] | None:
        schedules = self._call_tool(
            trace,
            "list_schedules",
            {
                "date_from": self.state.requested_date,
                "experience_id": self.state.experience_id,
            },
        )
        available = _filter_available_schedules(
            schedules,
            requested_date=self.state.requested_date,
            participant_count=self.state.participant_count,
        )
        return available[0] if available else None

    def _safe_transition(self, reservation_id: str, target_status: str, trace: TraceContext) -> None:
        self._call_tool(
            trace,
            "transition_reservation_status",
            {"reservation_id": reservation_id, "payload": {"target_status": target_status}},
        )

    def _call_tool(self, trace: TraceContext, name: str, args: dict[str, Any]) -> Any:
        trace.source = "tool"
        trace.tool_calls.append({"tool_name": name, "tool_args": args})

        if name == "list_experiences":
            return self.tools_client.list_experiences()
        if name == "list_schedules":
            return self.tools_client.list_schedules(
                date_from=args.get("date_from"),
                experience_id=args.get("experience_id"),
            )
        if name == "get_reservation_rules":
            return self.tools_client.get_reservation_rules()
        if name == "create_reservation":
            return self.tools_client.create_reservation(args)
        if name == "get_reservation":
            return self.tools_client.get_reservation(str(args["reservation_id"]))
        if name == "transition_reservation_status":
            return self.tools_client.transition_reservation_status(
                str(args["reservation_id"]),
                dict(args["payload"]),
            )
        if name == "create_payment_proof":
            return self.tools_client.create_payment_proof(
                str(args["reservation_id"]),
                dict(args["payload"]),
            )
        if name == "create_participant":
            return self.tools_client.create_participant(
                str(args["reservation_id"]),
                dict(args["payload"]),
            )
        if name == "confirm_reservation":
            return self.tools_client.confirm_reservation(
                str(args["reservation_id"]),
                dict(args["payload"]),
            )
        if name == "get_emergency_contacts":
            return self.tools_client.get_emergency_contacts()
        raise ValueError(f"Tool no soportada: {name}")

    def _handle_backend_error(self, exc: BackendApiError) -> str:
        if exc.status_code in {409, 422, 500, 502, 503}:
            return "Tu caso necesita revision humana por un conflicto operativo. Ya lo escalo."
        if exc.status_code == 404:
            return "No encontre ese registro en el backend. Verifica el ID y te ayudo de nuevo."
        if exc.status_code == 401:
            return "No pude autenticar el agente contra backend. Necesito revisar acceso."
        return f"No pude procesar la solicitud: {exc.message}."

    def _answer_with_rag_model(self, message: str) -> str | None:
        """Answer using the configured prompt-only model."""
        if self.rag_answerer is not None:
            try:
                answer = self.rag_answerer.answer(message)
                if answer:
                    return answer
            except BackendApiError as exc:
                # LLM failed (timeout, error, etc) - return no answer.
                print(f"[RAG Fallback] LLM error (status {exc.status_code}): {exc.message}")

        return None

    def _extract_entities(self, message: str) -> None:
        normalized = _normalize(message)

        reservation_id_match = RESERVATION_ID_PATTERN.search(message)
        if reservation_id_match:
            self.state.reservation_id = reservation_id_match.group(0)

        reservation_code_match = RESERVATION_CODE_PATTERN.search(message)
        if reservation_code_match:
            self.state.reservation_code = reservation_code_match.group(0)

        iso_match = ISO_DATE_PATTERN.search(message)
        if iso_match and _is_valid_iso_date(iso_match.group(1)):
            self.state.requested_date = iso_match.group(1)

        latam_match = LATAM_DATE_PATTERN.search(message)
        if latam_match and not self.state.requested_date:
            day, month, year = latam_match.groups()
            maybe_date = _to_iso_date(day, month, year)
            if maybe_date:
                self.state.requested_date = maybe_date

        participant_match = PARTICIPANT_PATTERN.search(message)
        if participant_match:
            self.state.participant_count = int(participant_match.group(1))

        email_match = EMAIL_PATTERN.search(message)
        if email_match:
            self.state.holder_email = email_match.group(0)

        phone_match = PHONE_PATTERN.search(message)
        if phone_match:
            self.state.holder_phone = re.sub(r"\s+", "", phone_match.group(0))

        if "soy " in normalized and self.state.holder_name is None:
            after = normalized.split("soy ", maxsplit=1)[1].strip()
            if after:
                self.state.holder_name = after[:80].title()

    def _log_turn(self, user_text: str, intent: str, response: str, trace: TraceContext) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "intent": intent,
            "source": trace.source,
            "user_text": user_text,
            "tool_calls": trace.tool_calls,
            "response": response,
        }
        self.trace_logger.append(entry)


def detect_intent(message: str) -> tuple[str, bool]:
    text = _normalize(message)
    matches: list[str] = []

    if any(token in text for token in ("asesor", "humano", "persona", "operador")):
        matches.append("human_handoff")
    if any(token in text for token in ("confirmar", "confirma", "confirmame")):
        matches.append("reservation_confirm")
    if any(token in text for token in ("comprobante", "transferencia", "pague", "pago enviado")):
        matches.append("payment_proof_received")
    if any(token in text for token in ("participante", "datos participante", "registro participante")):
        matches.append("participant_data_request")
    if any(token in text for token in ("estado", "como va", "mi reserva", "reserva")) and (
        "id" in text or "res-" in text
    ):
        matches.append("reservation_status_check")
    if any(token in text for token in ("disponibilidad", "cupos", "cupo", "hay para", "agenda")):
        matches.append("availability_check")
    if any(token in text for token in ("cotizacion", "cotizar", "precio", "cuanto cuesta", "valor")):
        matches.append("quote_request")
    if any(token in text for token in ("reservar", "reserva", "agendar", "separar")):
        matches.append("reservation_create")
    if any(token in text for token in ("politica", "reembolso", "cancelacion", "terminos", "reglas")):
        matches.append("faq_policy")
    if any(token in text for token in ("experiencia", "recomendacion", "recorrido", "actividad")):
        matches.append("faq_experience")

    if not matches:
        return "unknown", True

    priority = [
        "human_handoff",
        "reservation_confirm",
        "payment_proof_received",
        "participant_data_request",
        "reservation_status_check",
        "availability_check",
        "quote_request",
        "reservation_create",
        "faq_policy",
        "faq_experience",
    ]
    for intent in priority:
        if intent in matches:
            return intent, len(set(matches)) > 1
    return matches[0], len(set(matches)) > 1


def _filter_available_schedules(
    schedules: list[dict[str, Any]],
    requested_date: str | None,
    participant_count: int | None,
) -> list[dict[str, Any]]:
    if not requested_date or not participant_count:
        return []

    available = []
    for item in schedules:
        if str(item.get("date")) != requested_date:
            continue
        if str(item.get("status")) != "open":
            continue
        if bool(item.get("custom_request_only", False)):
            continue
        if int(item.get("available_slots", 0)) < participant_count:
            continue
        available.append(item)
    return available


def _resolve_experience_id(message: str, experiences: list[dict[str, Any]]) -> str | None:
    lower = _normalize(message)
    candidates: list[str] = []

    for item in experiences:
        experience_id = item.get("id")
        name = _normalize(str(item.get("name", "")))
        slug = _normalize(str(item.get("slug", "")))
        if not experience_id:
            continue
        if name and name in lower:
            candidates.append(str(experience_id))
            continue
        if slug and slug in lower:
            candidates.append(str(experience_id))

    unique_candidates = list(dict.fromkeys(candidates))
    if len(unique_candidates) == 1:
        return unique_candidates[0]

    direct_id = RESERVATION_ID_PATTERN.search(message)
    if direct_id:
        return direct_id.group(0)

    return None


def _missing_participant_fields(payload: dict[str, Any]) -> list[str]:
    required = {
        "first_name",
        "last_name",
        "birth_date",
        "document_type",
        "document_number",
        "phone",
        "country",
        "city",
        "height_cm",
        "weight_kg",
        "experience_level",
        "emergency_contact",
        "accepted_data_processing",
    }
    return sorted(field for field in required if field not in payload)


def _validate_payment_proof_payload(payload: dict[str, Any]) -> None:
    required = {"filename", "content_type", "size_bytes", "sha256", "content_base64"}
    missing = sorted(field for field in required if field not in payload)
    if missing:
        raise BackendApiError(400, f"Faltan campos del comprobante: {', '.join(missing)}")


def _safe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _extract_backend_error_message(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    if "message" in payload and isinstance(payload["message"], str):
        return payload["message"]
    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str):
            return message
    return None


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]{3,}", _normalize(text))
    return {token for token in tokens if token not in RAG_STOPWORDS}


def _normalize(value: str) -> str:
    normalized = value.lower().strip()
    return (
        normalized.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )


def _trim_for_whatsapp(text: str, max_chars: int = 320) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 3].rstrip() + "..."


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


def _is_valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _to_iso_date(day: str, month: str, year: str) -> str | None:
    try:
        parsed = date(int(year), int(month), int(day))
    except ValueError:
        return None
    return parsed.isoformat()


def _default_rag_sources(script_path: Path) -> list[Path]:
    repo_root = script_path.resolve().parents[3]
    return [
        repo_root / "README.md",
        repo_root / "docs" / "architecture" / "api.md",
        repo_root / "docs" / "architecture" / "api-endpoints.md",
        repo_root / "docs" / "setup" / "api.md",
        repo_root / "apps" / "api" / "README.md",
    ]


def build_agent_from_env() -> WhatsAppOperationalAgent:
    script_path = Path(__file__)
    env_file = Path(os.environ.get("LJ_ENV_FILE", script_path.parent / ".env"))
    load_env_file(env_file)

    api_base_url = os.environ.get("LJ_API_BASE_URL", "http://127.0.0.1:8000/api/v1")
    email = os.environ.get("LJ_AGENT_EMAIL", "")
    password = os.environ.get("LJ_AGENT_PASSWORD", "")
    trace_path = Path(os.environ.get("LJ_TRACE_FILE", script_path.parent / "conversation_trace.jsonl"))
    llm_enabled = _env_bool("LJ_LLM_ENABLED", default=False)
    llm_base_url = os.environ.get("LJ_LLM_BASE_URL", "http://127.0.0.1:1234/v1")
    llm_model = os.environ.get("LJ_LLM_MODEL", "gemma-4-27b-it")
    llm_api_key = os.environ.get("LJ_LLM_API_KEY")
    llm_timeout_seconds = _env_int("LJ_LLM_TIMEOUT_SECONDS", default=600)
    llm_circuit_breaker_threshold = _env_int("LJ_LLM_CIRCUIT_BREAKER_THRESHOLD", default=3)

    if not email or not password:
        raise RuntimeError(
            "Faltan credenciales. Define LJ_AGENT_EMAIL y LJ_AGENT_PASSWORD para autenticar tools."
        )

    custom_sources = os.environ.get("LJ_RAG_SOURCES")
    if custom_sources:
        rag_sources = [Path(item.strip()) for item in custom_sources.split(";") if item.strip()]
    else:
        rag_sources = _default_rag_sources(script_path)

    tools_client = BackendToolsClient(
        base_url=api_base_url,
        email=email,
        password=password,
    )
    retriever = LocalRagRetriever(rag_sources)
    rag_answerer: RagAnswerer | None = None
    if llm_enabled:
        rag_answerer = GemmaRagGenerator(
            retriever=retriever,
            llm_client=OpenAICompatibleChatClient(
                base_url=llm_base_url,
                model=llm_model,
                api_key=llm_api_key,
                timeout_seconds=llm_timeout_seconds,
            ),
            circuit_breaker_threshold=llm_circuit_breaker_threshold,
        )
    logger = TraceLogger(trace_path)
    return WhatsAppOperationalAgent(
        tools_client=tools_client,
        rag_retriever=retriever,
        trace_logger=logger,
        rag_answerer=rag_answerer,
    )


def _run_cli() -> int:
    parser = argparse.ArgumentParser(description="WhatsApp operational agent for La Juana")
    parser.add_argument(
        "--message",
        default="",
        help="If provided, processes one message and exits.",
    )
    args = parser.parse_args()

    try:
        agent = build_agent_from_env()
    except RuntimeError as exc:
        print(str(exc))
        return 1

    if args.message:
        print(agent.handle_message(args.message))
        return 0

    print("Agente WhatsApp operativo listo. Escribe 'salir' para terminar.")
    while True:
        user_text = input("Usuario: ").strip()
        if not user_text:
            continue
        if _normalize(user_text) in {"salir", "exit", "quit"}:
            break
        print("Agente:", agent.handle_message(user_text))
    return 0


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = int(value.strip())
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def load_env_file(file_path: Path, *, override: bool = False) -> None:
    if not file_path.exists() or not file_path.is_file():
        return
    for raw_line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(_run_cli())