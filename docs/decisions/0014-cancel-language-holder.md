# ADR-0014: Idioma del mensaje de cancelación/modificación = `holder_language`

**Fecha:** 2026-07-15  
**Estado:** ✅ Aceptado  
**Complementa:** [0010 — Política de idioma del bot](0010-bot-language-policy.md)

## Contexto

El bot de WhatsApp responde en `session.language` (idioma efectivo de la
conversación actual). Sin embargo, las **respuestas sobre una reserva
específica** (cancelación, modificación de fecha, modificación de
participantes) deben estar en el idioma en que el cliente **hizo** la
reserva, no en el idioma de la conversación actual.

**Escenario real reportado:** un cliente hace una reserva en inglés
(`holder_language="en"`), luego en una sesión posterior le dice al bot
"respóndeme en español" o simplemente continúa en español. Cuando el
cliente dice "cancelar mi reserva PR-XXXX", el bot le respondía en
español (idioma de la sesión actual), no en inglés (idioma de la
reserva). Esto genera:

1. **Inconsistencia de contexto:** el cliente recibe un mensaje en
   español sobre una reserva creada en inglés, con un código
   (`PR-XXXX`) y un nombre (`holder_name`) que pueden no significar
   nada en ese idioma.
2. **Confusión operativa:** si el cliente guarda el mensaje para
   referencia futura, queda en un idioma distinto al contrato original.
3. **Riesgo de soporte:** un humano que lea el historial ve la
   reserva creada en un idioma y la cancelación en otro, sin saber cuál
   es el "oficial".

## Decisión

Las tools de cliente que **operan sobre una reserva existente**
(`cancel_reservation`, `update_reservation_date`,
`update_reservation_participants`) deben responder en
`reservation.holder_language` (el idioma con que se creó la reserva),
no en `session.language` (el idioma de la conversación actual).

### Política de fallback

```
response_lang = reservation.holder_language or session.language
```

Si la reserva no tiene `holder_language` (caso legacy de reservas
anteriores a este ADR), se usa `session.language` como fallback. Esto
asegura que el cliente siempre recibe un mensaje en algún idioma
soportado, sin romper reservas existentes.

### Por qué NO auto-detectar

ADR-0010 establece que el bot **no auto-detecta** el idioma del
mensaje del usuario. El idioma efectivo solo cambia por petición
explícita. Esta decisión es **consistente** con ADR-0010: tampoco
auto-detectamos el idioma al generar respuestas sobre una reserva;
usamos el idioma contractual de la reserva.

### Por qué NO seguir `session.language`

El `session.language` refleja la conversación **actual**, no la reserva
sobre la que se opera. Una misma reserva puede ser cancelada desde
distintas conversaciones (cliente en español, luego admin en español,
luego cliente en inglés). El idioma de la respuesta debe ser estable
por reserva, no por sesión.

### Tools afectadas

- `app.ai.mcp.tools.client_reservations.cancel_reservation` — respuesta
  de éxito, de error (ya pagada), de error (reserva no encontrada)
- `app/ai/mcp/tools/client_reservations.update_reservation_date` —
  respuesta de éxito, de error (estado terminal), de error (pagada)
- `app/ai/mcp/tools/client_reservations.update_reservation_participants`
  — respuesta de éxito, de error (estado terminal), de error (pagada)

### Tools NO afectadas (justificación)

- `create_reservation_draft` — la reserva NO existe aún; se usa
  `session.language` para los mensajes de pedir datos al cliente.
- `attach_payment_proof_to_reservation` — usa el idioma de la sesión
  (el cliente está hablando AHORA con el bot, no revisando la
  reserva histórica).
- `check_availability_and_quote` — la reserva no existe; se usa
  `session.language`.
- `get_payment_instructions` — depende del contexto de la sesión
  actual (cliente preguntando cómo pagar).

## Nota sobre el "mensaje duplicado" reportado

El usuario también reportó que al cancelar se enviaba el mensaje 2
veces. La causa raíz está en las tools de **admin**:

- `cancel_reservation` (cliente) ya pasa `notify_client=False` al
  servicio, por lo que **no** se encola una notificación por outbox
  (sin duplicado).
- `admin_cancel_reservation` y los endpoints HTTP `POST /reservations/{id}/cancel`
  y `DELETE /reservations/cancel-by-client` **no** pasan
  `notify_client=False`. Estos encolan una notificación WhatsApp via
  outbox que se envía independientemente de la respuesta del endpoint,
  generando un segundo mensaje al cliente.

Sin embargo, los admins no usan el bot por WhatsApp (el canal
WhatsApp está mapeado a rol `client`, no `admin`), por lo que en
conversaciones de WhatsApp **no se debería ver el duplicado**. Si
algún usuario lo reportó, lo más probable es:

1. Un admin canceló vía panel admin (no bot).
2. O un race condition entre el bot y el outbox (no reproducible en
   condiciones normales).

**Acción:** dejar `notify_client=False` en el path del bot (ya está) y
NO cambiar el path admin. Si se confirma el duplicado en producción,
investigar logs del outbox worker para ver si la entrada
`RESERVATION_CANCELLED` se está enviando a un `conversation_id` que
también recibe el bot.

## Consecuencias

- Cancelación/modificación de reserva: respuesta siempre en el idioma
  contractual de la reserva.
- Si la reserva no tiene `holder_language` (legacy): fallback a
  `session.language`. No rompe nada.
- Mensajes pre/post-cancelación (ej. "Listo, tu reserva X ha sido
  cancelada") van en el idioma de la reserva.
- Errores de validación (ej. "Solo se pueden cancelar reservas con
  pago pendiente") también en el idioma de la reserva.
- Tests: `tests/test_client_reservations_language.py` (4 tests).
- ADR relacionado: 0010 (política de idioma), 0013 (STT multilingüe).

## Trazabilidad

- `apps/api/app/ai/mcp/tools/client_reservations.py` — `response_lang`
  en `cancel_reservation`, `update_reservation_date`,
  `update_reservation_participants`.
- `apps/api/tests/test_client_reservations_language.py` — tests del
  comportamiento.
- `docs/decisions/0014-cancel-language-holder.md` — este ADR.
