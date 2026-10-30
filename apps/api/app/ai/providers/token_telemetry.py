from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path

_WRITE_LOCK = threading.Lock()

# Resuelve la raíz del monorepo (cinco niveles arriba de este archivo):
# apps/api/app/ai/providers -> raíz
_TELEMETRY_PATH = Path(__file__).resolve().parents[5] / "token_telemetry.txt"


def _ensure_file() -> None:
    if not _TELEMETRY_PATH.exists():
        _TELEMETRY_PATH.write_text("", encoding="utf-8")


def log_token_usage(
    *,
    api_key_suffix: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    channel: str | None = None,
    conversation_id: str | None = None,
) -> None:
    """Registra una línea de telemetría de tokens en el archivo txt de la raíz.

    Cada llamada a Gemini genera una línea con timestamp, modelo,
    sufijo de API key, tokens y contexto de conversación.
    """
    timestamp = datetime.now(UTC).isoformat()
    line = (
        f"[{timestamp}] model={model} api_key=****{api_key_suffix} "
        f"prompt_tokens={prompt_tokens} completion_tokens={completion_tokens} "
        f"total_tokens={total_tokens}"
    )
    if channel:
        line += f" channel={channel}"
    if conversation_id:
        line += f" conversation_id={conversation_id}"
    line += "\n"

    with _WRITE_LOCK:
        _ensure_file()
        with _TELEMETRY_PATH.open("a", encoding="utf-8") as f:
            f.write(line)
