# 0007: Datos del titular obligatorios en pre-reserva vía chatbot

## Estado

Aceptado

## Contexto

El chatbot de WhatsApp creaba pre-reservas (`create_reservation_draft`) sin exigir el nombre completo ni el correo electrónico del titular. Esto generaba:

1. Reservas incompletas que luego requerían contacto manual para obtener datos básicos.
2. Imposibilidad de enviar notificaciones por correo al titular.
3. Experiencia del bot cortante, ya que el prompt enfatizaba neutralidad extrema y brevedad sin invitar a continuar la conversación.

Adicionalmente, al aprobar un pago desde la aplicación móvil, el backend intentaba enviar un mensaje de WhatsApp usando el template `payment_approved_form_sent.customer`, pero este template no existía en la base de datos porque el seed no se ejecutaba automáticamente en el arranque de la app.

## Decisión

1. **Hacer obligatorios `holder_name` y `holder_email`** en el flujo de conversación antes de llamar a `create_reservation_draft`.
2. **Actualizar el contrato `CreateReservationDraftInput`** para incluir `holder_email` y propagarlo hasta el servicio `ReservationDraftService`.
3. **Ajustar los prompts del planner** para que el bot mantenga un tono cálido, amable y conversacional, terminando siempre con una pregunta breve o invitación a continuar (salvo en cierre por políticas o `human_handoff`).
4. **Subir la `temperature` del `response_composer`** de `0.4` a `0.6` para generar respuestas más naturales y variadas.
5. **Ejecutar `seed_notification_templates` automáticamente** en el startup de FastAPI (`lifespan`) para garantizar que los templates transaccionales de WhatsApp existan en la base de datos.

## Consecuencias

### Positivas

- El bot recopila datos completos del titular (nombre, teléfono, correo) antes de crear la pre-reserva.
- Se elimina el error `Template payment_approved_form_sent.customer not found` al aprobar pagos.
- El tono del bot es más cercano y conversacional, incitando al usuario a seguir interactuando.
- Mayor trazabilidad: cada pre-reserva tiene correo del titular desde el origen.

### Negativas / Riesgos

- El flujo de conversación se alarga en al menos un turno (se debe pedir el correo). Esto es aceptable porque los datos son necesarios para operar.
- Si el usuario no tiene correo o no quiere darlo, el bot no podrá crear la pre-reserva. En ese caso, el bot puede derivar a `human_handoff`.
- La subida de `temperature` a `0.6` podría generar respuestas ligeramente menos deterministas. Se mitiga con el system prompt que fija las reglas de formato JSON.

## Alternativas consideradas

- **Pedir datos después de la pre-reserva**: Rechazada porque la pre-reserva quedaría incompleta y el sistema de notificaciones por email requeriría un paso adicional manual.
- **Hacer el correo opcional**: Rechazada porque el usuario solicitó explícitamente que sea obligatorio para tener "todos los datos necesarios".
- **Mantener temperatura 0.4**: Rechazada porque las respuestas seguían siendo demasiado robóticas y cortantes.

## Referencias

- `apps/api/app/ai/assistant/orchestrator.py` — `REQUIRED_FIELDS_BY_TOOL`, `FIELD_LABELS`
- `apps/api/app/ai/assistant/prompts/planner.py` — `PLANNER_SYSTEM_PROMPT`, `TOOL_RESULT_RESPONSE_SYSTEM_PROMPT`
- `apps/api/app/ai/assistant/response_composer.py` — `temperature`
- `apps/api/app/ai/mcp/tool_contracts.py` — `CreateReservationDraftInput`
- `apps/api/app/ai/mcp/tools/reservation_draft.py` — tool implementation
- `apps/api/app/services/reservation_draft_service.py` — service persistence
- `apps/api/app/core/lifespan.py` — startup seed
- `apps/api/app/migrations/seed_notification_templates.py` — seed data
