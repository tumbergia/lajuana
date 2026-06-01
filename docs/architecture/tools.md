# Tools MCP (Referencia Completa)

Este documento lista todos los MCP tools del asistente AI expuestos por `apps/api` según el registro en `ai/mcp/registry.py` y el pipeline del orquestador.

## Convenciones

- Los tools NO son endpoints HTTP. Se invocan internamente via `AssistantOrchestrator.ask()`.
- Entrada/salida: `dict[str, Any]` con contratos Pydantic en `tool_contracts.py`.
- Todo tool call se persiste en `ToolCallLogDocument` (colección `tool_call_logs`).
- El pipeline completo: **planner (Gemini) → policy engine → registry.call() → response composer**.
- Los tools son síncronos desde la perspectiva del orquestador pero asíncronos internamente.
- No deben confirmar pagos ni modificar cupos.

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
| `next_step` | `str` | Siguiente paso sugerido (default `check_availability_or_create_reservation_draft`; en Horizonte 2 el flujo de escritura usa `create_reservation_draft`). |
| `disclaimer` | `str` | Descargo: cotización no confirma reserva y no crea borrador por si sola (`quote_snapshot` es requisito previo para `create_reservation_draft`). |
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

### `list_available_schedules`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/schedules.py` |
| Propósito | Lista fechas y horarios disponibles para una experiencia en un rango de 60 días |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `ListAvailableSchedulesInput` |
| output | `ListAvailableSchedulesOutput` |

