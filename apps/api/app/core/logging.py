from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

LOGGER_NAME = "lajuana.assistant"


class _ColoredFormatter(logging.Formatter):
    _COLORS = {
        "DEBUG": "\x1b[36m",
        "INFO": "\x1b[32m",
        "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m",
        "CRITICAL": "\x1b[35m",
    }
    _RESET = "\x1b[0m"
    _BOLD = "\x1b[1m"
    _CYAN = "\x1b[36m"
    _MAGENTA = "\x1b[35m"
    _LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    _LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(self._LOG_FORMAT, datefmt=self._LOG_DATE_FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        level_color = self._COLORS.get(record.levelname, self._RESET)
        formatted = super().format(record)
        parts = formatted.split(" ", 4)
        if len(parts) == 5:
            return (
                f"{self._CYAN}{parts[0]} {parts[1]}{self._RESET}"
                f" {self._MAGENTA}{parts[2]}{self._RESET}"
                f" {level_color}{self._BOLD}{parts[3]}{self._RESET}"
                f" {parts[4]}"
            )
        return formatted


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        for key in (
            "trace_id",
            "conversation_id",
            "channel",
            "endpoint",
            "tool_name",
            "latency_ms",
            "status",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    log_format = os.getenv("LOG_FORMAT", "console").lower()

    if log_format == "console":
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_ColoredFormatter())
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())

    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


def reconfigure_logger() -> None:
    configure_logger()


logger = configure_logger()
