# Tools MCP (Referencia Completa)

Este documento lista todos los MCP tools del asistente AI expuestos por `apps/api` según el registro en `ai/mcp/registry.py` y el pipeline del orquestador.

## Convenciones

- Los tools NO son endpoints HTTP. Se invocan internamente via `AssistantOrchestrator.ask()`.
- Entrada/salida: `dict[str, Any]` con contratos Pydantic en `tool_contracts.py`.
- Todo tool call se persiste en `ToolCallLogDocument` (colección `tool_call_logs`).
- El pipeline completo: **planner (Gemini) → policy engine → registry.call() → response composer**.
- Los tools son síncronos desde la perspectiva del orquestador pero asíncronos internamente.
- No deben crear reservas, confirmar pagos ni modificar cupos.

## Pipeline

| Paso | Componente | Archivo | Descripción |
|---|---|---|---|
| 1 | Planner | `ai/assistant/planner.py` | LLM (Gemini) decide acción: `tool_call`, `final_response`, `ask_clarifying_question`, `human_handoff` |
| 2 | Policy | `ai/assistant/policy.py` | `ToolPolicyEngine` valida plan: confianza, riesgo, args requeridos, tool permitido |
| 3 | Registry | `ai/mcp/registry.py` | `ToolRegistry.call()` ejecuta el tool por nombre |
| 4 | Composer | `ai/assistant/response_composer.py` | Compone respuesta final (modo `cheap` o vía LLM) |

## Tools Registrados

### `check_experience_availability`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/availability.py` |
| Propósito | Consulta disponibilidad operativa de una experiencia en una fecha y cantidad de participantes |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `CheckExperienceAvailabilityInput` |
| output | `CheckExperienceAvailabilityOutput` |

**Input (`CheckExperienceAvailabilityInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `experience_id` | `str \| None` | No* | ID de la experiencia. Puede ser null si se usa `experience_query`. |
| `experience_query` | `str \| None` | No* | Texto libre para buscar experiencia por nombre/slug. |
| `requested_date` | `date` | Sí | Fecha solicitada. |
| `participant_count` | `int` (1-30) | Sí | Cantidad de participantes. |

**Output (`CheckExperienceAvailabilityOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `available` | `bool` | `true` si hay cupo y no hay bloqueos. |
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"check_experience_availability"` | Identificador del tool. |
| `experience_id` | `str \| None` | ID de la experiencia resuelta. |
| `experience_name` | `str \| None` | Nombre de la experiencia. |
| `schedule_id` | `str \| None` | ID del schedule encontrado. |
| `requested_date` | `date` | Fecha evaluada. |
| `participant_count` | `int` | Participantes solicitados. |
| `capacity_total` | `int \| None` | Cupo total del schedule. |
| `capacity_available` | `int \| None` | Cupos disponibles. |
| `min_notice_days` | `int \| None` | Anticipación mínima requerida. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos de bloqueo si no disponible. |

**Blocking reasons posibles**

| Código | Significado |
|---|---|
| `experience.not_found` | No se encontró experiencia que coincida. |
| `schedule.not_found` | No hay fecha operativa programada para esa fecha. |
| `schedule.not_open` | La fecha operativa está cerrada/completa/cancelada. |
| `schedule.no_availability` | No hay cupos suficientes. |
| `reservation.min_notice_violation` | No cumple anticipación mínima. |
| `tool.unhandled_error` | Error interno no esperado. |

---

### `list_experiences`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/catalog.py` |
| Propósito | Lista el catálogo de experiencias activas con resumen |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | Parámetros kwargs (sin contrato Pydantic propio) |
| output | `dict` con `experiences` y `total` |

**Input (kwargs)**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `is_active` | `bool \| None` | `True` | Filtrar por activas. |
| `limit` | `int` | `20` | Máximo de resultados. |

**Output**

| Campo | Tipo | Descripción |
|---|---|---|
| `experiences` | `list[dict]` | Lista de experiencias. |
| `total` | `int` | Cantidad de resultados. |

**Item del listado**

| Campo | Tipo | Descripción |
|---|---|---|
| `experience_id` | `str` | ID de la experiencia. |
| `name` | `str` | Nombre. |
| `slug` | `str` | Slug URL. |
| `short_description` | `str` | Subtítulo o primeros 120 chars de descripción. |
| `duration` | `str \| None` | Texto de duración. |
| `difficulty` | `str \| None` | Dificultad. |
| `level` | `str \| None` | Nivel. |
| `starting_price` | `int \| None` | Precio mínimo desde. |
| `tags` | `list[str]` | Etiquetas. |

---

### `quote_experience`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/quote.py` |
| Propósito | Genera cotización de precio para una experiencia según participantes y tarifas |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `QuoteExperienceInput` |
| output | `QuoteExperienceOutput` |

**Input (`QuoteExperienceInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `experience_id` | `str \| None` | No* | ID de la experiencia. |
| `experience_query` | `str \| None` | No* | Texto libre para buscar experiencia. |
| `participants_count` | `int` (1-30) | Sí | Número de participantes. |
| `schedule_id` | `str \| None` | No | ID opcional del schedule para validar coherencia. |
| `special_conditions` | `dict[str, str]` | No | Condiciones especiales (default `{}`). |

**Output (`QuoteExperienceOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `quoted` | `bool` | `true` si se pudo cotizar. |
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"quote_experience"` | Identificador del tool. |
| `experience_id` | `str \| None` | ID de la experiencia. |
| `experience_name` | `str \| None` | Nombre de la experiencia. |
| `participants_count` | `int` | Participantes cotizados. |
| `unit_price` | `int \| None` | Precio por persona. |
| `subtotal` | `int \| None` | Total estimado. |
| `currency` | `str` | Moneda (default `COP`). |
| `pricing_tier` | `QuotePricingTier \| None` | Tramo de precios aplicado. |
| `requested_date` | `str \| None` | Fecha solicitada (eco). |
| `notes` | `str \| None` | Notas adicionales. |
| `next_step` | `str` | Siguiente paso sugerido (default `check_availability_or_create_reservation_draft`). |
| `disclaimer` | `str` | Descargo: cotización no confirma reserva. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si no se pudo cotizar. |

**Blocking reasons posibles**

| Código | Significado |
|---|---|
| `quote.missing_participant_count` | Falta número de participantes. |
| `experience.not_found` | No se encontró experiencia. |
| `tool.unhandled_error` | Error interno no esperado. |

**QuotePricingTier**

| Campo | Tipo | Descripción |
|---|---|---|
| `min_participants` | `int` | Mínimo de participantes del tramo. |
| `max_participants` | `int` | Máximo de participantes del tramo. |
| `price_per_person` | `int` | Precio por persona en COP. |

---

## Gobernanza (ToolPolicyEngine)

| Clasificación | Tools | Acción |
|---|---|---|
| `READ_TOOLS` | `check_experience_availability`, `list_experiences`, `quote_experience` | Permitidos si pasan validaciones de args |
| `WRITE_TOOLS` | *(vacio)* | Reservado para futuros tools de escritura |
| `CRITICAL_TOOLS` | `confirm_reservation`, `cancel_reservation`, `mark_payment_verified`, `change_schedule_capacity`, `block_slots` | **Siempre denegados** — requieren intervención humana |

**Reglas de denegación** (orden de evaluación):

| Condición | Razón | HTTP análogo |
|---|---|---|
| `confidence < min_confidence` | `low_confidence` | — |
| `action != tool_call` | — | — (permitido) |
| `tool_name in CRITICAL_TOOLS` | `critical_tool_denied` | `403` |
| `risk_level in {HIGH, CRITICAL}` | `high_risk_requires_human` | `403` |
| `needs_human == true` | `human_review_required` | `403` |
| tool no está en READ_TOOLS ni WRITE_TOOLS | `unknown_or_not_allowed_tool` | `404/403` |
| `check_experience_availability` sin `requested_date` o `participant_count` | `missing_required_arguments:...` | `422` |
| `quote_experience` sin `experience_id`/`experience_query` | `missing_required_arguments:experience_id_or_experience_query` | `422` |
| `quote_experience` sin `participant_count`/`participants_count` | `missing_required_arguments:participant_count_or_participants_count` | `422` |

---

## Persistencia (ToolCallLogDocument)

Colección: `tool_call_logs`

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad (UUID). |
| `conversation_turn_id` | `str \| None` | ID del turno de conversación. |
| `tool_name` | `str` | Nombre del tool ejecutado. |
| `tool_version` | `str` | Versión del tool (default `2026-05-11`). |
| `input` | `dict[str, Any]` | Argumentos de entrada. |
| `output` | `dict[str, Any]` | Resultado de salida. |
| `status` | `str` | `"success"` o `"error"`. |
| `error_code` | `str \| None` | Código de error si falló. |
| `created_at` | `datetime` | Timestamp UTC. |

**Índices:** `trace_id`, `conversation_turn_id`, `tool_name`, `status`, `created_at`.

---

## Endpoint HTTP Relacionado

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/ask` | `ask_api_v1_ask_post` | `AskRequest` | `200 AskResponse` | `200` |

**`AskRequest`**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `message` | `str` | Sí | Mensaje del usuario. |
| `channel` | `"test" \| "whatsapp"` | No | Canal (default `test`). |
| `from_phone` | `str \| None` | No | Número de teléfono. |
| `conversation_id` | `str \| None` | No | ID de conversación existente. |
| `trace_id` | `str \| None` | No | ID de trazabilidad. |

**`AskResponse`**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `action` | `AssistantAction` | Acción resultante (`tool_call`, `final_response`, `ask_clarifying_question`, `human_handoff`). |
| `tool_name` | `str \| None` | Nombre del tool ejecutado (si aplica). |
| `planner_output` | `dict` | Output completo del planner. |
| `tool_output` | `dict` | Output del tool (vacío si no se ejecutó tool). |
| `response` | `str` | Respuesta textual para el usuario. |

**Estados de error del pipeline Ask**

| Condición | `action` resultante | `response` |
|---|---|---|
| Gemini cuota excedida (`GeminiResourceExhausted`) | `final_response` | Mensaje de servicio sobrepasado |
| Gemini modelo no disponible (`GeminiModelUnavailable`) | `human_handoff` | Transferencia a asesor humano |
| Error Gemini genérico (`GeminiProviderError`) | `human_handoff` | Transferencia a asesor humano |
| Tool execution falla | `tool_call` (con `tool_output.error`) | Mensaje de error genérico |

---

## Servidor MCP Standalone

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/server.py` |
| Framework | `FastMCP` |
| Server name | `lajuana-mcp` |
| Tools expuestos | `check_experience_availability`, `quote_experience` |
| `list_experiences` | No expuesto vía MCP standalone |

---

## ToolRegistry

| Método | Descripción |
|---|---|
| `register(name, callable)` | Registra un tool asíncrono. Lanza `RuntimeError` si ya existe. |
| `call(name, **kwargs)` | Ejecuta el tool, mide latencia, retorna `dict`. Lanza `RuntimeError` si no existe. |
| `names()` | Lista nombres registrados en orden alfabético. |

Singleton: `app.ai.mcp.registry.registry`

## Tools registrados actualmente

| Tool | Alias en registry | Archivo |
|---|---|---|
| check_experience_availability | `check_experience_availability` | `ai/mcp/tools/availability.py` |
| list_experiences | `list_experiences` | `ai/mcp/tools/catalog.py` |
| quote_experience | `quote_experience` | `ai/mcp/tools/quote.py` |

## Notas de mantenimiento

- Esta referencia debe actualizarse cuando se agregue/elimine/modifique un tool MCP.
- La fuente de verdad contractual sigue siendo `tool_contracts.py` + `ToolPolicyEngine` + `ToolCallLogDocument`.
- Para detalle narrativo del flujo conversacional, usar `docs/architecture/chatbot-whatsapp-v2.md`.
- Los `CRITICAL_TOOLS` están definidos pero no implementados como tools reales — existen solo como bloqueo preventivo en `policy.py`.