**Input (`ListAvailableSchedulesInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `experience_id` | `str \| None` | No* | ID de la experiencia. |
| `experience_query` | `str \| None` | No* | Texto libre para buscar experiencia. |
| `date_from` | `date \| None` | No | Fecha inicio (default: hoy). |
| `date_to` | `date \| None` | No | Fecha fin (default: date_from + 60 días). |
| `participant_count` | `int \| None` | No | Filtra schedules con cupo suficiente. |
| `limit` | `int` (1-30) | No | Máximo de resultados (default 10). |

**Output (`ListAvailableSchedulesOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"list_available_schedules"` | Identificador del tool. |
| `date_from` | `date` | Fecha inicio del rango. |
| `date_to` | `date` | Fecha fin del rango. |
| `participant_count` | `int \| None` | Filtro aplicado. |
| `schedules` | `list[AvailableScheduleItem]` | Schedules encontrados. |
| `total` | `int` | Cantidad total de schedules (sin limit). |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

**AvailableScheduleItem**

| Campo | Tipo | Descripción |
|---|---|---|
| `schedule_id` | `str` | ID del schedule. |
| `experience_id` | `str` | ID de la experiencia. |
| `experience_name` | `str` | Nombre de la experiencia. |
| `scheduled_date` | `date` | Fecha programada. |
| `start_time` | `str \| None` | Hora de inicio. |
| `capacity_total` | `int` | Cupo total. |
| `capacity_available` | `int` | Cupos disponibles. |
| `status` | `str` | Estado del schedule. |

---

### `suggest_alternative_dates`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/schedules.py` |
| Propósito | Sugiere fechas alternativas cuando no hay disponibilidad en la fecha solicitada |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `SuggestAlternativeDatesInput` |
| output | `SuggestAlternativeDatesOutput` |

**Input (`SuggestAlternativeDatesInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `experience_id` | `str \| None` | No* | ID de la experiencia. |
| `experience_query` | `str \| None` | No* | Texto libre para buscar experiencia. |
| `requested_date` | `date` | Sí | Fecha original solicitada. |
| `participant_count` | `int` (1-30) | Sí | Cantidad de participantes. |
| `search_days_before` | `int` (0-60) | No | Días antes a buscar (default 15). |
| `search_days_after` | `int` (1-90) | No | Días después a buscar (default 30). |
| `limit` | `int` (1-10) | No | Máximo de alternativas (default 5). |
| `exclude_dates` | `list[date]` | No | Fechas a excluir. |

**Output (`SuggestAlternativeDatesOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"suggest_alternative_dates"` | Identificador del tool. |
| `requested_date` | `date` | Fecha original. |
| `participant_count` | `int` | Participantes. |
| `alternatives` | `list[AvailableScheduleItem]` | Fechas alternativas. |
| `total` | `int` | Cantidad de alternativas. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

---

### `get_experience_detail`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/__init__.py` (stub, implementación planned) |
| Propósito | Obtiene información detallada de una experiencia |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `GetExperienceDetailInput` |
| output | `ExperienceDetailOutput` |

**Input (`GetExperienceDetailInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `experience_id` | `str \| None` | No* | ID de la experiencia. |
| `experience_query` | `str \| None` | No* | Texto libre para buscar experiencia. |

**Output (`ExperienceDetailOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"get_experience_detail"` | Identificador del tool. |
| `found` | `bool` | Si se encontró la experiencia. |
| `experience_id` | `str \| None` | ID de la experiencia. |
| `name` | `str \| None` | Nombre. |
| `slug` | `str \| None` | Slug URL. |
| `description` | `str \| None` | Descripción completa. |
| `short_description` | `str \| None` | Subtítulo. |
| `duration` | `str \| None` | Duración. |
| `difficulty` | `str \| None` | Dificultad. |
| `level` | `str \| None` | Nivel. |
| `includes` | `list[str]` | Incluye. |
| `restrictions` | `list[str]` | Restricciones. |
| `starting_price` | `int \| None` | Precio mínimo. |
| `currency` | `str` | Moneda (default COP). |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

---

### `get_public_business_rules`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/__init__.py` (stub, implementación planned) |
| Propósito | Devuelve las reglas de negocio públicas de La Juana |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `PublicBusinessRulesInput` |
| output | `PublicBusinessRulesOutput` |

**Input (`PublicBusinessRulesInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `include_reservation_rules` | `bool` | No | Incluir reglas de reserva (default true). |
| `include_behavior_rules` | `bool` | No | Incluir reglas de comportamiento (default true). |

**Output (`PublicBusinessRulesOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"get_public_business_rules"` | Identificador del tool. |
| `family_focus` | `str` | Enfoque familiar. |
| `alcohol_policy` | `str` | Política de alcohol. |
| `behavior_policy` | `str` | Política de comportamiento. |
| `reservation_notice_days` | `int \| None` | Anticipación mínima. |
| `general_restrictions` | `list[str]` | Restricciones generales. |
| `disclaimer` | `str` | Descargo de responsabilidad. |

---

### `request_human_review`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/__init__.py` (stub, implementación planned) |
| Propósito | Crea una solicitud trazable de revisión humana |
| Categoría | `LIMITED_WRITE_TOOLS` (escritura limitada) |
| input | `RequestHumanReviewInput` |
| output | `RequestHumanReviewOutput` |

**Input (`RequestHumanReviewInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `conversation_id` | `str` | Sí | ID de la conversación. |
| `reason_code` | `Literal[...]` | Sí | Motivo: `customer_requests_human`, `unclear_experience`, `special_condition`, `availability_conflict`, `payment_or_confirmation`, `safety_or_incident`, `other` |
| `summary` | `str` (10-1000) | Sí | Resumen del caso. |
| `priority` | `Literal["low", "normal", "high", "urgent"]` | No | Prioridad (default `normal`). |

**Output (`RequestHumanReviewOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"request_human_review"` | Identificador del tool. |
| `requested` | `bool` | `true` si se creó la solicitud. |
| `review_id` | `str` | ID de la solicitud de revisión. |
| `status` | `"open" \| "already_open"` | Estado de la solicitud. |
| `message` | `str` | Mensaje para el usuario. |

---

### `attach_payment_proof_to_reservation`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/reservation_draft.py` |
| Propósito | Asocia un comprobante de pago enviado por WhatsApp a una pre-reserva activa |
| Categoría | `LIMITED_WRITE_TOOLS` (escritura limitada) |
| input | `AttachPaymentProofToReservationInput` |
| output | `AttachPaymentProofToReservationOutput` |

**Input (`AttachPaymentProofToReservationInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `reservation_id` | `str \| None` | No* | ID interno de reserva. |
| `public_reservation_code` | `str \| None` | No* | Código público de reserva (`PR-...`). |
| `from_phone` | `str` | Sí | Teléfono remitente para validación de pertenencia. |
| `whatsapp_message_id` | `str` | Sí | ID del mensaje de WhatsApp para idempotencia. |
| `media_id` | `str` | Sí | ID del media en Meta. |
| `media_mime_type` | `str` | Sí | Tipo MIME del archivo. |
| `filename` | `str \| None` | No | Nombre original del archivo. |
| `caption` | `str \| None` | No | Texto adicional enviado con el comprobante. |

\*Debe venir `reservation_id` o `public_reservation_code`.

**Output (`AttachPaymentProofToReservationOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `attached` | `bool` | `true` si el comprobante quedó asociado o detectado como duplicado idempotente. |
| `idempotent` | `bool` | `true` si ya existía un comprobante equivalente. |
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"attach_payment_proof_to_reservation"` | Identificador del tool. |
| `reservation_code` | `str \| None` | Código público de reserva. |
| `reservation_status` | `"pending_payment" \| "payment_received" \| "unknown"` | Estado público de pago de la reserva. |
| `proof_status` | `"received" \| "under_review" \| "duplicate" \| "rejected"` | Estado del comprobante. |
| `message` | `str` | Mensaje operativo corto. |
| `response` | `str` | Respuesta redactada para el cliente. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos de bloqueo si falla. |

**Reglas implementadas**

- El tool solo registra/adjunta evidencia: **no** valida pago ni confirma reserva.
- Si el media ya existe (por `whatsapp_message_id` o hash), retorna `idempotent=true` y mantiene estado en revisión.
- La confirmación final depende de revisión administrativa y `confirm_reservation` en backend.

---

### `admin_get_logistics_checklist`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/operations.py` |
| Propósito | Obtiene checklist logístico de una reserva: estado, participantes, asignaciones, pólizas, registro de llegada |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `LogisticsChecklistInput` |
| output | `LogisticsChecklistOutput` |

**Input (`LogisticsChecklistInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `reservation_id` | `str` | Sí | ID de la reserva. |

**Output (`LogisticsChecklistOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"admin_get_logistics_checklist"` | Identificador del tool. |
| `reservation_id` | `str` | ID de la reserva consultada. |
| `items` | `list[LogisticsChecklistItem]` | Items del checklist. |
| `total` | `int` | Total de items. |
| `completed` | `int` | Items completados. |
| `pending` | `int` | Items pendientes. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

**LogisticsChecklistItem**

| Campo | Tipo | Descripción |
|---|---|---|
| `category` | `str` | Categoría (reserva, participantes, asignaciones, pólizas, operación). |
| `label` | `str` | Descripción del item. |
| `status` | `"completed" \| "pending" \| "not_applicable"` | Estado del item. |
| `details` | `str \| None` | Detalle adicional. |

---

### `guide_create_service_log`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/operations.py` |
| Propósito | Registra una entrada de bitácora de servicio para una reserva |
| Categoría | `LIMITED_WRITE_TOOLS` (escritura limitada) |
| input | `CreateServiceLogInput` |
| output | `CreateServiceLogOutput` |

**Input (`CreateServiceLogInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `reservation_id` | `str` | Sí | ID de la reserva. |
| `event_type` | `"arrival" \| "departure" \| "checkpoint" \| "closure" \| "note"` | Sí | Tipo de evento. |
| `happened_at` | `str \| None` | No | Timestamp ISO 8601 del evento (default: ahora). |
| `checkpoint_name` | `str \| None` | No* | Obligatorio si event_type es `checkpoint`. |
| `notes` | `str \| None` | No | Notas adicionales. |
| `related_participant_id` | `str \| None` | No | ID del participante relacionado. |
| `related_equine_id` | `str \| None` | No | ID del equino relacionado. |

**Output (`CreateServiceLogOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"guide_create_service_log"` | Identificador del tool. |
| `created` | `bool` | `true` si se registró la bitácora. |
| `log_id` | `str \| None` | ID del log creado. |
| `message` | `str` | Mensaje para el usuario. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

---

### `guide_report_incident`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/operations.py` |
| Propósito | Reporta un incidente durante la ejecución del servicio |
| Categoría | `WRITE_TOOLS` (escritura) |
| input | `ReportIncidentInput` |
| output | `ReportIncidentOutput` |

**Input (`ReportIncidentInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `reservation_id` | `str` | Sí | ID de la reserva. |
| `severity` | `"low" \| "medium" \| "high" \| "critical"` | Sí | Severidad del incidente. |
| `description` | `str` (10-2000) | Sí | Descripción del incidente. |
| `happened_at` | `str \| None` | No | Timestamp ISO 8601 (default: ahora). |
| `related_participant_id` | `str \| None` | No | Participante involucrado. |
| `related_equine_id` | `str \| None` | No | Equino involucrado. |

**Output (`ReportIncidentOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"guide_report_incident"` | Identificador del tool. |
| `reported` | `bool` | `true` si se reportó el incidente. |
| `incident_id` | `str \| None` | ID del incidente. |
| `message` | `str` | Mensaje para el usuario. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

---

### `admin_close_service_execution`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/operations.py` |
| Propósito | Cierra operativamente una reserva confirmada. Transiciona a COMPLETED |
| Categoría | `WRITE_TOOLS` (escritura) |
| input | `CloseServiceExecutionInput` |
| output | `CloseServiceExecutionOutput` |

**Input (`CloseServiceExecutionInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `reservation_id` | `str` | Sí | ID de la reserva a cerrar. |
| `notes` | `str \| None` | No | Notas de cierre. |

**Output (`CloseServiceExecutionOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"admin_close_service_execution"` | Identificador del tool. |
| `closed` | `bool` | `true` si se cerró la ejecución. |
| `reservation_id` | `str \| None` | ID de la reserva cerrada. |
| `message` | `str` | Mensaje para el usuario. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

---

### `admin_add_equine_health_event`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/operations.py` |
| Propósito | Registra un evento de salud o bienestar para un equino |
| Categoría | `LIMITED_WRITE_TOOLS` (escritura limitada) |
| input | `EquineHealthEventInput` |
| output | `EquineHealthEventOutput` |

**Input (`EquineHealthEventInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `equine_id` | `str` | Sí | ID del equino. |
| `event_type` | `"health_check" \| "injury" \| "treatment" \| "medication" \| "rest" \| "note"` | Sí | Tipo de evento. |
| `description` | `str` (5-2000) | Sí | Descripción del evento. |
| `happened_at` | `str \| None` | No | Timestamp ISO 8601 (default: ahora). |
| `severity` | `"low" \| "medium" \| "high"` | No | Severidad (default `low`). |

**Output (`EquineHealthEventOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"admin_add_equine_health_event"` | Identificador del tool. |
| `created` | `bool` | `true` si se registró el evento. |
| `event_id` | `str \| None` | ID del evento creado. |
| `message` | `str` | Mensaje para el usuario. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

---

### `admin_get_equine_workload`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/operations.py` |
| Propósito | Consulta la carga de trabajo de equinos: asignaciones próximas y disponibilidad |
| Categoría | `READ_TOOLS` (solo lectura) |
| input | `EquineWorkloadInput` |
| output | `EquineWorkloadOutput` |

**Input (`EquineWorkloadInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `equine_ids` | `list[str] \| None` | No | IDs específicos de equinos. Si se omite, consulta todos. |
| `only_available` | `bool` | No | Filtrar solo equinos disponibles (default `false`). |

**Output (`EquineWorkloadOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"admin_get_equine_workload"` | Identificador del tool. |
| `workload` | `list[EquineWorkloadItem]` | Carga de trabajo por equino. |
| `total` | `int` | Cantidad de equinos. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

**EquineWorkloadItem**

| Campo | Tipo | Descripción |
|---|---|---|
| `equine_id` | `str` | ID del equino. |
| `name` | `str` | Nombre del equino. |
| `is_available` | `bool` | Disponibilidad actual. |
| `upcoming_assignments` | `int` | Asignaciones futuras (reservas confirmadas). |
| `next_date` | `str \| None` | Próxima fecha de asignación. |

---

### `admin_update_equine_availability`

| Atributo | Valor |
|---|---|
| Archivo | `ai/mcp/tools/operations.py` |
| Propósito | Actualiza la disponibilidad operacional de un equino. Requiere motivo |
| Categoría | `WRITE_TOOLS` (escritura) |
| input | `UpdateEquineAvailabilityInput` |
| output | `UpdateEquineAvailabilityOutput` |

**Input (`UpdateEquineAvailabilityInput`)**

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `equine_id` | `str` | Sí | ID del equino. |
| `is_available` | `bool` | Sí | Nuevo estado de disponibilidad. |
| `reason` | `str` (5-500) | Sí | Motivo del cambio. |

**Output (`UpdateEquineAvailabilityOutput`)**

| Campo | Tipo | Descripción |
|---|---|---|
| `trace_id` | `str` | ID de trazabilidad. |
| `tool_name` | `"admin_update_equine_availability"` | Identificador del tool. |
| `updated` | `bool` | `true` si se actualizó. |
| `equine_id` | `str \| None` | ID del equino actualizado. |
| `is_available` | `bool \| None` | Nuevo estado de disponibilidad. |
| `message` | `str` | Mensaje para el usuario. |
| `blocking_reasons` | `list[ToolBlockingReason]` | Motivos si falló. |

---

## Admin Tools

Tools administrativas disponibles exclusivamente para el canal `admin_api`. Agrupadas por dominio de negocio.

### CRUD — Experiences

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_list_experiences_admin` | READ | Lista experiencias con datos completos (incluye inactivas) |
| `admin_create_experience` | WRITE | Crea una nueva experiencia |
| `admin_update_experience` | WRITE | Actualiza una experiencia existente |
| `admin_deactivate_experience` | WRITE | Desactiva una experiencia |

**Input**: `kwargs` → filtrados por `ExperienceCreateSchema` / `ExperienceUpdateSchema` según el tool.
**Output**: `AdminCreateExperienceOutput` / `AdminUpdateExperienceOutput` / `AdminListExperiencesOutput` / `AdminDeactivateExperienceOutput`

### CRUD — Users

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_list_users` | READ | Lista todos los usuarios del sistema |
| `admin_create_user` | LIMITED_WRITE | Crea nuevo usuario (email, full_name, password, role) |
| `admin_update_user` | LIMITED_WRITE | Actualiza campos de un usuario |
| `admin_deactivate_user` | WRITE | Desactiva (soft-delete) un usuario |

**Output**: `AdminListUsersOutput` / `AdminCreateUserOutput` / `AdminUpdateUserOutput` / `AdminDeactivateUserOutput`

### CRUD — Schedules

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_list_schedules_admin` | READ | Lista schedules con capacidad, slots, estado, activo |
| `admin_create_schedule` | WRITE | Crea schedule (experience_id, date, capacity_total) |
| `admin_update_schedule` | WRITE | Actualiza schedule |
| `admin_deactivate_schedule` | WRITE | Desactiva schedule |

**Output**: `AdminListSchedulesOutput` / `AdminCreateScheduleOutput` / `AdminUpdateScheduleOutput` / `AdminDeactivateScheduleOutput`

### CRUD — Equines

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_list_equines` | READ | Lista equinos (filtro `only_available`) |
| `admin_get_equine` | READ | Detalle completo de un equino |
| `admin_create_equine` | WRITE | Crea un equino |
| `admin_update_equine` | LIMITED_WRITE | Actualiza campos de un equino |
| `admin_deactivate_equine` | WRITE | Marca equino como no disponible |

**Output**: `AdminListEquinesOutput` / `AdminGetEquineOutput` / `AdminCreateEquineOutput` / `AdminUpdateEquineOutput` / `AdminDeactivateEquineOutput`

### Configuración del sistema

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_get_system_config` | READ | Muestra reglas de reserva + datos de pago |
| `admin_update_reservation_rules` | WRITE | Actualiza reglas (min_days, TTL, payment_proof) |
| `admin_get_payment_instructions` | READ | Muestra datos bancarios configurados |

**Output**: `AdminGetSystemConfigOutput` / `AdminUpdateReservationRulesOutput` / `AdminGetPaymentInstructionsOutput`

### Analítica y reportes

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_get_sales_summary` | READ | Resumen de ventas por rango de fechas |
| `admin_get_reservation_funnel` | READ | Embudo de conversión de reservas |
| `admin_get_channel_performance` | READ | Rendimiento por canal de atención |
| `admin_get_occupancy_report` | READ | Ocupación por fecha/experiencia |
| `admin_get_equine_workload_report` | READ | Carga de trabajo equina en rango de fechas |

**Input**: `date_from`, `date_to` (formato ISO), `experience_id` (solo occupancy).
**Output**: `SalesSummaryOutput` / `ReservationFunnelOutput` / `ChannelPerformanceOutput` / `OccupancyReportOutput` / `EquineWorkloadReportOutput`

### Operaciones de campo

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_get_logistics_checklist` | READ | Checklist operativo de una reserva |
| `admin_close_service_execution` | WRITE | Cierra servicio (reserva CONFIRMED → COMPLETED) |
| `admin_get_equine_workload` | READ | Carga de trabajo actual de equinos |
| `admin_update_equine_availability` | WRITE | Cambia disponibilidad de un equino (requiere motivo) |
| `admin_add_equine_health_event` | LIMITED_WRITE | Registra evento de salud equina |

**Output**: `LogisticsChecklistOutput` / `CloseServiceExecutionOutput` / `EquineWorkloadOutput` / `UpdateEquineAvailabilityOutput` / `EquineHealthEventOutput`

### Gestión de comprobantes de pago

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_get_payment_proof` | READ | Consulta comprobante por ID o reservation_id |
| `admin_approve_payment` | WRITE | Aprueba pago (verifica + avanza reserva a PAYMENT_RECEIVED + envía WhatsApp) |
| `admin_reject_payment_proof` | WRITE | Rechaza comprobante con motivo (notifica al cliente) |
| `admin_unverify_payment_proof` | WRITE | Deshace verificación (revierte reserva a PENDING_PAYMENT) |
| `admin_unreject_payment_proof` | WRITE | Deshace rechazo |

**Input**: `payment_proof_id` + según operación: `note`, `reason`.
**Output**: `AdminGetPaymentProofOutput` / `AdminApprovePaymentOutput` / `AdminRejectPaymentProofOutput` / `AdminUnverifyPaymentProofOutput` / `AdminUnrejectPaymentProofOutput`

### Gestión de reservas

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_list_reservations` | READ | Lista reservas (filtros: status, date_from, date_to) |
| `admin_get_reservation_detail` | READ | Detalle completo por ID o código público |
| `admin_confirm_reservation` | WRITE | Confirma reserva (valida anticipación, pago verificado, cupos, genera form link + WhatsApp) |
| `admin_cancel_reservation` | WRITE | Cancela reserva (libera schedule si estaba confirmada) |

**Output**: `AdminListReservationsOutput` / `AdminGetReservationDetailOutput` / `AdminConfirmReservationOutput` / `AdminCancelReservationOutput`

### Participantes

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_get_participant` | READ | Detalle completo de un participante + contacto de emergencia |
| `admin_update_participant` | LIMITED_WRITE | Actualiza campos de un participante (no crea nuevos) |

**Output**: `AdminGetParticipantOutput` / `AdminUpdateParticipantOutput`

### Automatizaciones

| Tool | Categoría | Propósito |
|---|---|---|
| `schedule_birthday_automation` | WRITE | Activa/desactiva/consulta estado de mensajes de cumpleaños |
| `schedule_visit_anniversary_automation` | WRITE | Activa/desactiva/consulta estado de mensajes de aniversario |
| `send_post_service_message` | LIMITED_WRITE | Registra mensaje post-servicio para una reserva completada |

**Input**: `enabled` (bool, opcional — si se omite solo consulta), `reservation_id`.
**Output**: `BirthdayAutomationOutput` / `AnniversaryAutomationOutput` / `PostServiceMessageOutput`

### Revisiones humanas

| Tool | Categoría | Propósito |
|---|---|---|
| `admin_list_human_review_requests` | READ | Lista solicitudes de revisión humana (filtros: status, priority) |

**Output**: `AdminListHumanReviewRequestsOutput`

---

## Gobernanza (ToolPolicyEngine)

| Clasificación | Tools | Acción |
|---|---|---|
| `READ_TOOLS` | `list_experiences`, `get_experience_detail`, `get_public_business_rules`, `check_experience_availability`, `list_available_schedules`, `quote_experience`, `suggest_alternative_dates`, `get_reservation_public_summary`, `get_reservation_status_by_phone`, `admin_get_logistics_checklist`, `admin_get_equine_workload`, `admin_get_sales_summary`, `admin_get_reservation_funnel`, `admin_get_channel_performance`, `admin_get_occupancy_report`, `admin_get_equine_workload_report`, `admin_list_experiences_admin`, `admin_list_users`, `admin_list_schedules_admin`, `admin_get_system_config`, `admin_get_payment_instructions`, `admin_list_human_review_requests`, `admin_get_payment_proof`, `admin_list_reservations`, `admin_get_reservation_detail`, `admin_list_equines`, `admin_get_equine`, `admin_get_participant` | Permitidos si pasan validaciones de args |
| `LIMITED_WRITE_TOOLS` | `request_human_review`, `create_reservation_draft`, `attach_payment_proof_to_reservation`, `guide_create_service_log`, `admin_add_equine_health_event`, `send_post_service_message`, `generate_participant_form_link`, `get_participant_form_status`, `admin_create_user`, `admin_update_user`, `admin_update_equine`, `admin_update_participant` | Escritura limitada (handoff trazable) |
| `WRITE_TOOLS` | `guide_report_incident`, `admin_close_service_execution`, `admin_update_equine_availability`, `schedule_birthday_automation`, `schedule_visit_anniversary_automation`, `admin_create_experience`, `admin_update_experience`, `admin_deactivate_experience`, `admin_deactivate_user`, `admin_create_schedule`, `admin_update_schedule`, `admin_deactivate_schedule`, `admin_update_reservation_rules`, `admin_approve_payment`, `admin_reject_payment_proof`, `admin_unverify_payment_proof`, `admin_unreject_payment_proof`, `admin_confirm_reservation`, `admin_cancel_reservation`, `admin_create_equine`, `admin_deactivate_equine` | Escritura, pasa por validación de riesgo |
| `CRITICAL_TOOLS` | `confirm_reservation`, `cancel_reservation`, `mark_payment_verified`, `change_schedule_capacity`, `block_slots` | **Siempre denegados** — requieren intervención humana. Nota: `admin_confirm_reservation` y `admin_cancel_reservation` son independientes (nombres distintos) y están permitidos para canal admin. |

**Reglas de denegación** (orden de evaluación):

| Condición | Razón | HTTP análogo |
|---|---|---|
| `confidence < min_confidence` | `low_confidence` | — |
| `action != tool_call` | — | — (permitido) |
| `tool_name in CRITICAL_TOOLS` | `critical_tool_denied` | `403` |
| `risk_level in {HIGH, CRITICAL}` | `high_risk_requires_human` | `403` |
| `needs_human == true` | `human_review_required` | `403` |
| tool no está en READ_TOOLS ni WRITE_TOOLS ni LIMITED_WRITE_TOOLS | `unknown_or_not_allowed_tool` | `404/403` |
| `check_experience_availability` sin `requested_date` o `participant_count` | `missing_required_arguments:...` | `422` |
| `quote_experience` sin `experience_id`/`experience_query` | `missing_required_arguments:experience_id_or_experience_query` | `422` |
| `quote_experience` sin `participant_count` | `missing_required_arguments:participant_count` | `422` |
| `get_reservation_public_summary` sin `code` o `holder_phone` | `missing_required_arguments:code,holder_phone` | `422` |

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
| Tools expuestos | `admin_add_equine_health_event`, `admin_close_service_execution`, `admin_get_channel_performance`, `admin_get_equine_workload`, `admin_get_equine_workload_report`, `admin_get_logistics_checklist`, `admin_get_occupancy_report`, `admin_get_reservation_funnel`, `admin_get_sales_summary`, `admin_update_equine_availability`, `admin_get_payment_proof`, `admin_approve_payment`, `admin_reject_payment_proof`, `admin_unverify_payment_proof`, `admin_unreject_payment_proof`, `admin_list_reservations`, `admin_get_reservation_detail`, `admin_confirm_reservation`, `admin_cancel_reservation`, `admin_list_equines`, `admin_get_equine`, `admin_create_equine`, `admin_update_equine`, `admin_deactivate_equine`, `admin_get_participant`, `admin_update_participant`, `admin_list_experiences_admin`, `admin_create_experience`, `admin_update_experience`, `admin_deactivate_experience`, `admin_list_users`, `admin_create_user`, `admin_update_user`, `admin_deactivate_user`, `admin_list_schedules_admin`, `admin_create_schedule`, `admin_update_schedule`, `admin_deactivate_schedule`, `admin_get_system_config`, `admin_update_reservation_rules`, `admin_get_payment_instructions`, `admin_list_human_review_requests`, `attach_payment_proof_to_reservation`, `check_experience_availability`, `create_reservation_draft`, `get_experience_detail`, `get_public_business_rules`, `get_reservation_public_summary`, `get_reservation_status_by_phone`, `guide_create_service_log`, `guide_report_incident`, `list_available_schedules`, `list_experiences`, `quote_experience`, `request_human_review`, `schedule_birthday_automation`, `schedule_visit_anniversary_automation`, `send_post_service_message`, `suggest_alternative_dates` |

---

## ToolRegistry

| Método | Descripción |
|---|---|
| `register(name, callable)` | Registra un tool asíncrono. Lanza `RuntimeError` si ya existe. |
| `call(name, **kwargs)` | Ejecuta el tool, mide latencia, retorna `dict`. Lanza `RuntimeError` si no existe. |
| `names()` | Lista nombres registrados en orden alfabético. |

Singleton: `app.ai.mcp.registry.registry`

## Tools registrados actualmente

| Tool | Archivo | Contrato Pydantic |
|---|---|---|
| admin_add_equine_health_event | `ai/mcp/tools/operations.py` | Sí |
| admin_approve_payment | `ai/mcp/tools/admin_payment_proofs.py` | Sí |
| admin_cancel_reservation | `ai/mcp/tools/admin_reservations.py` | Sí |
| admin_close_service_execution | `ai/mcp/tools/operations.py` | Sí |
| admin_confirm_reservation | `ai/mcp/tools/admin_reservations.py` | Sí |
| admin_create_equine | `ai/mcp/tools/admin_equines.py` | Sí |
| admin_create_experience | `ai/mcp/tools/admin_experiences.py` | Sí |
| admin_create_schedule | `ai/mcp/tools/admin_schedules.py` | Sí |
| admin_create_user | `ai/mcp/tools/admin_users.py` | Sí |
| admin_deactivate_equine | `ai/mcp/tools/admin_equines.py` | Sí |
| admin_deactivate_experience | `ai/mcp/tools/admin_experiences.py` | Sí |
| admin_deactivate_schedule | `ai/mcp/tools/admin_schedules.py` | Sí |
| admin_deactivate_user | `ai/mcp/tools/admin_users.py` | Sí |
| admin_get_channel_performance | `ai/mcp/tools/analytics.py` | Sí |
| admin_get_equine | `ai/mcp/tools/admin_equines.py` | Sí |
| admin_get_equine_workload | `ai/mcp/tools/operations.py` | Sí |
| admin_get_equine_workload_report | `ai/mcp/tools/analytics.py` | Sí |
| admin_get_logistics_checklist | `ai/mcp/tools/operations.py` | Sí |
| admin_get_occupancy_report | `ai/mcp/tools/analytics.py` | Sí |
| admin_get_participant | `ai/mcp/tools/admin_participants.py` | Sí |
| admin_get_payment_instructions | `ai/mcp/tools/admin_config.py` | Sí |
| admin_get_payment_proof | `ai/mcp/tools/admin_payment_proofs.py` | Sí |
| admin_get_reservation_detail | `ai/mcp/tools/admin_reservations.py` | Sí |
| admin_get_reservation_funnel | `ai/mcp/tools/analytics.py` | Sí |
| admin_get_sales_summary | `ai/mcp/tools/analytics.py` | Sí |
| admin_get_system_config | `ai/mcp/tools/admin_config.py` | Sí |
| admin_list_equines | `ai/mcp/tools/admin_equines.py` | Sí |
| admin_list_experiences_admin | `ai/mcp/tools/admin_experiences.py` | Sí |
| admin_list_human_review_requests | `ai/mcp/tools/admin_reviews.py` | Sí |
| admin_list_reservations | `ai/mcp/tools/admin_reservations.py` | Sí |
| admin_list_schedules_admin | `ai/mcp/tools/admin_schedules.py` | Sí |
| admin_list_users | `ai/mcp/tools/admin_users.py` | Sí |
| admin_reject_payment_proof | `ai/mcp/tools/admin_payment_proofs.py` | Sí |
| admin_unreject_payment_proof | `ai/mcp/tools/admin_payment_proofs.py` | Sí |
| admin_unverify_payment_proof | `ai/mcp/tools/admin_payment_proofs.py` | Sí |
| admin_update_equine | `ai/mcp/tools/admin_equines.py` | Sí |
| admin_update_equine_availability | `ai/mcp/tools/operations.py` | Sí |
| admin_update_experience | `ai/mcp/tools/admin_experiences.py` | Sí |
| admin_update_participant | `ai/mcp/tools/admin_participants.py` | Sí |
| admin_update_reservation_rules | `ai/mcp/tools/admin_config.py` | Sí |
| admin_update_schedule | `ai/mcp/tools/admin_schedules.py` | Sí |
| admin_update_user | `ai/mcp/tools/admin_users.py` | Sí |
| attach_payment_proof_to_reservation | `ai/mcp/tools/reservation_draft.py` | Sí |
| check_experience_availability | `ai/mcp/tools/availability.py` | Sí |
| create_reservation_draft | `ai/mcp/tools/reservation_draft.py` | Sí |
| generate_participant_form_link | `ai/mcp/tools/participant_forms.py` | Sí |
| get_experience_detail | `ai/mcp/tools/__init__.py` | Sí |
| get_participant_form_status | `ai/mcp/tools/participant_forms.py` | Sí |
| get_public_business_rules | `ai/mcp/tools/__init__.py` | Sí |
| get_reservation_public_summary | `ai/mcp/tools/reservation_draft.py` | Sí |
| get_reservation_status_by_phone | `ai/mcp/tools/reservation_draft.py` | Sí |
| guide_create_service_log | `ai/mcp/tools/operations.py` | Sí |
| guide_report_incident | `ai/mcp/tools/operations.py` | Sí |
| list_available_schedules | `ai/mcp/tools/schedules.py` | Sí |
| list_experiences | `ai/mcp/tools/catalog.py` | Sí |
| quote_experience | `ai/mcp/tools/quote.py` | Sí |
| request_human_review | `ai/mcp/tools/__init__.py` | Sí |
| schedule_birthday_automation | `ai/mcp/tools/automations.py` | Sí |
| schedule_visit_anniversary_automation | `ai/mcp/tools/automations.py` | Sí |
| send_post_service_message | `ai/mcp/tools/automations.py` | Sí |
| suggest_alternative_dates | `ai/mcp/tools/schedules.py` | Sí |

## Notas de mantenimiento

- Esta referencia debe actualizarse cuando se agregue/elimine/modifique un tool MCP.
- La fuente de verdad contractual sigue siendo `tool_contracts.py` + `ToolPolicyEngine` + `ToolCallLogDocument`.
- Para detalle narrativo del flujo conversacional, usar `docs/architecture/chatbot-whatsapp-v2.md`.
- Los nombres en `CRITICAL_TOOLS` (`confirm_reservation`, `cancel_reservation`, etc.) nunca se implementaron como tools — existen solo como bloqueo preventivo en `policy.py`. Las tools `admin_confirm_reservation` y `admin_cancel_reservation` son independientes y están funcionando para el canal admin.
