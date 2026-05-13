from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

LOGGER_NAME = "lajuana.assistant"


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

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    log_format = os.getenv("LOG_FORMAT", "json").lower()

    if log_format == "console":
        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
            )
        )
    else:
        handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)
    return logger


def reconfigure_logger() -> None:
    configure_logger()


logger = configure_logger()
