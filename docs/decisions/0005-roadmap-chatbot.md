# Roadmap del asistente AI para La Juana — v2 validado contra tools actuales

**Fecha de actualización:** 2026-05-15  
**Naturaleza del documento:** roadmap estratégico de capacidades, no plan de implementación sprint por sprint.  
**Validado contra:** arquitectura v2 del chatbot, `tools.md`, requerimientos funcionales/no funcionales, cronograma y documentación de arquitectura del proyecto.

## Índice

1. [Propósito](#1-propósito)
2. [Estado actual validado contra tools](#2-estado-actual-validado-contra-tools)
3. [Principios rectores](#3-principios-rectores)
4. [Arquitectura conceptual](#4-arquitectura-conceptual)
5. [Taxonomía: capacidades, tools y componentes internos](#5-taxonomía-capacidades-tools-y-componentes-internos)
6. [Matriz de canales, actores y permisos](#6-matriz-de-canales-actores-y-permisos)
7. [Horizontes de evolución](#7-horizontes-de-evolución)
8. [Dependencias duras entre capacidades](#8-dependencias-duras-entre-capacidades)
9. [Estados conversacionales mínimos](#9-estados-conversacionales-mínimos)
10. [Estados de reserva y relación con tools](#10-estados-de-reserva-y-relación-con-tools)
11. [Política de privacidad frente al LLM](#11-política-de-privacidad-frente-al-llm)
12. [Golden conversation suite](#12-golden-conversation-suite)
13. [Riesgos principales](#13-riesgos-principales)
14. [Criterio de cierre](#14-criterio-de-cierre)

---

## 1. Propósito

Este roadmap define la evolución del asistente AI de La Juana desde un asistente comercial público conectado a WhatsApp hacia una capa conversacional integral para atención, catálogo, disponibilidad, cotización, pre-reserva, soporte post-reserva, administración interna, operación de campo, bienestar equino y analítica.

El documento no es un backlog técnico lineal. Es un mapa de capacidades. Su objetivo es ordenar la evolución del asistente sin romper tres principios:

1. La reserva sigue siendo el eje operativo del sistema.
2. La IA no es fuente de verdad ni autoridad final sobre acciones críticas.
3. Toda acción relevante debe ser trazable, auditable y gobernada por permisos.

La solución debe mantener dos asistentes claramente separados:

| Asistente | Canal principal | Propósito | Restricción central |
|---|---|---|---|
| Asistente público | WhatsApp | Informar, filtrar, listar experiencias, consultar disponibilidad, cotizar y acompañar pre-reserva | No administra negocio ni ejecuta acciones críticas |
| Asistente administrativo | App móvil | Consultar, resumir, preparar acciones y apoyar operación interna | Requiere rol, permisos, preview y auditoría |

La entidad técnica principal seguirá siendo `Reservation`. Conceptualmente, una reserva confirmada equivale al **servicio programado**: experiencia contratada en una fecha específica, asociada a cliente, participantes, pago, activos físicos, logística y ejecución.

---

## 2. Estado actual validado contra tools

El asistente cuenta actualmente con arquitectura v2 basada en pipeline secuencial:

```txt
planner → policy → registry/tool → composer
```

Componentes actuales:

- `POST /api/v1/ask` para pruebas y depuración.
- `POST /api/v1/whatsapp/webhook` para mensajes entrantes desde WhatsApp Cloud API.
- `GeminiPlanner` con salida estructurada.
- `ToolPolicyEngine` para validar confianza, riesgo, argumentos requeridos y tool permitida.
- `ToolRegistry` interno para ejecutar tools desde el orquestador.
- `ResponseComposer` con composición vía LLM.
- `ConversationSessionDocument` para conservar slots conversacionales.
- `ConversationTurnDocument` para registrar cada turno.
- `ToolCallLogDocument` para auditar cada ejecución de tool.

### 2.1 Tools actuales

| Tool | Estado funcional | Registry interno | FastMCP standalone | Contrato Pydantic | Observación |
|---|---:|---:|---:|---:|---:|---|
| `list_experiences` | Implementada | Sí | Sí | Sí (v2) | Contrato formalizado con `ListExperiencesInput/Output`. Expuesta en FastMCP. |
| `check_experience_availability` | Implementada | Sí | Sí | Sí | Correcta como tool read-only. No crea reservas, no bloquea cupos, no confirma disponibilidad final sin backend. |
| `quote_experience` | Implementada | Sí | Sí | Sí | Correcta. `requested_date` opcional agregado al input. |
| `list_available_schedules` | Implementada | Sí | Sí | Sí | Nueva. Lista fechas disponibles en rango de 60 días. |
| `suggest_alternative_dates` | Implementada | Sí | Sí | Sí | Nueva. Sugiere fechas alternativas cuando no hay cupo. |
| `create_reservation_draft` | Implementada | Sí | Sí | Sí | Crea pre-reserva con `quote_snapshot` y respuesta con instrucciones de pago configurables. |
| `attach_payment_proof_to_reservation` | Implementada | Sí | Sí | Sí | Adjunta comprobante en estado `under_review`/`duplicate`; no valida pago. |
| `get_reservation_public_summary` | Implementada | Sí | Sí | Sí | Resumen seguro de reserva por código + holder_phone. |
| `get_reservation_status_by_phone` | Implementada | Sí | Sí | Sí | Consulta estado por teléfono del titular. |
| `get_experience_detail` | Stub | Sí | Sí | Sí | Stub que retorna no encontrado. Implementación real pendiente. |
| `get_public_business_rules` | Stub | Sí | Sí | Sí | Stub que retorna datos vacíos. Implementación real pendiente. |
| `request_human_review` | Stub | Sí | Sí | Sí | Stub funcional que crea solicitud. Integración real pendiente. |

### 2.2 Tools permitidas por policy actualmente

| Clasificación | Tools | Estado |
|---|---|---|---|
| `READ_TOOLS` | `list_experiences`, `get_experience_detail`, `get_public_business_rules`, `check_experience_availability`, `list_available_schedules`, `quote_experience`, `suggest_alternative_dates`, `get_reservation_public_summary`, `get_reservation_status_by_phone` | Permitidas si pasan validación de argumentos, confianza y riesgo |
| `LIMITED_WRITE_TOOLS` | `request_human_review`, `create_reservation_draft`, `attach_payment_proof_to_reservation` | Escritura limitada (handoff, pre-reserva y adjunto de comprobante) |
| `WRITE_TOOLS` | Ninguna | Vacío intencionalmente |
| `CRITICAL_TOOLS` | `confirm_reservation`, `cancel_reservation`, `mark_payment_verified`, `change_schedule_capacity`, `block_slots` | Denegadas preventivamente |

### 2.3 Limitación explícita actual

El asistente actual no debe:

- crear reservas confirmadas;
- validar pagos;
- aprobar comprobantes;
- modificar cupos;
- confirmar disponibilidad final por inferencia del modelo;
- exponer datos sensibles al prompt;
- ejecutar acciones críticas desde WhatsApp público.

### 2.4 Brechas inmediatas detectadas

| Brecha | Impacto | Estado |
|---|---|---|---|
| `list_experiences` no tiene contrato Pydantic formal | Rompe consistencia con el resto de tools | **Resuelta** — `ListExperiencesInput/Output` creados. |
| `list_experiences` no está expuesta en FastMCP standalone | Diferencia entre registry interno y servidor MCP | **Resuelta** — Expuesta en FastMCP. |
| `quote_experience` devuelve `requested_date` pero el input documentado no lo incluye | Contrato ambiguo | **Resuelta** — `requested_date` opcional agregado a `QuoteExperienceInput`. |
| Arquitectura v2 puede quedar desactualizada frente a `quote_experience` | Documentación contradictoria | **Resuelta** — `chatbot-whatsapp-v2.md` y `tools.md` actualizados. |
| No existe todavía `list_available_schedules` | Brecha comercial fuerte | **Resuelta** — Implementada y registrada. |
| No existe `request_human_review` | Handoff aún informal | **Resuelta (stub)** — Registrada como LIMITED_WRITE_TOOL. Integración real pendiente. |

---

## 3. Principios rectores

### 3.1 La IA no es fuente de verdad

La IA puede planificar, redactar, resumir y guiar. No puede validar pagos, confirmar reservas, modificar cupos, aprobar disponibilidad ni cambiar estados críticos.

La verdad operativa viene de:

- `services/`;
- `documents/`;
- validaciones de dominio;
- contracts Pydantic;
- policy engine;
- estado persistido en MongoDB.

### 3.2 La reserva es el eje operativo

Cuando existe intención comercial concreta, todo debe converger hacia una reserva o pre-reserva trazable. La reserva conecta:

- cliente titular;
- canal de origen;
- experiencia;
- fecha operativa;
- participantes estimados o reales;
- cotización;
- pago/comprobante;
- confirmación;
- formularios;
- pólizas;
- logística;
- asignaciones;
- bitácora;
- post-servicio.

### 3.3 WhatsApp público no administra el negocio

WhatsApp puede informar, filtrar, cotizar, consultar disponibilidad y crear solicitudes limitadas cuando exista diseño de pre-reserva. No puede validar pagos, cerrar cupos, cancelar servicios, modificar fechas operativas ni exponer datos sensibles.

### 3.4 App móvil administrativa sí puede operar, pero con permisos

La app móvil es el canal natural para operación interna y administración. El asistente administrativo debe entrar primero como lectura y resumen. La escritura asistida debe requerir preview, permisos, confirmación explícita e idempotencia.

### 3.5 Toda tool estable debe ser tipada

Una tool estable debe tener:

- input Pydantic;
- output Pydantic;
- errores estructurados;
- `trace_id`;
- logging en `ToolCallLogDocument`;
- clasificación de riesgo;
- policy explícita;
- owner de negocio o servicio dueño.

---

## 4. Arquitectura conceptual

```txt
HTTP / WhatsApp
  → api/endpoints
  → channels/whatsapp normalizer
  → ai/assistant/orchestrator
      → session load/create
      → ConversationTurn insert
      → GeminiPlanner
      → slot merge
      → ToolPolicyEngine
      → ToolRegistry / MCP tool
      → ToolCallLog
      → ResponseComposer
      → ConversationTurn complete
  → WhatsApp sender / AskResponse
```

Responsabilidades por capa:

| Capa | Responsabilidad | Qué NO debe hacer |
|---|---|---|
| `api/endpoints/` | Exponer HTTP | Lógica de negocio |
| `channels/` | Traducir payloads externos | Decidir negocio |
| `ai/assistant/` | Orquestar conversación, policy y respuesta | Validar disponibilidad real o pagos |
| `ai/providers/` | Conectar con Gemini u otro LLM | Saber de reservas o pagos |
| `ai/mcp/` | Exponer tools al asistente | Duplicar reglas de negocio |
| `services/` | Validar dominio y negocio | Redactar conversación |
| `documents/` | Persistencia y trazabilidad | Tomar decisiones |

---

## 5. Taxonomía: capacidades, tools y componentes internos

El roadmap distingue tres categorías.

### 5.1 Capacidad

Una capacidad es algo que el sistema permite hacer desde la perspectiva del negocio.

Ejemplos:

- consultar catálogo;
- cotizar experiencia;
- consultar disponibilidad;
- crear pre-reserva;
- adjuntar comprobante;
- consultar pendientes administrativos.

### 5.2 Tool MCP / Tool del assistant

Una tool es una operación invocable por el orquestador. Debe tener contrato, policy y logging.

Ejemplos actuales:

- `list_experiences`;
- `check_experience_availability`;
- `quote_experience`.

### 5.3 Componente interno

Un componente interno no debe aparecer como tool para el modelo. Es infraestructura o helper.

No deben modelarse como tools:

- `resolve_actor_context`;
- `validate_tool_access`;
- `classify_tool_risk`;
- `require_human_confirmation`;
- `deny_critical_public_action`;
- `log_tool_call`;
- `format_schedule_options`;
- `explain_quote_disclaimer`;
- `explain_availability_block`.

Deben vivir como:

- `ToolContextResolver`;
- `ToolPolicyEngine`;
- instrumentación del `ToolRegistry`;
- helpers del `ResponseComposer`;
- servicios de dominio.

### 5.4 Estados de una tool en el roadmap

| Estado | Significado |
|---|---|
| `planned` | Existe en roadmap, no en código |
| `registry` | Existe en `ToolRegistry` y funciona desde `/ask` / WhatsApp |
| `mcp_standalone` | También está expuesta en el servidor FastMCP |
| `deprecated` | Existía pero debe retirarse o migrarse |

Toda tool pública estable debe llegar como mínimo a `registry`. Si se quiere consumir desde clientes MCP externos, debe llegar también a `mcp_standalone`.

---

## 6. Matriz de canales, actores y permisos

| Capacidad | WhatsApp público | App admin | Guía | Sistema |
|---|---:|---:|---:|---:|
| Ver catálogo | Sí | Sí | Sí | Sí |
| Ver detalle de experiencia | Sí | Sí | Sí | Sí |
| Consultar reglas públicas | Sí | Sí | Sí | Sí |
| Consultar disponibilidad | Sí | Sí | Sí limitado | Sí |
| Cotizar | Sí | Sí | No necesario | Sí |
| Crear pre-reserva | Sí, limitada | Sí | No | Sí, bajo reglas |
| Consultar estado propio | Sí, limitado por teléfono | Sí | No | Sí |
| Adjuntar comprobante | Sí, limitado | Sí | No | Sí |
| Validar pago | No | Admin crítico | No | Solo integración confiable |
| Confirmar reserva | No | Admin crítico | No | Sí, si reglas completas |
| Ver datos médicos | No | Admin autorizado | Guía limitado y necesario | No por defecto |
| Enviar formulario | Sí, sistema | Sí | No | Sí |
| Crear bitácora | No | Sí | Sí | Sí |
| Ver carga equina | No | Sí | Sí limitado | Sí |
| Cambiar cupos/capacidad | No | Admin crítico | No | Sí, con reglas |

---

## 7. Horizontes de evolución

## Horizonte 0 — Fundamento AI seguro

### Objetivo

Estabilizar la arquitectura conversacional antes de permitir escritura. El foco es que el asistente no mezcle usuarios, no duplique respuestas, no ejecute tools indebidas y deje trazabilidad completa.

### Capacidades

| Capacidad | Estado | Observación |
|---|---:|---:|---|
| Pipeline planner → policy → tool → composer | Implementado | Base actual de la v2 |
| Sesiones conversacionales con slots | Implementado / fortalecer | Debe formalizar estados conversacionales |
| ToolCallLog por ejecución | Implementado | Incluye trace_id y latencia |
| Slot merge tool-aware (`REQUIRED_FIELDS_BY_TOOL`) | Implementado | merge_slots() con required_fields por tool |
| Deduplicación WhatsApp por `external_message_id` | Pendiente | Crítico antes de escritura |
| Lock por `conversation_key` | Pendiente | Crítico para evitar respuestas entrelazadas |
| Debounce/batching de mensajes cortos | Pendiente | Necesario para usuarios que escriben en varios mensajes |
| Contratos Pydantic para todas las tools | Completado | Todas las tools públicas tienen contrato Pydantic |
| Simetría registry/FastMCP | Completado | Todas las tools expuestas en registry y FastMCP |

### Criterio de salida

- 100 conversaciones de prueba sin mezcla de usuarios.
- 0 mensajes duplicados procesados dos veces.
- 0 tool calls sin `trace_id`.
- 0 turns sin `planner_output`.
- Todas las tools públicas tienen contrato Pydantic o deuda explícitamente documentada.
- `/ask` y WhatsApp usan el mismo orquestador.

---

## Horizonte 1 — MVP comercial público

### Objetivo

Permitir que un cliente por WhatsApp pueda entender qué ofrece La Juana, consultar opciones, pedir disponibilidad, cotizar y recibir alternativas sin que el sistema cree reservas ni toque pagos.

### Tools / capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---:|---|---|
| `list_experiences` | Implementada | Pública lectura | Contrato Pydantic + FastMCP |
| `get_experience_detail` | Stub | Pública lectura | Stub en registry/FastMCP. Implementación real pendiente |
| `get_public_business_rules` | Stub | Pública lectura | Stub en registry/FastMCP. Implementación real pendiente |
| `check_experience_availability` | Implementada | Pública lectura | Tool operativa actual |
| `list_available_schedules` | Implementada | Pública lectura | Rango 60 días, filtro por cupo |
| `quote_experience` | Implementada | Pública lectura | `requested_date` opcional alineado |
| `suggest_alternative_dates` | Implementada | Pública lectura | ±15/30 días, exclude_dates |
| `request_human_review` | Implementada (stub) | Escritura limitada | Stub funcional en LIMITED_WRITE_TOOLS |

### Criterio de salida

- Cliente pregunta “qué ofrecen” y recibe catálogo desde base de datos.
- Cliente pregunta “cuánto vale X para N personas” y recibe cotización desde `quote_experience`.
- Cliente pregunta “hay cupo X fecha” y recibe disponibilidad desde `check_experience_availability`.
- Cliente pregunta “qué fechas tienen” y recibe opciones reales desde `list_available_schedules`.
- Si no hay cupo, el sistema propone fechas alternativas.
- Ninguna respuesta inventa precio, cupo, duración ni confirmación.

---

## Horizonte 2 — Pre-reserva trazable

### Objetivo

Convertir una conversación viable en una reserva no confirmada, con snapshot comercial y trazabilidad de origen.

### Capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---|---|
| `create_reservation_draft` | Implementada | Pública escritura limitada | No confirma reserva ni descuenta cupos |
| `get_reservation_public_summary` | Implementada | Pública lectura limitada | Resumen seguro para cliente (código + holder_phone) |
| `get_reservation_status_by_phone` | Implementada | Pública lectura limitada | Solo reservas asociadas al teléfono |
| `expire_reservation_draft` | Implementada | Sistema | Expira borradores de reserva sin avance |
| `quote_snapshot` | Implementada | Persistencia | Obligatorio antes de crear `create_reservation_draft` |

### Regla de diseño

`create_reservation_draft` debe crear una reserva en estado no confirmado. Debe guardar:

- experiencia;
- fecha;
- participantes estimados;
- teléfono/canal de origen;
- quote snapshot;
- tool_call_id de origen;
- trace_id;
- estado inicial permitido.

### Criterio de salida

- Todo `create_reservation_draft` tiene `quote_snapshot`.
- Todo `create_reservation_draft` tiene canal de origen y trace.
- No se descuentan cupos.
- No se confirma pago.
- No se confirma reserva.

---

## Horizonte 3 — Pago, confirmación y post-reserva inmediato

### Objetivo

Recibir comprobantes, permitir revisión administrativa y confirmar reservas solo con backend, pago verificado y disponibilidad vigente.

### Capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---|---|
| `attach_payment_proof_to_reservation` | Implementada | Pública escritura limitada | Recibe evidencia y la deja en revision (`under_review`/`duplicate`) |
| `get_payment_proof_public_status` | Planned | Pública lectura limitada | Estado agregado: recibido/en revisión |
| `admin_get_payment_proof` | Implementada (API) | Admin lectura | `GET /api/v1/payment-proofs/{payment_proof_id}` |
| `admin_verify_payment_proof` | Implementada (API) | Admin crítica | `POST /api/v1/payment-proofs/{payment_proof_id}/verify` |
| `admin_reject_payment_proof` | Implementada (API) | Admin crítica | `POST /api/v1/payment-proofs/{payment_proof_id}/reject` con motivo |
| `admin_confirm_reservation` | Implementada (API) | Admin crítica | `POST /api/v1/reservations/{reservation_id}/confirm`; exige pago verificado y commit atómico de cupo |
| `send_reservation_confirmation` | Planned | Sistema | Mensaje formal post-confirmación |

### Regla de diseño

`attach_payment_proof_to_reservation` nunca debe marcar pago como verificado. Solo debe dejar el comprobante como recibido o en revisión.

### Criterio de salida

- Cliente puede enviar comprobante.
- Admin puede aprobar/rechazar comprobante.
- Confirmar reserva exige pago verificado y disponibilidad vigente.
- Confirmar reserva descuenta cupos en backend.
- Toda transición queda auditada.

---

## Horizonte 4 — Participantes, formularios y datos sensibles

### Objetivo

Recolectar datos obligatorios de participantes de forma segura, evitando exponer información sensible por WhatsApp o prompt LLM.

### Capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---|---|
| `generate_participant_form_link` | Planned | Sistema | Link seguro, versionado y trazable |
| `send_participant_form_link` | Planned | Sistema/Pública | Se envía después de confirmación |
| `get_participant_form_status` | Planned | Pública lectura limitada | Solo estado agregado |
| `admin_get_missing_participant_fields` | Planned | Admin lectura | Campos faltantes, con permisos |
| `send_participant_form_reminder` | Planned | Sistema/Admin | Recordatorios configurables |

### Criterio de salida

- El cliente no entrega datos sensibles directamente al chatbot.
- WhatsApp solo informa estado agregado.
- Admin puede revisar faltantes con permisos.
- Guía recibe únicamente datos operativos necesarios.

---

## Horizonte 5 — Asistente administrativo de lectura

### Objetivo

Introducir asistente en app móvil sin riesgo de escritura. Primero debe consultar, resumir y filtrar.

### Capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---|---|
| `admin_search_global` | Planned | Admin lectura | Buscar entidades autorizadas |
| `admin_get_today_summary` | Planned | Admin lectura | Operación del día |
| `admin_get_pending_tasks` | Planned | Admin lectura | Pagos, formularios, pólizas, asignaciones |
| `admin_get_reservation_detail` | Planned | Admin lectura | Detalle autorizado |
| `admin_generate_operational_summary` | Planned | Admin lectura | Resumen operativo desde datos estructurados |
| `guide_get_service_briefing` | Planned | Guía lectura | Briefing limitado para campo |

### Criterio de salida

- Admin puede consultar operación sin modificar datos.
- Guía puede ver briefing limitado.
- No se exponen datos sensibles innecesarios.
- Todo acceso queda auditado.

---

## Horizonte 6 — Escritura asistida administrativa

### Objetivo

Permitir creación/actualización asistida con preview, confirmación explícita e idempotencia.

### Capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---|---|
| `admin_prepare_create_entity` | Planned | Admin escritura asistida | Prepara, no ejecuta |
| `admin_prepare_update_entity` | Planned | Admin escritura asistida | Devuelve diff/preview |
| `admin_execute_prepared_action` | Planned | Admin escritura | Ejecuta acción confirmada |
| `admin_discard_prepared_action` | Planned | Admin escritura | Descarta acción |
| `admin_prepare_critical_action` | Planned | Admin crítica | Prepara acción sensible |
| `admin_confirm_critical_action` | Planned | Admin crítica | Ejecuta tras confirmación explícita |

### Criterio de salida

- Ninguna escritura ocurre por inferencia directa del modelo.
- Toda escritura tiene preview.
- Toda escritura tiene actor y permisos.
- Toda escritura tiene idempotency key.
- Toda escritura crítica tiene confirmación explícita.

---

## Horizonte 7 — Operación de campo y bienestar equino

### Objetivo

Conectar la reserva confirmada con ejecución en campo, bitácora, asignaciones y bienestar equino.

### Capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---|---|
| `admin_get_logistics_checklist` | Planned | Admin/Guía lectura | Checklist por reserva/experiencia |
| `guide_create_service_log` | Planned | Guía escritura | Bitácora offline-first |
| `guide_report_incident` | Planned | Guía crítica | Incidentes con severidad |
| `admin_close_service_execution` | Planned | Admin crítica | Cierre operativo |
| `admin_add_equine_health_event` | Planned | Admin escritura | Salud/bienestar |
| `admin_get_equine_workload` | Planned | Admin lectura | Carga de trabajo |
| `admin_update_equine_availability` | Planned | Admin crítica | Cambia disponibilidad operacional |

### Criterio de salida

- Operación puede ver briefing antes de salida.
- Guía puede registrar bitácora incluso con mala conectividad.
- Incidentes quedan asociados a reserva/equino/participante si aplica.
- Carga de trabajo equina se consulta antes de asignaciones críticas.

---

## Horizonte 8 — Analítica, reportes y automatizaciones

### Objetivo

Convertir datos operativos en decisiones: embudo comercial, ocupación, canales, carga equina, proveedores, incidentes y post-servicio.

### Capacidades

| Tool o capacidad | Estado | Tipo | Comentario |
|---|---:|---|---|
| `admin_get_sales_summary` | Planned | Admin lectura | Ventas/reservas/pagos |
| `admin_get_reservation_funnel` | Planned | Admin lectura | Conversión por estado |
| `admin_get_channel_performance` | Planned | Admin lectura | Canales de entrada |
| `admin_get_occupancy_report` | Planned | Admin lectura | Ocupación por fecha/experiencia |
| `admin_get_equine_workload_report` | Planned | Admin lectura | Carga equina |
| `send_post_service_message` | Planned | Sistema | Agradecimiento/reseñas |
| `schedule_birthday_automation` | Planned | Sistema/Admin | Fidelización |
| `schedule_visit_anniversary_automation` | Planned | Sistema/Admin | Fidelización |

### Criterio de salida

- Admin puede ver embudo comercial.
- Admin puede ver ocupación y carga operativa.
- Automatizaciones son configurables y auditables.
- Post-servicio se ejecuta por reglas, no por improvisación del modelo.

---

## 8. Dependencias duras entre capacidades

| Capacidad | Depende de | Motivo |
|---|---|---|
| `create_reservation_draft` | disponibilidad estable, cotización estable, `quote_snapshot`, deduplicación WhatsApp, locks por conversación | Evitar duplicados, inconsistencias y reservas sin trazabilidad |
| `attach_payment_proof_to_reservation` | reserva no confirmada existente, file upload estable, asociación reserva ↔ comprobante | Comprobante debe tener entidad destino |
| `admin_verify_payment_proof` | auth/roles, comprobante existente, confirmación explícita | Acción financiera crítica |
| `admin_confirm_reservation` | pago verificado, disponibilidad revalidada, transición de estado válida, descuento atómico | Evitar sobreventa y falsa confirmación |
| `send_participant_form_link` | reserva confirmada, formulario versionado, link seguro | No pedir datos sensibles sin reserva confirmada |
| asistente admin escritura | auth/roles, ToolContext, preview, idempotency | Evitar cambios destructivos por inferencia |
| guía en campo | app offline-first, sync, permisos de guía, datos mínimos operativos | Operación rural con conectividad pobre |

---

## 9. Estados conversacionales mínimos

`ConversationSessionDocument` no debe ser solo un diccionario de slots. Debe tener estado conversacional explícito.

Estados sugeridos:

| Estado | Significado |
|---|---|
| `idle` | Sin flujo activo |
| `catalog_exploration` | Usuario revisa experiencias |
| `collecting_availability_fields` | Faltan fecha, personas o experiencia |
| `availability_checked` | Ya se consultó disponibilidad |
| `quote_requested` | Usuario pidió precio/cotización |
| `quote_ready` | Cotización generada |
| `draft_ready_to_create` | Hay datos mínimos para crear pre-reserva |
| `waiting_payment_instructions` | Pre-reserva creada y cliente debe pagar |
| `payment_under_review` | Comprobante recibido, pendiente revisión |
| `handoff_requested` | Caso escalado a humano |
| `closed` | Conversación cerrada o vencida |

Regla: el planner puede sugerir el próximo paso, pero el orquestador debe actualizar estado solo si el backend valida la transición.

---

## 10. Estados de reserva y relación con tools

Estados base recomendados:

| Estado | Descripción | Quién puede entrar ahí |
|---|---|---|
| `contact` | Contacto inicial registrado | sistema / assistant público |
| `quoted` | Hay cotización asociada | assistant público / admin |
| `pending_payment` | Cliente recibió instrucciones de pago | assistant público / admin |
| `payment_received` | Comprobante recibido, no verificado | assistant público / admin |
| `confirmed` | Pago validado y cupo descontado | admin crítico / backend |
| `cancelled` | Reserva cancelada | admin crítico |
| `completed` | Servicio ejecutado y cerrado | admin crítico / sistema |

Relación con tools:

| Tool | Puede crear/transicionar estado | Estado permitido | Restricción |
|---|---:|---|---|
| `quote_experience` | No | Ninguno | Solo calcula precio |
| `check_experience_availability` | No | Ninguno | Solo consulta cupo |
| `create_reservation_draft` | Sí | `contact` / `quoted` / `pending_payment` | No confirma |
| `attach_payment_proof_to_reservation` | Sí | `payment_received` | No valida pago |
| `admin_verify_payment_proof` | Sí | estado interno de pago verificado | Admin crítico |
| `admin_confirm_reservation` | Sí | `confirmed` | Revalida disponibilidad y descuenta cupos |
| `admin_cancel_reservation` | Sí | `cancelled` | Requiere motivo y permisos |

---

## 11. Política de privacidad frente al LLM

El asistente no debe inyectar datos sensibles al modelo salvo justificación estricta y minimización explícita.

Datos que no deben enviarse al LLM por defecto:

- número de documento;
- fecha de nacimiento;
- datos médicos;
- EPS;
- tipo de sangre;
- condiciones funcionales;
- contacto de emergencia;
- comprobante completo;
- referencias bancarias sensibles;
- datos completos de participantes;
- información veterinaria sensible no necesaria para el turno.

Respuestas públicas sobre participantes deben ser agregadas:

- “faltan 2 participantes por completar formulario”;
- “faltan datos médicos obligatorios”;
- “el formulario está completo”;
- “el comprobante está recibido y en revisión”.

No se debe exponer por WhatsApp:

- datos médicos de participantes;
- documentos;
- datos de terceros;
- comprobantes completos;
- información administrativa interna.

---

## 12. Golden conversation suite

Estas conversaciones deben convertirse en pruebas de regresión funcional.

| Caso | Esperado |
|---|---|
| “qué ofrecen” | Usa `list_experiences`, no inventa catálogo |
| “cuánto vale medio día para 4” | Usa `quote_experience` |
| “hay cupo para 4 el 20 de junio” | Usa `check_experience_availability` si tiene experiencia o pide aclaración si falta |
| “qué fechas tienen para 4” | Debe usar `list_available_schedules` cuando exista |
| “quiero reservar” | Pide datos mínimos, no crea reserva sin contexto |
| “quiero reservar medio día para 4 el 20 de junio” | Consulta disponibilidad primero |
| “listo, separémela” | Solo crea pre-reserva cuando exista flujo implementado y datos mínimos |
| “ya pagué” | No valida pago; pide/recibe comprobante o escala |
| “quiero tomar y hacer fiesta” | Filtra según reglas comerciales familiares |
| “quiero cancelar” | Handoff o flujo protegido, no cancela por WhatsApp público |
| “me accidenté” | `human_handoff` inmediato |
| “faltan datos de participantes” | Responde estado agregado, no expone datos sensibles |

---

## 13. Riesgos principales

| Riesgo | Descripción | Mitigación |
|---|---|---|
| Scope creep | Intentar construir todo antes de cerrar MVP comercial | Trabajar por horizontes y criterios de salida |
| Tool sprawl | Convertir helpers internos en MCP tools | Mantener taxonomía estricta |
| Desalineación registry/FastMCP | Una tool funciona en `/ask` pero no en MCP standalone | Matriz de exposición por tool |
| Privacidad insuficiente | Datos sensibles entran al prompt o WhatsApp | Política de minimización y masking |
| Pre-reservas duplicadas | Mensajes repetidos o múltiples turnos crean duplicados | Idempotency key, deduplicación y locks |
| Confirmación insegura | Reserva confirmada sin pago o cupo real | Acción crítica solo backend/admin |
| Catálogo débil | Gemini entiende intención pero resolver falla | `ExperienceCatalogResolver`, aliases, tests |
| Quote sin snapshot | Precio ofrecido no queda auditado | `quote_snapshot` obligatorio en pre-reserva |
| WhatsApp entrelazado | Respuestas de usuarios se mezclan | Lock por `conversation_key` |
| Roadmap como backlog infinito | Demasiadas tools sin prioridad | Horizontes y criterios de salida |

---

## 14. Criterio de cierre

Este roadmap se considera correctamente encaminado cuando:

1. El asistente público puede responder catálogo, disponibilidad y cotización sin inventar datos.
2. Todas las tools actuales están tipadas y documentadas.
3. `ToolRegistry` y FastMCP no tienen discrepancias no justificadas.
4. La sesión conversacional conserva slots y estado sin mezclar usuarios.
5. Toda tool call tiene `trace_id`, input, output, estado y latencia.
6. WhatsApp tiene deduplicación y bloqueo por conversación antes de cualquier escritura.
7. La pre-reserva guarda snapshot de cotización y canal de origen.
8. El LLM no recibe datos sensibles innecesarios.
9. Las acciones críticas están fuera del canal público.
10. La evolución posterior sigue horizontes, no una lista caótica de tools.

---

## Próxima acción recomendada

Brechas resueltas (documentación y tools alineadas):

1. ✅ `ListExperiencesInput` y `ListExperiencesOutput` creados.
2. ✅ `list_experiences` expuesta en FastMCP.
3. ✅ `requested_date` opcional agregado a `QuoteExperienceInput`.
4. ✅ Documentación de arquitectura v2 y tools actualizada.
5. ⬜ Implementar pruebas golden para catálogo, disponibilidad y cotización.
6. ✅ `list_available_schedules` implementada.

Próximas prioridades:
- Implementar `get_experience_detail` real (no stub).
- Implementar `get_public_business_rules` real (no stub).
- Integrar `request_human_review` con sistema de tickets/bandeja.
- Implementar deduplicación WhatsApp y lock por conversación.
