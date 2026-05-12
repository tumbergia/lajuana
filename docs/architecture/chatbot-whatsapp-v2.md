# Arquitectura del Chatbot + Webhooks (v2)

La v2 reemplazó el grafo LangGraph por un pipeline secuencial con planner → policy → tool → composer. La IA es asistiva: planifica y redacta, pero no valida negocio ni ejecuta acciones críticas.

## Capas y responsabilidades

```
app/ai/             → orquestación, planner, policy, LLM provider, tools MCP
app/api/endpoints/  → expone /ask y /whatsapp/webhook
app/channels/       → adapta payloads externos (WhatsApp) al formato interno
app/services/       → validación de negocio (reservas, pagos, disponibilidad real)
app/documents/      → persistencia (Beanie/Mongo): sesiones, turns, logs
app/schemas/        → contratos serializables entre capas
```

- `ai/` planifica y redacta respuestas, **no** confirma pagos, no modifica cupos, no crea reservas.
- `services/` es la fuente de verdad para validaciones críticas.
- `documents/` registra todo: sesiones, turns, tool calls.
- `channels/` solo traduce formatos externos (WhatsApp) al modelo interno.

## Flujo completo: webhook WhatsApp

```
Meta WhatsApp Cloud API
  │ POST /whatsapp/webhook
  ▼
whatsapp.py → receive_webhook()
  │ GET /whatsapp/webhook → verify_webhook() (challenge-response)
  ▼
normalizer.py → normalize_whatsapp_payload()
  │ raw JSON → list[WhatsAppWebhookMessage]
  ▼
orchestrator.ask(AskRequest)  ← por cada mensaje
  │
  ├─ 1. Cargar o crear ConversationSessionDocument
  │    (clave: channel + conversation_id/from_phone/trace_id)
  │
  ├─ 2. Insertar ConversationTurnDocument (user_message)
  │
  ├─ 3. GeminiPlanner.plan()
  │    → LLM produce AssistantPlan estructurado
  │    (acción, tool, argumentos, riesgo, auditoría)
  │
  ├─ 4. Merge slots: plan.arguments + session.slot_values
  │    → merge_slots() completa campos faltantes
  │    → si complete → promueve a TOOL_CALL
  │    → si faltan → ASK_CLARIFYING_QUESTION
  │
  ├─ 5. Policy: ToolPolicyEngine.validate(plan)
  │    → confianza baja, tool crítica, args faltantes → bloquea
  │    → bloqueado → responde sin ejecutar tool
  │
  ├─ 6. Ejecutar tool MCP: registry.call(name, **args)
  │    → check_experience_availability o list_experiences
  │
  ├─ 7. Componer respuesta: compose_tool_response()
  │    → "cheap": template directo
  │    → "llm": segunda llamada Gemini con tool output
  │
  ├─ 8. Persistir: turn, session, tool_call_log
  │
  └─ 9. Enviar respuesta: WhatsAppSender.send_text()
       → POST a Meta Graph API
```

El endpoint `/ask` (test/debug) sigue el mismo pipeline pero devuelve `AskResponse` como JSON, sin enviar por WhatsApp.

## Componentes

### AssistantOrchestrator (`ai/assistant/orchestrator.py`)

Coordinador central. Ejecuta el pipeline completo:

```
_load_or_create_session()
  → planner.plan()
  → slot merge
  → policy.validate()
  → registry.call()
  → compose_tool_response()
  → persistir todo
  → AskResponse
```

Mantiene trazabilidad completa: cada turno tiene `trace_id`, el plan se guarda antes de ejecutar tools, y cada tool call se loguea con input, output, status y latencia.

### GeminiPlanner (`ai/assistant/planner.py`)

Una sola llamada a Gemini con `response_model=AssistantPlan`. El prompt (`prompts/planner.py`) instruye:

- Clasificar intención en 4 acciones: `final_response`, `tool_call`, `ask_clarifying_question`, `human_handoff`
- Extraer argumentos estructurados: `experience_query`, `requested_date`, `participant_count`
- Evaluar nivel de riesgo: `low` / `medium` / `high` / `critical`
- Nunca inventar datos operativos, precios ni políticas de pago
- Auditabilidad: cada decisión incluye `audit_summary` de una línea

Temperatura: 0.1 (determinístico).

### ToolPolicyEngine (`ai/assistant/policy.py`)

Guarda rail antes de ejecutar tools. Evalúa:

| Regla | Condición | Resultado |
|---|---|---|
| Confianza baja | `< settings.assistant_min_plan_confidence` | Bloquea |
| Sin tool | `action != TOOL_CALL` | Permite (no-op) |
| Tool crítica | `confirm_reservation`, `cancel_reservation`, `mark_payment_verified`, `change_schedule_capacity`, `block_slots` | Bloquea siempre |
| Riesgo alto | `risk_level in {HIGH, CRITICAL}` | Requiere humano |
| Args faltantes | `requested_date` o `participant_count` ausentes | Bloquea + detalle |
| Tool desconocida | no está en `READ_TOOLS` ni `WRITE_TOOLS` | Bloquea |

