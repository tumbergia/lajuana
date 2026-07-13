# ADR-0010: Política de idioma y entrega de medios de pago del bot de WhatsApp

**Fecha:** 2026-06-25  
**Estado:** ✅ Aceptado

## Contexto

Conversaciones reales del bot expusieron tres problemas:

1. **Idioma inestable.** Tras escribir "sí" el bot respondió en inglés
   ("Great! To move forward with your booking..."). La auto-detección por
   racha (ADR-0010 v1) seguía pudiendo cambiar el idioma del bot; tokens
   neutros o frases cortas en inglés lo desplazaban a inglés aunque el
   usuario no lo hubiera pedido.
2. **Mentiras sobre envío por correo.** El bot decía "te he enviado los
   detalles de pago a tu correo electrónico juan.rendon37632@ucaldas.edu.co"
   pese a que no existe sistema de envío por correo. La información de pago
   debe entregarse **en este mismo chat de WhatsApp**.
3. **Falta раскрыть `includes`.** El usuario preguntó "qué es lo que incluye"
   y la respuesta no mencionó el campo `inclusions.items` de la experiencia.

## Decisión

### 1. Idioma: sólo override explícito

El bot **nace en español y nunca auto-detecta**. El idioma efectivo sólo
cambia por petición explícita del usuario (ej. "respóndeme en inglés"),
materializada con `session.language_override` persistente. La racha de 3
mensajes queda **desactivada**; los campos `language_streak`/
`language_streak_lang` se conservan en el documento por trazabilidad pero no
se usan para cambiar idioma.

Efecto: si el usuario escribe "Great!" o cinco mensajes en inglés, el bot
sigue respondiendo en español hasta que el usuario pida explícitamente otro
idioma o revierta a español.

### 2. Medios de pago por WhatsApp, literal

Se crea la tool `get_payment_instructions`
(`app/ai/mcp/tools/payment_instructions.py`) que entrega los medios de pago
en texto plano, literal, dentro del mismo mensaje de WhatsApp:

```
Medios de pago disponibles:

1. CUENTA AHORROS BANCOLOMBIA
   No. 7165 1544 758
   Jairo Ramírez Londoño
   C.C. No. 10.288.647

2. LINK DE PAGO BOLD
   Debe ser solicitado a LA JUANA ...
   Nota: con el uso de este medio de pago se cargará 7% adicional ...
```

El `TOOL_RESULT_RESPONSE_SYSTEM_PROMPT` ahora prohíbe afirmar envíos por
correo y exige que cuando el tool trae `includes`, el composer lo mencione
breve. Y el orchestrator generaliza el bypass: cualquier tool en
`LITERAL_RESPONSE_TOOLS` (`create_reservation_draft`,
`get_payment_instructions`, `attach_payment_proof_to_reservation`) entrega
su `response` literal sin pasar por `compose_tool_response`, evitando que el
LLM reformule y mienta.

El `intent_router` enruta `detalles de pago`, `cómo pago`, `medios de pago`,
`datos de pago`, `cuenta bancolombia` → `get_payment_instructions`. La
pregunta se prioriza antes que `_DETAIL_KEYWORDS` para no confundirla con
"detalles de una experiencia".

### 3. Bold → enlace fijo configurable

Cualquier mención explícita de pago Bold enruta a `get_payment_instructions`.
La herramienta obtiene de `ConfigService` el enlace HTTPS fijo y la comisión
configurados. Si Bold está inactivo, ofrece únicamente los métodos activos.

### 4. `includes` expuesto

La tool `get_experience_detail` ya devolvía `includes=inclusions.items`.
El `TOOL_RESULT_RESPONSE_SYSTEM_PROMPT` se refuerza para que, cuando el
usuario pregunte qué incluye o pida detalle, el composer mencione la lista
de `includes` de forma breve.

## Alternativas consideradas

- **Mantener auto-detección con umbral 3.** Descartado: el usuario reportó
  que cualquier cambio que él no pidiera es inaceptable, y la racha seguía
  permitiendo saltos no pedidos ante mensajes en inglés aislados.
- **Crear herramienta de email.** Descartado: no existe sistema de envío por
  correo y el usuario debía recibir todo en WhatsApp.
- **Integración transaccional Bold.** Descartada en esta fase: el enlace es fijo
  y la verificación del pago continúa siendo administrativa.

## Consecuencias

- El bot es determinista en español: cambia de idioma sólo a petición.
- Los detalles de pago se entregan por WhatsApp, no se miente sobre correo.
- `includes` aparece en respuestas de detalle/experiencia.
- Bold responde con el enlace fijo configurado, sin inventarlo ni escalarlo.

## Trazabilidad

- `apps/api/app/ai/assistant/orchestrator.py` (política idioma, `LITERAL_RESPONSE_TOOLS`)
- `apps/api/app/ai/assistant/intent_router.py` (Bold → handoff, pago → tool)
- `apps/api/app/ai/assistant/prompts/planner.py` (reglas del composer)
- `apps/api/app/ai/mcp/tools/payment_instructions.py` (tool nueva)
- `apps/api/app/ai/mcp/tools/reservation_draft.py` (`_PAYMENT_STEPS`)
- `apps/api/app/ai/mcp/__init__.py` (registro de `get_payment_instructions`)
- `apps/api/app/channels/whatsapp/normalizer.py` (`strip_whatsapp_markup`)
- `apps/api/app/channels/whatsapp/outbound_service.py` (saneamiento)
- `apps/api/tests/test_language_policy_orchestrator.py`
