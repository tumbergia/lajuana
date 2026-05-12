from __future__ import annotations

import logging
import sys


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

    def format(self, record: logging.LogRecord) -> str:
        level_color = self._COLORS.get(record.levelname, self._RESET)
        formatted = super().format(record)
        parts = formatted.split(" ", 4)
        if len(parts) == 5:
            colored = (
                f"{self._CYAN}{parts[0]} {parts[1]}{self._RESET}"
                f" {self._MAGENTA}{parts[2]}{self._RESET}"
                f" {level_color}{self._BOLD}{parts[3]}{self._RESET}"
                f" {parts[4]}"
            )
            return colored
        return formatted


_LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("lajuana.assistant")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            _ColoredFormatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)
        )
        logger.addHandler(handler)

    return logger


def reconfigure_logger() -> None:
    logger = logging.getLogger("lajuana.assistant")
    logger.setLevel(logging.INFO)
    logger.disabled = False
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        _ColoredFormatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)
    )
    logger.addHandler(handler)


logger = _setup_logger()
