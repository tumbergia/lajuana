from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.common.enums import NotificationChannel
from app.documents.notification_outbox_document import NotificationOutboxDocument


@dataclass
class SendResult:
    success: bool
    provider_message_id: str | None = None
    error_code: str | None = None
    error_detail: str | None = None


class NotificationProvider(ABC):
    channel: NotificationChannel

    @abstractmethod
    async def send(self, entry: NotificationOutboxDocument) -> SendResult: ...

    @abstractmethod
    async def validate_config(self) -> bool: ...
