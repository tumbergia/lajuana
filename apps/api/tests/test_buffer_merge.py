"""Tests para el merge de buffers pendientes del mismo conversation_id.

Caso de uso: el bot tarda varios segundos/minutos en responder. Mientras
tanto el usuario envía más mensajes (ej. comprobante, código de reserva).
El scheduler debe unir todos los buffers pendientes en un solo turno para
que el bot tenga el contexto completo.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


class _MockBuffer:
    """Mock minimal de MessageBufferDocument para los tests de merge."""

    def __init__(
        self,
        *,
        buffer_id: str,
        conversation_id: str,
        message_ids: list[str],
        first_message_at: datetime,
        last_message_at: datetime,
        status: str = "scheduled",
        version: int = 1,
    ) -> None:
        self.buffer_id = buffer_id
        self.conversation_id = conversation_id
        self.message_ids = list(message_ids)
        self.first_message_at = first_message_at
        self.last_message_at = last_message_at
        self.status = status
        self.version = version
        self.saved = False
        self.scheduled_for = None

    async def save(self) -> None:
        self.saved = True


# ── Merge logic ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_merge_returns_only_primary_when_no_others_pending() -> None:
    """Sin otros buffers pendientes, el merge devuelve solo el primario."""
    from app.conversations.services.message_buffer_service import MessageBufferService

    service = MessageBufferService()
    primary = _MockBuffer(
        buffer_id="b1",
        conversation_id="conv-1",
        message_ids=["m1"],
        first_message_at=datetime(2026, 1, 1, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    # Mock find que devuelve lista vacía
    mock_find = MagicMock()
    mock_find.sort = MagicMock(return_value=mock_find)
    mock_find.to_list = AsyncMock(return_value=[])

    from app.conversations.documents import MessageBufferDocument

    original_find = MessageBufferDocument.find
    MessageBufferDocument.find = MagicMock(return_value=mock_find)
    try:
        result = await service.merge_pending_buffers(primary=primary)
        assert result == [primary]
        assert primary.saved is False
    finally:
        MessageBufferDocument.find = original_find


@pytest.mark.asyncio
async def test_merge_consolidates_message_ids_from_other_buffers() -> None:
    """El merge añade los message_ids de los buffers secundarios al primario."""
    from app.conversations.services.message_buffer_service import MessageBufferService

    service = MessageBufferService()
    primary = _MockBuffer(
        buffer_id="b1",
        conversation_id="conv-1",
        message_ids=["m1", "m2"],
        first_message_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
    )
    other1 = _MockBuffer(
        buffer_id="b2",
        conversation_id="conv-1",
        message_ids=["m3", "m4"],
        first_message_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=UTC),
    )
    other2 = _MockBuffer(
        buffer_id="b3",
        conversation_id="conv-1",
        message_ids=["m5"],
        first_message_at=datetime(2026, 1, 1, 10, 2, 0, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, 10, 3, 0, tzinfo=UTC),
    )

    mock_find = MagicMock()
    mock_find.sort = MagicMock(return_value=mock_find)
    mock_find.to_list = AsyncMock(return_value=[other1, other2])

    from app.conversations.documents import MessageBufferDocument
    from app.conversations.services import message_buffer_service as mbs

    original_find = MessageBufferDocument.find
    original_collection = mbs.MessageBufferDocument.get_motor_collection

    MessageBufferDocument.find = MagicMock(return_value=mock_find)
    mbs.MessageBufferDocument.get_motor_collection = MagicMock(
        return_value=MagicMock(
            find_one_and_update=AsyncMock(return_value=None)
        )
    )

    try:
        result = await service.merge_pending_buffers(primary=primary)
        # El primario contiene ahora todos los message_ids
        assert primary.message_ids == ["m1", "m2", "m3", "m4", "m5"]
        # Devuelve [primary, other1, other2]
        assert result == [primary, other1, other2]
        # El primario se guardó
        assert primary.saved is True
        # El primario tiene la versión incrementada
        assert primary.version == 2
        # El primario tiene el last_message_at del más reciente
        assert primary.last_message_at == other2.last_message_at
    finally:
        MessageBufferDocument.find = original_find
        mbs.MessageBufferDocument.get_motor_collection = original_collection


@pytest.mark.asyncio
async def test_merge_deduplicates_message_ids() -> None:
    """Si un message_id ya está en el primario, no se duplica."""
    from app.conversations.services.message_buffer_service import MessageBufferService

    service = MessageBufferService()
    primary = _MockBuffer(
        buffer_id="b1",
        conversation_id="conv-1",
        message_ids=["m1", "m2"],
        first_message_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
    )
    other = _MockBuffer(
        buffer_id="b2",
        conversation_id="conv-1",
        # m2 ya está en el primario
        message_ids=["m2", "m3"],
        first_message_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, 10, 1, 0, tzinfo=UTC),
    )

    mock_find = MagicMock()
    mock_find.sort = MagicMock(return_value=mock_find)
    mock_find.to_list = AsyncMock(return_value=[other])

    from app.conversations.documents import MessageBufferDocument
    from app.conversations.services import message_buffer_service as mbs

    original_find = MessageBufferDocument.find
    original_collection = mbs.MessageBufferDocument.get_motor_collection

    MessageBufferDocument.find = MagicMock(return_value=mock_find)
    mbs.MessageBufferDocument.get_motor_collection = MagicMock(
        return_value=MagicMock(
            find_one_and_update=AsyncMock(return_value=None)
        )
    )

    try:
        await service.merge_pending_buffers(primary=primary)
        # m2 NO se duplica
        assert primary.message_ids == ["m1", "m2", "m3"]
    finally:
        MessageBufferDocument.find = original_find
        mbs.MessageBufferDocument.get_motor_collection = original_collection


@pytest.mark.asyncio
async def test_merge_excludes_buffers_from_other_conversations() -> None:
    """El merge solo une buffers del MISMO conversation_id."""
    from app.conversations.services.message_buffer_service import MessageBufferService

    service = MessageBufferService()
    primary = _MockBuffer(
        buffer_id="b1",
        conversation_id="conv-1",
        message_ids=["m1"],
        first_message_at=datetime(2026, 1, 1, tzinfo=UTC),
        last_message_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    # La query del find ya filtra por conversation_id. Simulamos que
    # devuelve lista vacía.
    mock_find = MagicMock()
    mock_find.sort = MagicMock(return_value=mock_find)
    mock_find.to_list = AsyncMock(return_value=[])

    from app.conversations.documents import MessageBufferDocument

    original_find = MessageBufferDocument.find
    MessageBufferDocument.find = MagicMock(return_value=mock_find)

    try:
        # Verificamos que el filtro del find incluye el conversation_id
        MessageBufferDocument.find.assert_not_called()
        result = await service.merge_pending_buffers(primary=primary)
        # El find fue llamado con el filtro correcto
        find_call_args = MessageBufferDocument.find.call_args
        assert find_call_args is not None
        filter_arg = find_call_args[0][0]
        assert filter_arg["conversation_id"] == "conv-1"
        assert filter_arg["status"] == "scheduled"
        assert filter_arg["buffer_id"] == {"$ne": "b1"}
        assert result == [primary]
    finally:
        MessageBufferDocument.find = original_find
