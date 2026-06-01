# ADR: Cancelación de reservas con notificación automática por WhatsApp y self-cancel del cliente

## Contexto

El sistema de reservas necesitaba dos capacidades que no existían:

1. Que un administrador pueda cancelar una reserva desde la app mobile y que el cliente reciba automáticamente una notificación por WhatsApp informando la cancelación.
2. Que el titular de una reserva pueda cancelarla por su propia cuenta, pero solo si aún no ha realizado el pago (estado de pago pendiente).

## Decisión

### Backend

- Se agregó el evento de notificación `RESERVATION_CANCELLED` al enum `NotificationEventType`.
- Se creó un template de WhatsApp transaccional (`reservation_cancelled.customer`) con un mensaje cordial y humano, usando las variables `customer_name`, `reservation_code` y `experience_name`.
- Se implementó `send_reservation_cancelled(...)` en `ReservationWhatsAppNotificationService`, siguiendo el mismo patrón determinístico que ya usan `send_payment_approved_participant_form`, `send_payment_rejected`, etc. (sin pasar por el chatbot).
- Se modificó `ReservationService.cancel_reservation(...)` para que, después de guardar el estado `CANCELLED`, dispare el envío de WhatsApp de forma **best-effort** (fallos en el envío no afectan la cancelación).
- Se creó un endpoint **público** `POST /api/v1/reservations/self-cancel` que permite al titular de una reserva cancelarla sin autenticación de admin, validando:
  - Que la reserva exista (`reservation_code` + `holder_phone`).
  - Que el pago esté en estado `PENDING`.
  - Que la transición de estado sea válida (ya la valida `transition_status`).

### Mobile

- Se habilitó el botón "Cancelar reserva" en la pestaña **Resumen** del detalle de reserva, visible solo para **admin** y cuando la reserva no está en estado terminal.
- Se agregó estado de carga (`cancellationState`), diálogo de confirmación (`AppConfirmDialog`) y retroalimentación por `SnackBar` siguiendo el patrón de `confirmReservation`.
- Se corrigieron los labels del diálogo de confirmación para que el botón destructivo diga **"Confirmar cancelación"** y el botón secundario diga **"Volver"**.

## Consecuencias

- El admin puede cancelar reservas desde el mobile y el cliente recibe notificación inmediata por WhatsApp.
- El endpoint `self-cancel` prepara el sistema para que cualquier interfaz de cliente futura (formulario web de participantes, chatbot, etc.) permita la cancelación self-service sin permisos de admin.
- Los tests de Flutter fueron actualizados para implementar el nuevo método `cancelReservation` en todos los fakes/repositorios.

## Estado

Aceptada.

## Relacionado

- `docs/architecture/api-endpoints.md` (actualizado con `/reservations/self-cancel`).
