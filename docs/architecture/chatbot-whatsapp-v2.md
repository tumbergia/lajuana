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

- `ai/` planifica y redacta respuestas; puede ejecutar escritura limitada (`create_reservation_draft`, `attach_payment_proof_to_reservation`) pero **no** confirma pagos ni modifica cupos.
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
  ├─ 3. Pre-planner media branch (solo WhatsApp)
  │    → si llega imagen/PDF y existe una sola pre-reserva activa por teléfono:
  │      ejecuta `attach_payment_proof_to_reservation` y responde sin planner
  │    → si no hay pre-reserva activa o hay varias: responde instrucción/código y corta flujo
  │
  ├─ 4. GeminiPlanner.plan()
   │    → LLM produce AssistantPlan estructurado
   │    (acción, tool, argumentos, riesgo, auditoría)
   │
  ├─ 5. Merge slots: plan.arguments + session.slot_values
  │    → merge_slots() tool-aware por REQUIRED_FIELDS_BY_TOOL
  │    → required_fields según plan.tool_name (check_experience_availability, create_reservation_draft, suggest_alternative_dates)
  │    → si complete → promueve a TOOL_CALL
  │    → si faltan → ASK_CLARIFYING_QUESTION
  │
  ├─ 6. Policy: ToolPolicyEngine.validate(plan)
  │    → confianza baja, tool crítica, args faltantes → bloquea
  │    → bloqueado → responde sin ejecutar tool
  │
  ├─ 7. Ejecutar tool MCP: registry.call(name, **args)
  │    → check_experience_availability, list_experiences, quote_experience,
  │      list_available_schedules, suggest_alternative_dates, ...
  │
  ├─ 8. Componer respuesta: compose_tool_response()
  │    → LLM: segunda llamada Gemini con tool output (único modo)
  │
  ├─ 9. Persistir: turn, session, tool_call_log
  │
  └─ 10. Enviar respuesta: WhatsAppSender.send_text()
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
- Extraer argumentos estructurados: `experience_query`, `experience_id`, `requested_date`, `participant_count`
- Invocar `list_experiences` para consultas de catálogo ("qué ofrecen", "planes", "experiencias")
- Invocar `check_experience_availability` cuando hay fecha + participantes + experiencia
- Invocar `quote_experience` para cotizar precio según participantes
- Invocar `create_reservation_draft` requiere además `holder_name` y `holder_email` del titular
- Invocar `list_available_schedules` para consultar fechas disponibles
- Invocar `suggest_alternative_dates` cuando no hay cupo o el usuario rechaza fechas mostradas
- Evaluar nivel de riesgo: `low` / `medium` / `high` / `critical`
- Nunca inventar datos operativos, precios ni políticas de pago
- Auditabilidad: cada decisión incluye `audit_summary` de una línea

Temperatura: 0.1 (determinístico).

El planner acepta inyección del caller para testing (constructor `AssistantOrchestrator(planner=...)`).

### ToolPolicyEngine (`ai/assistant/policy.py`)

Guarda rail antes de ejecutar tools. Evalúa:

| Regla | Condición | Resultado |
|---|---|---|
| Confianza baja | `< settings.assistant_min_plan_confidence` | Bloquea |
| Sin tool | `action != TOOL_CALL` | Permite (no-op) |
| Tool crítica | `confirm_reservation`, `cancel_reservation`, `mark_payment_verified`, `change_schedule_capacity`, `block_slots` | Bloquea siempre |
| Riesgo alto | `risk_level in {HIGH, CRITICAL}` | Requiere humano |
| Args faltantes | `requested_date` o `participant_count` ausentes | Bloquea + detalle |
| Tool desconocida | no está en `READ_TOOLS` ni `WRITE_TOOLS` ni `LIMITED_WRITE_TOOLS` | Bloquea |

Tools autorizadas como lectura: `check_experience_availability`, `list_experiences`, `quote_experience`, `list_available_schedules`, `suggest_alternative_dates`, `get_experience_detail`, `get_public_business_rules`, `get_reservation_public_summary`, `get_reservation_status_by_phone`.  
Tools de escritura limitada: `request_human_review`, `create_reservation_draft`, `attach_payment_proof_to_reservation`.

### ResponseComposer (`ai/assistant/response_composer.py`)

Una sola llamada Gemini con `response_model=ToolResultResponse`, temperatura 0.6, que recibe `user_message`, `plan` y `tool_output` para redactar una respuesta natural y cálida. El prompt instruye terminar con una pregunta breve o invitación a continuar.

### MCP Tools (`ai/mcp/`)

Registro central tipo `dict[str, Callable]` en `registry.py`. Se registran al importar `ai/mcp/__init__.py`:

