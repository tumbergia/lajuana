"""Integración real: POST /api/v1/admin/ask + Mongo + Gemini.

Lista usuarios de Atlas y crea uno de prueba por voz, luego lo borra.
Misma ruta que el móvil. Requiere red, GEMINI_API_KEY y MONGODB_URI.

    cd apps/api
    .venv/bin/pytest --noconftest tests/test_admin_ask_live_mongo.py -s --tb=short
"""

from __future__ import annotations

import os
import re
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

os.environ.setdefault("APP_SKIP_DB_INIT", "false")
sys.modules.setdefault("faster_whisper", MagicMock())

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.schemas.ask import AskResponse
from app.schemas.assistant_plan import AssistantAction


pytestmark = [pytest.mark.integration, pytest.mark.llm]

ADMIN_ASK_PATH = "/api/v1/admin/ask"
TEST_EMAIL_PREFIX = "gemini.integration."
_PASSWORD_RE = re.compile(r"Contraseña temporal: \S+", re.IGNORECASE)


def _gemini_ok() -> bool:
    return bool((settings.gemini_api_key or "").strip())


requires_live = pytest.mark.skipif(
    not _gemini_ok(),
    reason="GEMINI_API_KEY no configurada",
)


def _redact(text: str) -> str:
    return _PASSWORD_RE.sub("Contraseña temporal: [redactada]", text)


def _outage(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in lowered
        for token in (
            "servicio de ia sobrepasado",
            "modelo no disponible",
            "error temporal en mi sistema",
        )
    )


@pytest.fixture
async def live_admin_ask(monkeypatch: pytest.MonkeyPatch) -> Any:
    settings.app_skip_db_init = False

    from app.core.db import close_db, init_db
    from app.core.di import Container

    Container.init()
    try:
        await init_db()
    except Exception as exc:
        pytest.skip(f"Mongo no disponible: {exc}")

    async def gate_allowed(*_args: Any, **_kwargs: Any) -> Any:
        return SimpleNamespace(allowed=True, reason="allowed")

    monkeypatch.setattr("app.api.endpoints.admin_ask.AssistantGate.evaluate", gate_allowed)

    from app.api.deps import get_current_user
    from app.common.enums import UserRole
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="admin-live-int",
        role=UserRole.ADMIN,
        is_active=True,
    )
    client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        timeout=120.0,
    )

    async def ask(message: str, conversation_id: str | None = None) -> AskResponse:
        payload: dict[str, Any] = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        http_response = await client.post(ADMIN_ASK_PATH, json=payload)
        if http_response.status_code != 200:
            pytest.fail(f"{ADMIN_ASK_PATH} HTTP {http_response.status_code}: {http_response.text}")
        data = AskResponse.model_validate(http_response.json())
        if _outage(data.response):
            pytest.skip(f"Gemini no disponible: {data.response}")
        return data

    try:
        yield SimpleNamespace(ask=ask, path=ADMIN_ASK_PATH)
    finally:
        await client.aclose()
        app.dependency_overrides.clear()
        await close_db()


async def _delete_user_by_email(email: str) -> None:
    from app.documents import UserDocument

    user = await UserDocument.find_one({"email": email})
    if user is not None:
        await user.delete()


async def _purge_orphans(conversation_ids: list[str]) -> None:
    from app.documents.conversation_session_document import ConversationSessionDocument
    from app.documents.conversation_turn_document import ConversationTurnDocument

    if not conversation_ids:
        return
    await ConversationSessionDocument.find(
        {"conversation_key": {"$in": conversation_ids}}
    ).delete()
    await ConversationTurnDocument.find({"conversation_id": {"$in": conversation_ids}}).delete()


@requires_live
async def test_admin_ask_lists_real_users_from_mongo(live_admin_ask: SimpleNamespace) -> None:
    from app.documents import UserDocument

    conversation_id = f"gemini-live-list-{uuid4()}"
    db_count = await UserDocument.find_all().count()
    try:
        response = await live_admin_ask.ask(
            "ándale, sácame el personal que tenemos en la plataforma",
            conversation_id,
        )
        users = response.tool_output.get("users") or []
        total = response.tool_output.get("total")
        print(
            "\nLISTAR REAL /admin/ask\n"
            f"  DB count={db_count}\n"
            f"  tool={response.tool_name} action={response.action.value}\n"
            f"  tool_output.total={total} users={len(users)}\n"
            f"  response={response.response[:240]}"
        )
        assert live_admin_ask.path == ADMIN_ASK_PATH
        assert response.tool_name == "admin_list_users"
        assert response.action == AssistantAction.TOOL_CALL
        assert isinstance(users, list)
        assert total == len(users)
        assert total == min(db_count, 200)
        if users:
            assert users[0].get("email")
            assert users[0].get("full_name")
    finally:
        await _purge_orphans([conversation_id])


@requires_live
async def test_admin_ask_creates_real_user_then_deletes(live_admin_ask: SimpleNamespace) -> None:
    from app.documents import UserDocument

    suffix = uuid4().hex[:10]
    email = f"{TEST_EMAIL_PREFIX}{suffix}@example.com"
    full_name = "Qa Gemini Int"
    create_cid = f"gemini-live-create-{suffix}"
    list_cid = f"gemini-live-verify-{suffix}"

    await _delete_user_by_email(email)

    try:
        first = await live_admin_ask.ask(
            f"necesito meter a {full_name} al equipo, correo {email}",
            create_cid,
        )
        assert first.tool_name == "admin_create_user"

        if first.needs_confirmation:
            created = await live_admin_ask.ask("sí, dale", create_cid)
        elif first.action == AssistantAction.TOOL_CALL:
            created = first
        else:
            pytest.fail(
                f"no llegó a crear: action={first.action.value} "
                f"confirm={first.needs_confirmation} response={first.response}"
            )

        assert created.action == AssistantAction.TOOL_CALL
        assert created.tool_name == "admin_create_user"
        assert created.tool_output.get("created") is True
        assert created.tool_output.get("email") == email
        assert "creado" in created.response.lower()

        db_user = await UserDocument.find_one({"email": email})
        assert db_user is not None, "el usuario no quedó en Mongo"
        assert db_user.full_name == full_name
        assert db_user.is_active is True

        listed = await live_admin_ask.ask(
            "ándale, sácame el personal que tenemos en la plataforma",
            list_cid,
        )
        listed_emails = {
            str(item.get("email"))
            for item in (listed.tool_output.get("users") or [])
            if isinstance(item, dict)
        }
        assert email in listed_emails, f"{email} no apareció en el listado real"

        print(
            "\nCREAR REAL /admin/ask\n"
            f"  email={email}\n"
            f"  user_id={created.tool_output.get('user_id')}\n"
            f"  t1={first.action.value} confirm={first.needs_confirmation}\n"
            f"  create={_redact(created.response)[:240]}\n"
            f"  list_total={listed.tool_output.get('total')}"
        )
    finally:
        await _delete_user_by_email(email)
        leftover = await UserDocument.find_one({"email": email})
        assert leftover is None, "cleanup falló: el usuario de prueba sigue en Mongo"
        await _purge_orphans([create_cid, list_cid])
