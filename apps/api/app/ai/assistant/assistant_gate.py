"""Early gate that decides whether the assistant may process a turn."""

from __future__ import annotations

from dataclasses import dataclass

from app.channels.whatsapp.normalizer import normalize_phone
from app.common.enums import ReservationStatus
from app.documents.reservation_document import ACTIVE_RESERVATION_STATUSES, ReservationDocument
from app.services.config_service import ConfigService

_GATE_STATUSES = [
    ReservationStatus.CONTACT.value,
    ReservationStatus.PRE_RESERVED.value,
    *ACTIVE_RESERVATION_STATUSES,
]


class AssistantGate:
    """Blocks assistant replies when AI is off globally, for a phone, or for a reservation."""

    def __init__(self, config_service: ConfigService | None = None) -> None:
        self._config_service = config_service or ConfigService()

    async def evaluate(self, normalized_phone: str | None = None) -> AssistantGateDecision:
        ai = await self._config_service.get_ai_configuration()
        if not ai.enabled:
            return AssistantGateDecision(allowed=False, reason="global_disabled")

        if normalized_phone is None:
            return AssistantGateDecision(allowed=True, reason="allowed")

        phone = normalized_phone
        try:
            phone = normalize_phone(normalized_phone)
        except ValueError:
            return AssistantGateDecision(allowed=False, reason="invalid_phone")

        if phone in ai.muted_phones:
            return AssistantGateDecision(allowed=False, reason="muted_phone")

        if await self._has_disabled_active_reservation(phone):
            return AssistantGateDecision(allowed=False, reason="reservation_disabled")

        return AssistantGateDecision(allowed=True, reason="allowed")

    async def is_allowed(self, normalized_phone: str) -> bool:
        return (await self.evaluate(normalized_phone)).allowed

    async def _has_disabled_active_reservation(self, normalized_phone: str) -> bool:
        docs = await ReservationDocument.find(
            {
                "assistant_disabled": True,
                "status": {"$in": _GATE_STATUSES},
                "deleted_at": None,
                "holder_phone": {"$ne": None},
            }
        ).to_list()
        for doc in docs:
            raw = doc.holder_phone
            if not raw:
                continue
            try:
                if normalize_phone(raw) == normalized_phone:
                    return True
            except ValueError:
                continue
        return False


@dataclass(frozen=True)
class AssistantGateDecision:
    allowed: bool
    reason: str
