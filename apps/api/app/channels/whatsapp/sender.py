from uuid import uuid4

from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.documents.conversation_turn_document import ConversationTurnDocument


class WhatsAppSender:
    def __init__(self) -> None:
        self._service = WhatsAppOutboundService()

    async def send_text(self, *, to_phone: str, text: str) -> bool:
        turn = ConversationTurnDocument(
            trace_id=str(uuid4()),
            channel="whatsapp",
            from_phone=to_phone,
            user_message="(legacy send)",
            conversation_id=f"whatsapp:{to_phone}",
        )
        await turn.insert()
        result = await self._service.send(turn=turn, to_phone=to_phone, text=text)
        return result.status == "sent"
