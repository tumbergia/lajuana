# Contrato: Confirmar reserva

Versión: 1.0
Última actualización: 2026-05-26

## Endpoint

```
POST /api/v1/reservations/{reservation_id}/confirm
```

**Request body:**
```json
{
  "notes": "Opcional — comentario interno del administrador"
}
```

**Response (200):** `ReservationResponseSchema` — detalle completo de la reserva con:
- `status` → `confirmed`
- `confirmed_at` → timestamp ISO 8601
- `form_url` → enlace de formulario de participantes generado automáticamente
- `participants[]` y `payment_proofs[]` actualizados

## Errores

| HTTP | Código | Significado |
|---|---|---|
| 400 | `reservation.min_notice_violation` | No cumple anticipación mínima configurada |
| 400 | `reservation.payment_not_verified` | El pago no está verificado (no se confirmó el comprobante) |
| 401 | `auth.unauthorized` | Token requerido |
| 403 | `auth.forbidden` | El rol no tiene permiso (guía no puede) |
| 404 | `reservation.not_found` | Reserva no existe |
| 404 | `schedule.not_found` | Agenda asociada no existe |
| 409 | `reservation.invalid_status_transition` | La reserva ya está confirmada, cancelada o completada |
| 409 | `reservation.no_availability` | La fecha ya no está disponible o no hay cupos |
| 409 | `reservation.confirmation_not_allowed` | La reserva no tiene agenda operativa asignada |
| 409 | `schedule.not_open` | La agenda está desactivada |
| 422 | `common.validation_error` | Payload inválido |

## Permisos

| Acción | Permiso requerido | admin | guía |
|---|---|---|---|
| Confirmar reserva | `RESERVATION_CONFIRM` | Sí | **No** |

La validación ocurre en dos capas:
1. **Endpoint**: `require_permissions(Permission.RESERVATION_CONFIRM)`
2. **Servicio**: La transición `PAYMENT_RECEIVED → CONFIRMED` solo se permite si el rol es admin (defensa en profundidad)

## Precondiciones

Antes de confirmar, el backend valida **todas**:

1. **Reserva existe** — 404 si no
2. **Agenda operativa asignada** — `schedule_id` no puede ser `null`
3. **Agenda activa** — `schedule.is_active` debe ser `true`
4. **Anticipación mínima** — `requested_date` debe cumplir `min_days_in_advance` (configurable)
5. **Pago verificado** — `payment_status` debe ser `verified` (si `require_payment_proof_for_confirmation` está activo, valor por defecto)
6. **Disponibilidad de fecha** — no debe existir otra reserva activa que bloquee la misma fecha
7. **Cupos disponibles** — `available_slots` en schedule deben ser suficientes para `participant_count`
8. **Transición válida** — solo desde `PAYMENT_RECEIVED` hacia `CONFIRMED`

## Efecto en la reserva

| Campo | Antes | Después |
|---|---|---|
| `status` | `payment_received` | `confirmed` |
| `confirmed_at` | `null` | `datetime.now(UTC)` |
| `form_url` | `null` | URL generada con token |
| `participant_form_status` | `not_sent` | `sent` |
| `updated_by` | Anterior | `actor_id` del admin |

## Efecto en el schedule

- `reserved_slots += participant_count`
- `available_slots -= participant_count` O `held_slots -= participant_count` (dependiendo de qué pool se use)
- `status` se recalcula según disponibilidad restante

## Atomicidad

La confirmación ocurre en una sola operación lógica:
1. Revalidación de disponibilidad (pre-try)
2. Descuento de cupos con `$inc` atómico y condición `$gte` en MongoDB (pre-try, falla si otro admin ya tomó los cupos)
3. Transición de estado + persistencia
4. Generación de form link
5. Auditoría (best-effort, no bloqueante)

Si falla entre el paso 2 y el 5, los cupos se revierten (rollback en `except`).

## Doble confirmación

Si dos admins intentan confirmar simultáneamente, el segundo falla con **409**:
- La transición `PAYMENT_RECEIVED → CONFIRMED` no es válida desde `CONFIRMED` o
- El descuento atómico de cupos no encuentra `available_slots >= participant_count`

## Auditoría

Cada confirmación crea un `ReservationAuditLogDocument` en la colección `reservation_audit_logs`:

| Campo | Tipo | Descripción |
|---|---|---|
| `reservation_id` | PydanticObjectId | Reserva confirmada |
| `actor_user_id` | PydanticObjectId | Quien ejecutó la acción |
| `actor_role` | UserRole | `admin` |
| `action` | str | `reservation.confirmed` |
| `previous_status` | str | Estado antes de confirmar (ej: `payment_received`) |
| `new_status` | str | `confirmed` |
| `source` | str | `mobile_app` |

La auditoría es **best-effort**: si falla la inserción, la confirmación no se revierte.

## Reglas de UI (frontend)

1. **Online only** — confirmar requiere conexión. No hay cola offline para esta acción.
2. **Admin only** — el guía no ve el botón de confirmar.
3. **No disponible si** la reserva ya está `confirmed`, `cancelled` o `completed`.
4. **Doble-tap bloqueado** — el botón se deshabilita mientras la acción está en curso.
5. **Diálogo de confirmación** — antes de ejecutar, mostrar modal explicativo.
6. **Refrescar detalle** — después de confirmar, actualizar el detalle completo con la respuesta del backend.
7. **Actualizar cache local** — el repositorio persiste el nuevo estado en SQLite.

## Post-confirmación (siguiente microplan)

| Aspecto | Estado |
|---|---|
| Envío de mensaje WhatsApp de confirmación | Backend lo envía automáticamente (best-effort) |
| Envío de formulario de participantes | Enlace generado y almacenado en `form_url` / `form_sent` |
| Asignaciones equino/silla | Pendiente (microplan separado) |
| Bitácora operativa | Pendiente (microplan separado) |
