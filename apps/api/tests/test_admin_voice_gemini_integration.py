"""Integración del asistente de voz admin contra Gemini vía HTTP /admin/ask.

Misma ruta que el móvil (`VoiceAssistantApiClient` → POST /api/v1/admin/ask).
No escribe en Mongo de producción: sesión, turns y tools van en memoria.

Correr (desde apps/api, con red):

    .venv/bin/pytest --noconftest tests/test_admin_voice_gemini_integration.py -s --tb=short
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

os.environ.setdefault("APP_SKIP_DB_INIT", "true")
sys.modules.setdefault("faster_whisper", MagicMock())

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.assistant.intent_router import detect_and_build_plan
from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.ai.assistant.planner import GeminiPlanner, normalize_admin_llm_plan
from app.ai.providers.gemini_provider import (
    GeminiModelUnavailable,
    GeminiProvider,
    GeminiProviderError,
    GeminiResourceExhausted,
)
from app.core.config import settings
from app.schemas.ask import AskResponse
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs


pytestmark = pytest.mark.integration

CATALOG: list[dict[str, Any]] = []

# Frases que el regex admin no cubre: si el router las mata, Gemini no entra.
GEMINI_NL_CASES: list[tuple[str, str, set[str]]] = [
    (
        "ándale, sácame el personal que tenemos en la plataforma",
        "listar usuarios (paráfrasis)",
        {"admin_list_users"},
    ),
    (
        "quiénes están dados de alta como guías o admins",
        "listar usuarios (roles)",
        {"admin_list_users"},
    ),
    (
        "pásame el catálogo de planes que vendemos",
        "listar experiencias (paráfrasis)",
        {"admin_list_experiences_admin"},
    ),
    (
        "necesito meter a Camila Restrepo al equipo, correo camila.int@lajuana.co",
        "crear usuario completo",
        {"admin_create_user"},
    ),
    (
        "pon en marcha un plan nuevo que se llame Cascada Escondida",
        "crear experiencia incompleta",
        {"admin_create_experience"},
    ),
    (
        "hay un aliado nuevo, Finca La Esperanza, de hospedaje",
        "crear proveedor",
        {"admin_create_provider"},
    ),
    (
        "entra Trueno como mula al inventario",
        "crear equino",
        {"admin_create_equine"},
    ),
    (
        "este ehh este como que hay que dar de alta una persona, Camila Restrepo",
        "crear usuario con fillers STT",
        {"admin_create_user"},
    ),
    (
        "pásame el inventario de mulas que hay en finca",
        "listar equinos (paráfrasis)",
        {"admin_list_equines"},
    ),
    (
        "pásame el inventario de monturas de la bodega",
        "listar sillas (paráfrasis)",
        {"admin_list_saddles"},
    ),
    (
        "cómo va el negocio este mes, cuánta plata entró",
        "reporte de ventas (paráfrasis)",
        {"admin_get_sales_summary"},
    ),
    (
        "cómo nos encuentran la gente, facebook o boca a boca",
        "rendimiento por canal (paráfrasis)",
        {"admin_get_channel_performance"},
    ),
    (
        "está lleno el cupo de las salidas próximas",
        "ocupación (paráfrasis)",
        {"admin_get_occupancy_report"},
    ),
    (
        "necesito el expediente de aquella salida, me falta el código",
        "detalle de reserva incompleto",
        {"admin_get_reservation_detail", "admin_list_reservations"},
    ),
    (
        "hay que dar luz verde a un comprobante que llegó",
        "aprobar pago incompleto",
        {"admin_approve_payment", "admin_get_payment_proof"},
    ),
    (
        "mete una montura nueva al inventario",
        "crear silla incompleta",
        {"admin_create_saddle"},
    ),
    (
        "necesito las reglas de anticipación y si piden comprobante",
        "config / reglas de reserva",
        {"admin_get_system_config", "admin_update_reservation_rules", "admin_get_payment_instructions"},
    ),
    (
        "anótale a Trueno que ya lo herraron ayer",
        "crear evento equino incompleto",
        {"admin_create_equine_event", "admin_add_equine_health_event", "admin_update_equine"},
    ),
    (
        "ayúdame a armar quién sale con qué mula mañana",
        "tablero de asignación (paráfrasis)",
        {"admin_get_assignment_board", "admin_list_reservations", "admin_list_equines"},
    ),
]


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == "GEMINI_API_KEY" and value and not settings.gemini_api_key:
            settings.gemini_api_key = value
        elif key == "GEMINI_API_KEY_2" and value and not settings.gemini_api_key_2:
            settings.gemini_api_key_2 = value
        elif key == "GEMINI_API_KEY_3" and value and not settings.gemini_api_key_3:
            settings.gemini_api_key_3 = value
        elif key == "LLM_PROVIDER" and value:
            settings.llm_provider = value


_load_env_file()


def _gemini_configured() -> bool:
    return bool((settings.gemini_api_key or "").strip())


requires_gemini = pytest.mark.skipif(
    not _gemini_configured(),
    reason="GEMINI_API_KEY no configurada",
)


def _record(entrada: str, salida: dict[str, Any], nota: str = "") -> None:
    CATALOG.append({"entrada": entrada, "salida": salida, "nota": nota})


def _outage_text(text: str) -> bool:
    lowered = text.lower()
    return any(
        token in lowered
        for token in (
            "servicio de ia sobrepasado",
            "modelo no disponible",
            "error temporal en mi sistema",
        )
    )


def _skip_if_outage(response: AskResponse | AssistantPlan) -> None:
    text = getattr(response, "response", None) or getattr(response, "audit_summary", "") or ""
    if _outage_text(str(text)):
        pytest.skip(f"Gemini no disponible: {text}")


async def _plan_or_skip(planner: GeminiPlanner, **kwargs: Any) -> AssistantPlan:
    try:
        return await planner.plan(**kwargs)
    except (GeminiResourceExhausted, GeminiModelUnavailable, GeminiProviderError) as exc:
        pytest.skip(f"Gemini no disponible: {exc}")


class MemoryTurn:
    store: list[MemoryTurn] = []

    def __init__(self, **kwargs: Any) -> None:
        self.trace_id = kwargs.get("trace_id") or str(uuid4())
        self.channel = kwargs.get("channel", "admin_api")
        self.conversation_id = kwargs.get("conversation_id")
        self.user_message = kwargs.get("user_message")
        self.from_phone = kwargs.get("from_phone")
        self.planner_output = kwargs.get("planner_output") or {}
        self.tool_output = kwargs.get("tool_output") or {}
        self.response_text = kwargs.get("response_text")
        self.status = kwargs.get("status", "received")
        self.error_code = kwargs.get("error_code")
        self.created_at = datetime.now(UTC)
        self.responded_at = kwargs.get("responded_at")

    async def save(self) -> None:
        if self not in MemoryTurn.store:
            MemoryTurn.store.append(self)

    async def insert(self) -> MemoryTurn:
        await self.save()
        return self

    @classmethod
    def find(cls, query: dict[str, Any], *args: Any, **kwargs: Any) -> SimpleNamespace:
        conversation_id = query.get("conversation_id")
        statuses = (query.get("status") or {}).get("$in")
        matched = [
            doc
            for doc in cls.store
            if doc.conversation_id == conversation_id
            and (not statuses or doc.status in statuses)
        ]
        matched.sort(key=lambda doc: doc.created_at, reverse=True)

        class _Query:
            def sort(self, _field: str) -> _Query:
                return self

            def limit(self, n: int) -> _Query:
                self._limit = n
                return self

            async def to_list(self) -> list[MemoryTurn]:
                return matched[: getattr(self, "_limit", 8)]

        return _Query()


class FakeLog:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def insert(self) -> FakeLog:
        return self


def _build_session(**overrides: Any) -> Any:
    async def noop_save() -> None:
        pass

    data = {
        "id": "ses-gemini",
        "channel": "admin_api",
        "conversation_key": "gemini-voice-1",
        "status": "active",
        "slot_values": {},
        "turn_count": 0,
        "pending_fields": [],
        "last_intent": None,
        "last_trace_id": None,
        "updated_at": None,
        "language": "es",
        "language_override": None,
        "language_streak": 0,
        "language_streak_lang": None,
        "pending_media_proof": None,
        "from_phone": "admin-integration",
        "conversation_id": None,
        "save": noop_save,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class SpyPlanner:
    def __init__(self) -> None:
        self._inner = GeminiPlanner()
        self.calls = 0

    async def plan(self, **kwargs: Any) -> AssistantPlan:
        self.calls += 1
        return await self._inner.plan(**kwargs)

    @property
    def last_token_usage(self) -> dict[str, int] | None:
        return self._inner.last_token_usage


def _args_blob(plan: AssistantPlan) -> str:
    dumped = plan.arguments.model_dump(exclude_none=True) if plan.arguments else {}
    return str(dumped).lower()


ADMIN_ASK_PATH = "/api/v1/admin/ask"


@pytest.fixture
async def live_stack(monkeypatch: pytest.MonkeyPatch) -> Any:
    MemoryTurn.store = []
    sessions: dict[str, Any] = {}
    registry_calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_load(
        self: AssistantOrchestrator,
        *,
        channel: str,
        conversation_key: str,
        from_phone: str | None,
        conversation_id: str | None,
        trace_id: str,
    ) -> Any:
        if conversation_key not in sessions:
            sessions[conversation_key] = _build_session(
                channel=channel,
                conversation_key=conversation_key,
                from_phone=from_phone,
                conversation_id=conversation_id,
                last_trace_id=trace_id,
            )
        return sessions[conversation_key]

    async def fake_registry_call(tool_name: str, /, **kwargs: Any) -> dict[str, Any]:
        registry_calls.append((tool_name, kwargs))
        if tool_name == "admin_list_users":
            return {
                "users": [
                    {
                        "user_id": "u1",
                        "full_name": "Admin Demo",
                        "email": "admin@lajuana.co",
                        "role": "admin",
                        "is_active": True,
                    }
                ],
                "total": 1,
                "message": "Hay 1 usuario activo: Admin Demo.",
            }
        if tool_name == "admin_list_experiences_admin":
            return {
                "experiences": [{"name": "Bosque nublado", "slug": "bosque-nublado"}],
                "total": 1,
                "message": "Hay 1 experiencia: Bosque nublado.",
            }
        if tool_name.startswith("admin_create_"):
            return {
                "created": True,
                "message": f"{tool_name} ejecutado en modo integración (stub).",
            }
        return {"ok": True, "message": f"{tool_name} ok (stub)."}

    async def live_provider() -> GeminiProvider:
        return GeminiProvider()

    async def gate_allowed(*_args: Any, **_kwargs: Any) -> Any:
        return SimpleNamespace(allowed=True, reason="allowed")

    planner = SpyPlanner()

    monkeypatch.setattr(AssistantOrchestrator, "_load_or_create_session", fake_load)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", MemoryTurn)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", FakeLog)
    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)
    monkeypatch.setattr("app.ai.assistant.planner.get_llm_provider", live_provider)
    monkeypatch.setattr("app.ai.assistant.response_composer.get_llm_provider", live_provider)
    monkeypatch.setattr("app.api.endpoints.admin_ask.AssistantGate.evaluate", gate_allowed)
    monkeypatch.setattr(
        "app.api.endpoints.admin_ask.AssistantOrchestrator",
        lambda: AssistantOrchestrator(planner=planner),
    )

    from app.api.deps import get_current_user
    from app.common.enums import UserRole
    from app.main import app

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id="admin-int",
        role=UserRole.ADMIN,
        is_active=True,
    )
    client = AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    )

    async def ask(message: str, conversation_id: str | None = None) -> AskResponse:
        payload: dict[str, Any] = {"message": message}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        http_response = await client.post(ADMIN_ASK_PATH, json=payload)
        if http_response.status_code != 200:
            pytest.fail(f"{ADMIN_ASK_PATH} HTTP {http_response.status_code}: {http_response.text}")
        return AskResponse.model_validate(http_response.json())

    try:
        yield SimpleNamespace(
            ask=ask,
            sessions=sessions,
            registry_calls=registry_calls,
            planner=planner,
            path=ADMIN_ASK_PATH,
        )
    finally:
        await client.aclose()
        app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def _print_catalog() -> Any:
    yield
    if not CATALOG:
        return
    print("\n\n===== CATÁLOGO INTEGRACIÓN GEMINI (entrada → salida) =====")
    for index, row in enumerate(CATALOG, start=1):
        salida = row["salida"]
        print(f"\n{index}. {row.get('nota') or 'caso'}")
        print(f"   ENTRADA: {row['entrada']}")
        print(f"   SALIDA:  {salida}")


def _stub_plan(**overrides: Any) -> AssistantPlan:
    data: dict[str, Any] = {
        "action": AssistantAction.ASK_CLARIFYING_QUESTION,
        "confidence": 0.9,
        "user_goal": "test",
        "audit_summary": "test",
    }
    data.update(overrides)
    return AssistantPlan(**data)


def test_normalize_alias_list_experiences() -> None:
    plan = _stub_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="admin_list_experiences",
    )
    normalize_admin_llm_plan(plan)
    assert plan.tool_name == "admin_list_experiences_admin"


def test_normalize_alias_reservation_rules() -> None:
    plan = _stub_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="admin_get_reservation_rules",
    )
    normalize_admin_llm_plan(plan)
    assert plan.tool_name == "admin_get_system_config"


def test_normalize_fills_create_user_when_gemini_omits_tool() -> None:
    plan = _stub_plan(
        missing_fields=["email"],
        arguments=ToolArgs(full_name="Camila Restrepo"),
    )
    normalize_admin_llm_plan(plan)
    assert plan.tool_name == "admin_create_user"


def test_normalize_fills_create_experience_when_gemini_omits_tool() -> None:
    plan = _stub_plan(missing_fields=["description", "level", "duration_hours"])
    normalize_admin_llm_plan(plan)
    assert plan.tool_name == "admin_create_experience"


def test_normalize_provider_type_hospedaje_to_lodging() -> None:
    plan = _stub_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="admin_create_provider",
        arguments=ToolArgs(name="Finca La Esperanza", provider_type="hospedaje"),
    )
    normalize_admin_llm_plan(plan)
    assert plan.arguments.type == "lodging"


async def test_admin_ask_requires_auth() -> None:
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.post(ADMIN_ASK_PATH, json={"message": "listar usuarios"})
    assert response.status_code == 401


def test_gemini_nl_utterances_miss_the_intent_router() -> None:
    for utterance, _label, _tools in GEMINI_NL_CASES:
        plan = detect_and_build_plan(user_message=utterance, channel="admin_api")
        assert plan is None, f"el router interceptó y Gemini no vería: {utterance!r} -> {plan}"


@requires_gemini
@pytest.mark.llm
@pytest.mark.parametrize(
    "utterance,label,expected_tools",
    GEMINI_NL_CASES,
    ids=[label for _utterance, label, _tools in GEMINI_NL_CASES],
)
async def test_gemini_planner_interprets_natural_admin_voice(
    utterance: str,
    label: str,
    expected_tools: set[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def live_provider() -> GeminiProvider:
        return GeminiProvider()

    monkeypatch.setattr("app.ai.assistant.planner.get_llm_provider", live_provider)
    planner = GeminiPlanner()
    plan = await _plan_or_skip(
        planner,
        user_message=utterance,
        channel="admin_api",
        conversation_id=f"gemini-planner-{uuid4()}",
        language="es",
    )
    _skip_if_outage(plan)
    blob = _args_blob(plan)
    _record(
        utterance,
        {
            "via": "GeminiPlanner",
            "action": plan.action.value,
            "tool_name": plan.tool_name,
            "arguments": plan.arguments.model_dump(exclude_none=True) if plan.arguments else {},
            "missing_fields": plan.missing_fields,
            "response": (plan.response or "")[:240],
            "tokens": planner.last_token_usage,
        },
        nota=label,
    )
    assert plan.tool_name in expected_tools, (
        f"{label}: Gemini eligió {plan.tool_name!r} action={plan.action.value} args={blob}"
    )
    assert plan.action in {
        AssistantAction.TOOL_CALL,
        AssistantAction.ASK_CLARIFYING_QUESTION,
    }
    if "camila.int@lajuana.co" in utterance:
        assert "camila.int@lajuana.co" in blob
    if "Camila Restrepo" in utterance and "camila.int@" not in utterance:
        assert "camila" in blob or plan.action == AssistantAction.ASK_CLARIFYING_QUESTION
    if "Cascada Escondida" in utterance:
        assert "cascada" in blob
    if "Finca La Esperanza" in utterance:
        assert "esperanza" in blob or "finca" in blob
        assert "lodging" in blob or "alojamiento" in blob or "hospedaje" in blob or "type" in blob
    if "entra Trueno" in utterance:
        assert "trueno" in blob


@requires_gemini
@pytest.mark.llm
async def test_gemini_list_users_then_compose_spoken_reply(
    live_stack: SimpleNamespace,
) -> None:
    utterance = "ándale, sácame el personal que tenemos en la plataforma"
    conversation_id = f"gemini-list-{uuid4()}"
    response = await live_stack.ask(utterance, conversation_id)
    _skip_if_outage(response)
    _record(
        utterance,
        {
            "via": "POST /api/v1/admin/ask",
            "action": response.action.value,
            "tool_name": response.tool_name,
            "needs_confirmation": response.needs_confirmation,
            "response": response.response[:320],
            "gemini_calls": live_stack.planner.calls,
            "tools_executed": [name for name, _args in live_stack.registry_calls],
            "tokens": live_stack.planner.last_token_usage,
        },
        nota="listar usuarios + respuesta hablada",
    )
    assert live_stack.path == ADMIN_ASK_PATH
    assert live_stack.planner.calls >= 1
    assert response.tool_name == "admin_list_users"
    assert response.action == AssistantAction.TOOL_CALL
    assert response.needs_confirmation is False
    assert live_stack.registry_calls and live_stack.registry_calls[0][0] == "admin_list_users"
    assert len(response.response.strip()) > 8
    assert "servicio de ia sobrepasado" not in response.response.lower()


@requires_gemini
@pytest.mark.llm
async def test_gemini_incomplete_user_pause_email_then_confirm(
    live_stack: SimpleNamespace,
) -> None:
    conversation_id = f"gemini-pause-{uuid4()}"
    first_msg = "necesito meter a alguien al equipo, se llama Camila Restrepo"
    first = await live_stack.ask(first_msg, conversation_id)
    _skip_if_outage(first)
    assert live_stack.planner.calls >= 1
    assert first.tool_name == "admin_create_user"
    assert first.needs_confirmation is False
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert "correo" in first.response.lower() or "email" in first.response.lower()

    gemini_after_first = live_stack.planner.calls
    second_msg = "el correo es camila.int@lajuana.co"
    second = await live_stack.ask(second_msg, conversation_id)
    _skip_if_outage(second)
    assert second.tool_name == "admin_create_user"
    assert second.needs_confirmation is True
    assert "camila" in second.response.lower() or "usuario" in second.response.lower()

    third_msg = "sí, dale"
    third = await live_stack.ask(third_msg, conversation_id)
    _skip_if_outage(third)
    executed = [name for name, _args in live_stack.registry_calls]
    _record(
        f"1) {first_msg} | 2) {second_msg} | 3) {third_msg}",
        {
            "t1": {
                "action": first.action.value,
                "tool": first.tool_name,
                "confirm": first.needs_confirmation,
                "response": first.response[:240],
                "gemini": True,
            },
            "t2": {
                "action": second.action.value,
                "tool": second.tool_name,
                "confirm": second.needs_confirmation,
                "response": second.response[:240],
                "gemini_extra": live_stack.planner.calls > gemini_after_first,
            },
            "t3": {
                "action": third.action.value,
                "tool": third.tool_name,
                "response": third.response[:240],
                "executed": executed,
            },
        },
        nota="pausa + correo + confirmar (Gemini en t1)",
    )
    assert third.action == AssistantAction.TOOL_CALL
    assert executed == ["admin_create_user"]


@requires_gemini
@pytest.mark.llm
async def test_gemini_complete_create_then_cancel(
    live_stack: SimpleNamespace,
) -> None:
    conversation_id = f"gemini-cancel-{uuid4()}"
    first_msg = "necesito meter a Camila Restrepo al equipo, correo camila.int@lajuana.co"
    first = await live_stack.ask(first_msg, conversation_id)
    _skip_if_outage(first)
    assert live_stack.planner.calls >= 1
    assert first.tool_name == "admin_create_user"

    if first.needs_confirmation:
        second = await live_stack.ask("no, mejor no", conversation_id)
        executed = [name for name, _args in live_stack.registry_calls]
        _record(
            f"1) {first_msg} | 2) no, mejor no",
            {
                "t1": {
                    "action": first.action.value,
                    "confirm": first.needs_confirmation,
                    "response": first.response[:240],
                },
                "t2": {"action": second.action.value, "response": second.response[:240]},
                "executed": executed,
            },
            nota="crear completo Gemini + cancelar",
        )
        assert second.action == AssistantAction.FINAL_RESPONSE
        assert executed == []
        return

    _record(
        first_msg,
        {
            "action": first.action.value,
            "tool": first.tool_name,
            "confirm": first.needs_confirmation,
            "missing": first.planner_output.get("missing_fields"),
            "response": first.response[:240],
        },
        nota="crear completo Gemini (pidió más datos, no llegó a confirmar)",
    )
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert first.needs_confirmation is False


@requires_gemini
@pytest.mark.llm
async def test_gemini_incomplete_then_switch_to_list(
    live_stack: SimpleNamespace,
) -> None:
    conversation_id = f"gemini-switch-{uuid4()}"
    first_msg = "este ehh este como que hay que dar de alta una persona, Camila Restrepo"
    first = await live_stack.ask(first_msg, conversation_id)
    _skip_if_outage(first)
    assert first.tool_name == "admin_create_user"
    assert first.needs_confirmation is False

    second_msg = "listar usuarios"
    second = await live_stack.ask(second_msg, conversation_id)
    _skip_if_outage(second)
    session = live_stack.sessions[conversation_id]
    _record(
        f"1) {first_msg} | 2) {second_msg}",
        {
            "t1": {
                "action": first.action.value,
                "tool": first.tool_name,
                "response": first.response[:240],
                "gemini": live_stack.planner.calls >= 1,
            },
            "t2": {
                "action": second.action.value,
                "tool": second.tool_name,
                "response": second.response[:240],
                "active_tool": session.slot_values.get("_active_tool_name"),
            },
        },
        nota="STT incompleto Gemini + cambio a listar",
    )
    assert second.tool_name == "admin_list_users"
    assert session.slot_values.get("_active_tool_name") is None


@requires_gemini
@pytest.mark.llm
async def test_gemini_experience_incomplete_asks_fields_not_confirm(
    live_stack: SimpleNamespace,
) -> None:
    utterance = "pon en marcha un plan nuevo que se llame Cascada Escondida"
    conversation_id = f"gemini-exp-{uuid4()}"
    response = await live_stack.ask(utterance, conversation_id)
    _skip_if_outage(response)
    _record(
        utterance,
        {
            "action": response.action.value,
            "tool": response.tool_name,
            "confirm": response.needs_confirmation,
            "response": response.response[:320],
            "gemini_calls": live_stack.planner.calls,
        },
        nota="experiencia incompleta (Gemini)",
    )
    assert live_stack.planner.calls >= 1
    assert response.tool_name == "admin_create_experience"
    assert response.needs_confirmation is False
    assert response.action == AssistantAction.ASK_CLARIFYING_QUESTION
    lowered = response.response.lower()
    assert any(token in lowered for token in ("descrip", "nivel", "dura", "hora", "día", "dia"))
    assert not live_stack.registry_calls


@requires_gemini
@pytest.mark.llm
async def test_gemini_experience_pause_then_continue_then_confirm(
    live_stack: SimpleNamespace,
) -> None:
    conversation_id = f"gemini-exp-pause-{uuid4()}"
    first_msg = "pon en marcha un plan nuevo que se llame Cascada Escondida"
    first = await live_stack.ask(first_msg, conversation_id)
    _skip_if_outage(first)
    assert first.tool_name == "admin_create_experience"
    assert first.needs_confirmation is False

    gemini_after_first = live_stack.planner.calls
    second_msg = "es un recorrido por bosque, nivel intermedio, dura 4 horas"
    second = await live_stack.ask(second_msg, conversation_id)
    _skip_if_outage(second)
    assert second.tool_name == "admin_create_experience"
    assert second.needs_confirmation is True

    third = await live_stack.ask("sí, dale", conversation_id)
    executed = [name for name, _args in live_stack.registry_calls]
    _record(
        f"1) {first_msg} | 2) {second_msg} | 3) sí, dale",
        {
            "t1": {
                "action": first.action.value,
                "tool": first.tool_name,
                "response": first.response[:200],
            },
            "t2": {
                "action": second.action.value,
                "confirm": second.needs_confirmation,
                "gemini_extra": live_stack.planner.calls > gemini_after_first,
            },
            "t3": {"action": third.action.value, "executed": executed},
        },
        nota="experiencia: pausa + datos + confirmar",
    )
    assert third.action == AssistantAction.TOOL_CALL
    assert executed == ["admin_create_experience"]


@requires_gemini
@pytest.mark.llm
async def test_gemini_provider_pause_type_then_confirm(
    live_stack: SimpleNamespace,
) -> None:
    conversation_id = f"gemini-prov-pause-{uuid4()}"
    first_msg = "hay un aliado nuevo, Finca La Esperanza"
    first = await live_stack.ask(first_msg, conversation_id)
    _skip_if_outage(first)
    assert first.tool_name == "admin_create_provider"
    assert first.needs_confirmation is False

    second = await live_stack.ask("alojamiento", conversation_id)
    _skip_if_outage(second)
    assert second.tool_name == "admin_create_provider"
    assert second.needs_confirmation is True

    third = await live_stack.ask("sí", conversation_id)
    executed = [name for name, _args in live_stack.registry_calls]
    _record(
        f"1) {first_msg} | 2) alojamiento | 3) sí",
        {
            "t1": {
                "action": first.action.value,
                "tool": first.tool_name,
                "response": first.response[:200],
            },
            "t2": {"confirm": second.needs_confirmation, "response": second.response[:200]},
            "t3": {"action": third.action.value, "executed": executed},
        },
        nota="proveedor: pausa + tipo + confirmar",
    )
    assert third.action == AssistantAction.TOOL_CALL
    assert executed == ["admin_create_provider"]


@requires_gemini
@pytest.mark.llm
async def test_gemini_equine_pause_name_then_confirm(
    live_stack: SimpleNamespace,
) -> None:
    conversation_id = f"gemini-eq-pause-{uuid4()}"
    first_msg = "entra una mula nueva al inventario"
    first = await live_stack.ask(first_msg, conversation_id)
    _skip_if_outage(first)
    assert first.tool_name == "admin_create_equine"
    assert first.needs_confirmation is False

    second = await live_stack.ask("Trueno", conversation_id)
    _skip_if_outage(second)
    assert second.tool_name == "admin_create_equine"
    assert second.needs_confirmation is True

    third = await live_stack.ask("sí", conversation_id)
    executed = [name for name, _args in live_stack.registry_calls]
    _record(
        f"1) {first_msg} | 2) Trueno | 3) sí",
        {
            "t1": {
                "action": first.action.value,
                "tool": first.tool_name,
                "response": first.response[:200],
            },
            "t2": {"confirm": second.needs_confirmation},
            "t3": {"action": third.action.value, "executed": executed},
        },
        nota="equino: pausa + nombre + confirmar",
    )
    assert third.action == AssistantAction.TOOL_CALL
    assert executed == ["admin_create_equine"]


@requires_gemini
@pytest.mark.llm
async def test_gemini_saddle_pause_code_then_execute(
    live_stack: SimpleNamespace,
) -> None:
    conversation_id = f"gemini-sad-pause-{uuid4()}"
    first_msg = "mete una montura nueva al inventario"
    first = await live_stack.ask(first_msg, conversation_id)
    _skip_if_outage(first)
    assert first.tool_name == "admin_create_saddle"
    assert first.needs_confirmation is False
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION

    second = await live_stack.ask("el código es SL-99", conversation_id)
    _skip_if_outage(second)
    executed = [name for name, _args in live_stack.registry_calls]
    _record(
        f"1) {first_msg} | 2) el código es SL-99",
        {
            "t1": {
                "action": first.action.value,
                "tool": first.tool_name,
                "response": first.response[:200],
            },
            "t2": {
                "action": second.action.value,
                "confirm": second.needs_confirmation,
                "executed": executed,
            },
        },
        nota="silla: pausa + código",
    )
    assert second.tool_name == "admin_create_saddle"
    assert executed == ["admin_create_saddle"] or second.needs_confirmation is True
