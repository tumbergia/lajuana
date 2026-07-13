"""Early gate that decides whether the WhatsApp assistant may process a turn."""

from __future__ import annotations

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
    """Blocks automated assistant replies when AI is off globally, for a phone, or for a reservation."""

    def __init__(self, config_service: ConfigService | None = None) -> None:
        self._config_service = config_service or ConfigService()

    async def is_allowed(self, normalized_phone: str) -> bool:
        ai = await self._config_service.get_ai_configuration()
        if not ai.enabled:
            return False

        phone = normalized_phone
        try:
            phone = normalize_phone(normalized_phone)
        except ValueError:
            return False

        if phone in ai.muted_phones:
            return False

        if await self._has_disabled_active_reservation(phone):
            return False

        return True

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
