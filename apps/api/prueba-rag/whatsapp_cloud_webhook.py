"""WhatsApp Cloud API webhook bridge for the operational agent.

Run this app with uvicorn and expose it publicly (ngrok/cloudflared) so Meta can
deliver WhatsApp events.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from datetime import UTC, datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib import error, request

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from whatsapp_operational_agent import WhatsAppOperationalAgent, build_agent_from_env, load_env_file

load_env_file(Path(os.environ.get("LJ_ENV_FILE", CURRENT_DIR / ".env")))


app = FastAPI(title="La Juana WhatsApp Webhook", version="0.1.0")
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


def _webhook_trace_path() -> Path:
    _reload_env_for_runtime()
    default_path = CURRENT_DIR / "webhook_events.jsonl"
    configured = os.environ.get("LJ_WEBHOOK_TRACE_FILE", str(default_path))
    return Path(configured)


def _append_webhook_trace(entry: dict[str, Any]) -> None:
    path = _webhook_trace_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _reload_env_for_runtime() -> None:
    env_file = Path(os.environ.get("LJ_ENV_FILE", CURRENT_DIR / ".env"))
    load_env_file(env_file, override=True)


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@dataclass
class SessionManager:
    lock: threading.Lock = field(default_factory=threading.Lock)
    sessions: dict[str, WhatsAppOperationalAgent] = field(default_factory=dict)
    user_locks: dict[str, threading.Lock] = field(default_factory=dict)

    def get_agent(self, wa_user_id: str) -> WhatsAppOperationalAgent:
        with self.lock:
            existing = self.sessions.get(wa_user_id)
            if existing is not None:
                return existing
            new_agent = build_agent_from_env()
            self.sessions[wa_user_id] = new_agent
            return new_agent

    def get_user_lock(self, wa_user_id: str) -> threading.Lock:
        with self.lock:
            user_lock = self.user_locks.get(wa_user_id)
            if user_lock is None:
                user_lock = threading.Lock()
                self.user_locks[wa_user_id] = user_lock
            return user_lock


session_manager = SessionManager()


def _send_whatsapp_text(to_number: str, text: str) -> None:
    _reload_env_for_runtime()
    phone_number_id = _required_env("WA_PHONE_NUMBER_ID")
    access_token = _required_env("WA_ACCESS_TOKEN")
    graph_version = os.environ.get("WA_GRAPH_VERSION", "v23.0")

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }
    url = f"https://graph.facebook.com/{graph_version}/{phone_number_id}/messages"

    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=20):
            logger.info("Outbound WhatsApp message sent to %s", to_number)
            return
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise HTTPException(status_code=502, detail=f"WhatsApp send error: {body[:240]}") from exc
    except error.URLError as exc:
        raise HTTPException(status_code=503, detail="Could not reach WhatsApp Graph API") from exc


def _extract_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    entries = payload.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            result.extend(messages)
    return result


def _message_cache() -> dict[str, datetime]:
    if not hasattr(_message_cache, "cache"):
        _message_cache.cache = {}
    return _message_cache.cache  # type: ignore[attr-defined]


def _is_duplicate_message(message: dict[str, Any]) -> bool:
    message_id = str(message.get("id", "")).strip()
    if not message_id:
        return False

    now = datetime.now(UTC)
    cache = _message_cache()
    expiry = now.timestamp() - 300

    stale_ids = [item_id for item_id, seen_at in cache.items() if seen_at.timestamp() < expiry]
    for stale_id in stale_ids:
        cache.pop(stale_id, None)

    if message_id in cache:
        return True

    cache[message_id] = now
    return False


def _parse_optional_payload(text: str) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
    clean = text.strip()
    if clean.startswith("/proof "):
        raw_json = clean[len("/proof ") :].strip()
        payload = json.loads(raw_json)
        return "Comprobante enviado", payload, None
    if clean.startswith("/participant "):
        raw_json = clean[len("/participant ") :].strip()
        payload = json.loads(raw_json)
        return "Registrar participante", None, payload
    return clean, None, None


@app.get("/webhook")
async def verify_webhook(request: Request) -> PlainTextResponse:
    verify_token = _required_env("WA_VERIFY_TOKEN")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token and challenge:
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request) -> JSONResponse:
    _reload_env_for_runtime()
    payload = await request.json()
    _append_webhook_trace(
        {
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "event": "webhook_received",
            "object": payload.get("object", "unknown"),
            "entries": len(payload.get("entry", [])),
        }
    )
    logger.info(
        "Webhook event received: object=%s entries=%s",
        payload.get("object", "unknown"),
        len(payload.get("entry", [])),
    )
    messages = _extract_messages(payload)
    if not messages:
        logger.info("Webhook contains no inbound messages (likely status/update event).")

    for message in messages:
        try:
            wa_user_id = str(message.get("from", "")).strip()
            if not wa_user_id:
                logger.info("Skipping message without sender id.")
                continue
            if _is_duplicate_message(message):
                logger.info("Skipping duplicate message id=%s from=%s", message.get("id", "unknown"), wa_user_id)
                continue
            msg_type = str(message.get("type", "")).strip()
            logger.info("Inbound message from=%s type=%s", wa_user_id, msg_type or "unknown")
            _append_webhook_trace(
                {
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "event": "inbound_message",
                    "from": wa_user_id,
                    "type": msg_type or "unknown",
                }
            )
            if msg_type != "text":
                logger.info("Skipping unsupported message type=%s from=%s", msg_type, wa_user_id)
                if msg_type in {"audio", "image", "video", "document", "sticker"}:
                    try:
                        _send_whatsapp_text(
                            wa_user_id,
                            "Recibi tu mensaje multimedia. Por ahora respondeme en texto y te ayudo enseguida.",
                        )
                    except Exception as send_exc:
                        logger.exception(
                            "Failed sending non-text fallback reply to %s: %s", wa_user_id, send_exc
                        )
                continue

            incoming = message.get("text", {}).get("body", "").strip()
            if not incoming:
                logger.info("Skipping empty text message from=%s", wa_user_id)
                continue

            logger.info("Inbound text from=%s body=%s", wa_user_id, incoming[:120])
            _append_webhook_trace(
                {
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "event": "inbound_text",
                    "from": wa_user_id,
                    "body": incoming[:300],
                }
            )

            agent = session_manager.get_agent(wa_user_id)
            user_lock = session_manager.get_user_lock(wa_user_id)
            with user_lock:
                try:
                    user_text, payment_payload, participant_payload = _parse_optional_payload(incoming)
                except json.JSONDecodeError:
                    logger.info("Skipping malformed JSON payload from=%s", wa_user_id)
                    continue

                reply = agent.handle_message(
                    user_text,
                    payment_proof_payload=payment_payload,
                    participant_payload=participant_payload,
                )
                if not reply:
                    logger.info("Agent produced no reply for=%s; skipping send.", wa_user_id)
                    continue

                logger.info("Agent reply for=%s body=%s", wa_user_id, reply[:160])
                _append_webhook_trace(
                    {
                        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                        "event": "agent_reply",
                        "to": wa_user_id,
                        "body": reply[:300],
                    }
                )
                try:
                    _send_whatsapp_text(wa_user_id, reply)
                except Exception as send_exc:  # pragma: no cover - defensive logging path
                    logger.exception("Failed sending WhatsApp reply to %s: %s", wa_user_id, send_exc)
        except Exception as msg_exc:  # pragma: no cover - defensive logging path
            logger.exception("Failed processing webhook message payload: %s", msg_exc)

    return JSONResponse({"ok": True})
