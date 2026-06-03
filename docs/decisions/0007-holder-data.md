# ADR-0007: Datos holder obligatorios pre-reserva

**Fecha:** 2026-06-01  
**Estado:** ✅ Aceptado  

## Contexto

El asistente WhatsApp creaba borradores de reserva sin nombre/email del titular. Esto generaba reservas incompletas que requerían backoffice para completar.

## Decisión

El slot merge del orquestador NUNCA autocompleta `holder_name`/`holder_email` desde la sesión. El bot siempre pregunta estos datos explícitamente antes de llamar a `create_reservation_draft`.

## Consecuencias

- `create_reservation_draft` requiere siempre: experience_id, participant_count, holder_phone, holder_name, holder_email, requested_date, quote_snapshot
- Los slots holder_name/holder_email se excluyen del merge en `merge_slots()`
- Mensajes claros al usuario sobre cada campo requerido
- Menos reservas incompletas en base de datos
