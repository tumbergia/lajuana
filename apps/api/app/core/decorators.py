"""Lightweight decorators for cross-cutting concerns: error logging, timing."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def log_error(
    logger: logging.Logger,
    reraise: bool = False,
    message: str | None = None,
) -> Callable[[F], F]:
    """Log exception with traceback. Optionally re-raise.

    Usage::

        logger = logging.getLogger(__name__)

        @log_error(logger, reraise=False, message="Failed to send notification")
        async def notify():
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    "%s | func=%s | error=%s",
                    message or "Unhandled error",
                    func.__name__,
                    e,
                    exc_info=True,
                )
                if reraise:
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    "%s | func=%s | error=%s",
                    message or "Unhandled error",
                    func.__name__,
                    e,
                    exc_info=True,
                )
                if reraise:
                    raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]
    return decorator