```
check_experience_availability  → tools/availability.py
list_experiences              → tools/catalog.py
quote_experience              → tools/quote.py
list_available_schedules      → tools/schedules.py
suggest_alternative_dates     → tools/schedules.py
create_reservation_draft      → tools/reservation_draft.py
attach_payment_proof_to_reservation → tools/reservation_draft.py
get_reservation_public_summary→ tools/reservation_draft.py
get_reservation_status_by_phone→ tools/reservation_draft.py
get_experience_detail         → tools/__init__.py (stub, planned)
get_public_business_rules     → tools/__init__.py (stub, planned)
request_human_review          → tools/__init__.py (stub, planned)
```

`check_experience_availability`:
1. Resuelve experiencia por ID o texto vía `ExperienceCatalogResolver`
2. Busca `ScheduleDocument` para la fecha solicitada
3. Valida: estado abierto, cupo disponible, días de antelación mínimos (`min_notice` se evalúa solo si no hay schedule)
4. Retorna `available`, `blocking_reasons`, capacidad, etc.
5. Loguea cada llamada en `ToolCallLogDocument`

`list_available_schedules`:
1. Resuelve experiencia por ID o texto
2. Busca `ScheduleDocument` en rango de fechas (60 días, con filtros is_active + OPEN)
3. Filtra por cupo si `participant_count` está presente
4. Retorna listado de fechas con capacidad disponible

`suggest_alternative_dates`:
1. Resuelve experiencia por ID o texto
2. Busca schedules alternativos alrededor de la fecha (15 días antes, 30 después)
3. Excluye fechas ya mostradas
4. Retorna alternativas ordenadas por fecha

`ExperienceCatalogResolver` soporta:
- Búsqueda por slug exacto, nombre, alias o ID de MongoDB
- Normalización de acentos ("cafe" → "café", "dia" → "día")
- Token overlap con longitud mínima 3 caracteres
- Búsqueda en `tags` además de name, slug, description, aliases
- Inyección de datos mock para testing unitario
- Retorna `FOUND`, `AMBIGUOUS` (múltiples candidatos) o `NOT_FOUND`

`list_experiences`:
1. Query `ExperienceDocument.find()` con filtro opcional `is_active`
2. Retorna resumen: nombre, slug, duración, dificultad, precio desde, tags
3. Seed incluye aliases expandidos (`un día`, `día completo`, `cafe`, `café`) y tags de búsqueda

`quote_experience`:
1. Resuelve experiencia por ID o texto
2. Calcula precio según `participant_count` usando tarifas configuradas (tramos por rango de participantes)
3. Retorna precio unitario, subtotal, tramo aplicado

Tools activas de reserva/pago (runtime):
- `create_reservation_draft` crea una reserva en estado no confirmado con trazabilidad de origen; no confirma pago ni reserva.
- `create_reservation_draft` devuelve instrucciones de pago desde configuración (`ConfigService.get_payment_instructions()`).
- `attach_payment_proof_to_reservation` asocia comprobantes enviados por WhatsApp y los deja en estado `under_review`/`duplicate`; no valida pago.
- `get_reservation_public_summary` devuelve un resumen seguro para el cliente por codigo de reserva + `holder_phone` (doble validacion).
- `get_reservation_status_by_phone` consulta estado solo para reservas del telefono del solicitante.
- `expire_reservation_draft` se ejecuta como job del sistema para vencer borradores sin avance.
- Regla: `create_reservation_draft` requiere `quote_snapshot` valido antes de persistir el borrador.

Confirmacion administrativa en backend:
- `POST /api/v1/payment-proofs/{payment_proof_id}/verify` y `POST /api/v1/payment-proofs/{payment_proof_id}/reject` son acciones de admin con permiso `PAYMENT_VERIFY`.
- `POST /api/v1/reservations/{reservation_id}/confirm` exige pago verificado y realiza commit de cupo con revalidacion al confirmar.

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

- `ai/` no ejecuta acciones críticas: solo planifica, redacta y ejecuta escritura limitada no crítica.
- `services/` valida disponibilidad real; la tool `check_experience_availability` es una consulta operativa, no una confirmación.
- Las herramientas críticas (`confirm_reservation`, etc.) están bloqueadas por `ToolPolicyEngine` y no se exponen al LLM.
- Cada turno y tool call se loguea con trazabilidad completa (`trace_id`).
- La sesión acumula slots entre turnos hasta completar los datos necesarios para una tool call.

## Notificaciones deterministas

El servicio `ReservationWhatsAppNotificationService` envía mensajes transaccionales (aprobación/rechazo de pago, logística, formulario) directamente vía `WhatsAppOutboundService`, sin pasar por el LLM. Los templates de notificación se seedean automáticamente al arrancar la aplicación (`seed_notification_templates` en `lifespan`) para evitar errores de "template not found".