Tools autorizadas como lectura: solo `check_experience_availability` (y por añadidura `list_experiences`).

### ResponseComposer (`ai/assistant/response_composer.py`)

Dos modos:

- **cheap** (`settings.assistant_tool_response_mode == "cheap"`): template `cheap_tool_summary()` que construye texto a partir del plan y tool output. Sin LLM, rápido y barato.
- **llm**: segunda llamada Gemini con `response_model=ToolResultResponse`, temperatura 0.4, que recibe `user_message`, `plan` y `tool_output` para redactar una respuesta natural.

### MCP Tools (`ai/mcp/`)

Registro central tipo `dict[str, Callable]` en `registry.py`. Se registran al importar `ai/mcp/__init__.py`:

```
check_experience_availability  → tools/availability.py
list_experiences              → tools/catalog.py
```

`check_experience_availability`:
1. Resuelve experiencia por ID o texto vía `ExperienceCatalogResolver`
2. Busca `ScheduleDocument` para la fecha solicitada
3. Valida: estado abierto, cupo disponible, días de antelación mínimos
4. Retorna `available`, `blocking_reasons`, capacidad, etc.
5. Loguea cada llamada en `ToolCallLogDocument`

`list_experiences`:
1. Query `ExperienceDocument.find()` con filtro opcional `is_active`
2. Retorna resumen: nombre, slug, duración, dificultad, precio desde, tags

### LLM Provider (`ai/providers/`)

Abstracción vía `factory.get_llm_provider()`. Actualmente solo `GeminiProvider`:

- SDK `google-genai` sincrónico envuelto en `asyncio.to_thread()` con timeout
- `generate_structured()`: schema JSON → response_model Pydantic
- Stripea `additionalProperties` del schema (Gemini no lo soporta)
- Timeout, error de parseo y respuesta vacía se capturan como `GeminiProviderError`

### Conversación y estado (`documents/`)

`ConversationSessionDocument` persiste por `channel + conversation_key`:

- `slot_values`: diccionario acumulado de datos del usuario (fecha, pax, experiencia)
- `pending_fields`: qué falta preguntar
- `last_intent`, `turn_count`, `status`

`ConversationTurnDocument` persiste por turno:

- `user_message`, `planner_output`, `tool_output`, `response_text`, `status`, `error_code`

`ToolCallLogDocument` persiste por tool call:

- `tool_name`, `input`, `output`, `status`, `error_code`, `latency_ms`

### Webhook WhatsApp (`channels/whatsapp/`)

`normalizer.py` transforma el payload crudo de Meta (`entry[0].changes[0].value.messages[]`) en `list[WhatsAppWebhookMessage]` con `external_message_id`, `from_phone`, `text`.

`sender.py` envía respuestas vía `POST` a `https://graph.facebook.com/v21.0/{phone_number_id}/messages` con token Bearer del settings.

## Endpoints

### `POST /api/v1/ask`

Test/debug. Recibe `AskRequest`, ejecuta pipeline completo, retorna `AskResponse` JSON.

### `GET /api/v1/whatsapp/webhook`

Verificación Meta: responde `hub.challenge` si `hub.mode == "subscribe"` y `hub.verify_token` coincide.

### `POST /api/v1/whatsapp/webhook`

Recibe mensajes entrantes, los normaliza, ejecuta orquestador por cada uno, envía respuesta por WhatsApp.

## Diagrama de capas

```
HTTP (Meta / test)
       │
       ▼
api/endpoints/       ← expone, no contiene lógica de negocio
       │
       ▼
ai/assistant/        ← planifica, policy, compone respuestas
ai/providers/        ← llama Gemini
ai/mcp/tools/        ← tools MCP (disponibilidad, catálogo)
       │
       ├──► services/       ← validación de negocio (resolvers)
       ├──► documents/      ← persistencia MongoDB (Beanie)
       └──► channels/       ← adaptación WhatsApp (normalizer, sender)
```

## Reglas

- `ai/` no ejecuta acciones críticas: solo planifica y redacta.
- `services/` valida disponibilidad real; la tool `check_experience_availability` es una consulta operativa, no una confirmación.
- Las herramientas críticas (`confirm_reservation`, etc.) están bloqueadas por `ToolPolicyEngine` y no se exponen al LLM.
- Cada turno y tool call se loguea con trazabilidad completa (`trace_id`).
- La sesión acumula slots entre turnos hasta completar los datos necesarios para una tool call.
