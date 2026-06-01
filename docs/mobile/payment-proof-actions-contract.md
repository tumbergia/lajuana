# Contrato: Acciones sobre comprobantes de pago

Versión: 1.0
Última actualización: 2026-05-25

## Endpoints

### Aprobar comprobante

```
POST /api/v1/payment-proofs/{payment_proof_id}/approve
```

**Request body:**
```json
{
  "confirmation_token": "APPROVE_PAYMENT",
  "note": "Opcional — comentario del administrador"
}
```

**Response (200):** `ReservationResponseSchema` — detalle completo de la reserva con participantes y comprobantes actualizados.

### Rechazar comprobante

```
POST /api/v1/payment-proofs/{payment_proof_id}/reject
```

**Request body:**
```json
{
  "confirmation_token": "REJECT_PAYMENT",
  "reason": "Motivo obligatorio del rechazo"
}
```

**Response (200):** `ReservationResponseSchema` — detalle completo de la reserva actualizada.

## Estados del comprobante

| Valor | Descripción |
|---|---|
| `pending` | Pendiente (sin acción) |
| `received` | Recibido, pendiente de revisión |
| `verified` | Verificado / Aprobado |
| `rejected` | Rechazado |

## Transiciones permitidas

| Desde | Hacia | ¿Permitido? | Condición |
|---|---|---|---|
| `received` | `verified` | Sí | Solo admin |
| `received` | `rejected` | Sí | Solo admin + motivo obligatorio |
| `verified` | — | No | Terminal |
| `rejected` | — | No | Terminal |

**Regla dura:** Aprobar un comprobante NO confirma la reserva. Solo transiciona `reservation.payment_status` a `verified` y `reservation.status` a `payment_received`. La confirmación definitiva requiere otro microplan con revalidación de disponibilidad.

## Códigos de error

| HTTP | Código | Significado |
|---|---|---|
| 401 | `auth.unauthorized` | Token requerido |
| 401 | `auth.expired_token` | Token expirado |
| 403 | `auth.forbidden` | El rol no tiene permiso (guía no puede) |
| 404 | `payment_proof.not_found` | Comprobante no existe |
| 404 | `reservation.not_found` | Reserva asociada no existe |
| 409 | `reservation.invalid_status_transition` | El comprobante ya está en estado terminal |
| 422 | `common.validation_error` | Reason vacío o confirmation_token inválido |

## Permisos

| Acción | Permiso requerido | admin | guía |
|---|---|---|---|
| Ver comprobante | `PAYMENT_PROOF_READ` | Sí | Sí |
| Descargar | `PAYMENT_PROOF_READ` | Sí | Sí |
| Crear | `PAYMENT_PROOF_CREATE` | Sí | Sí |
| Aprobar | `PAYMENT_VERIFY` | Sí | **No** |
| Rechazar | `PAYMENT_VERIFY` | Sí | **No** |

La validación de permisos ocurre en dos capas:
1. **Endpoint**: `require_permissions(Permission.PAYMENT_VERIFY)` — bloquea en el router
2. **Servicio**: `if actor_role != UserRole.ADMIN: raise ApiError(403)` — defensa en profundidad

## Efecto en la reserva

### Al aprobar
- `payment_proof.status` → `verified`
- `reservation.payment_status` → `verified`
- `reservation.status` → `payment_received` (NO `confirmed`)
- Se envía notificación WhatsApp al titular
- Se crea evento de auditoría

### Al rechazar
- `payment_proof.status` → `rejected`
- `reservation.payment_status` → `rejected`
- `reservation.status` → NO cambia (sigue en estado anterior)
- Se crea evento de auditoría con el motivo

## Auditoría

Cada acción crea un `ReservationAuditLogDocument` en la colección `reservation_audit_logs`.

**Campos:**
| Campo | Tipo | Descripción |
|---|---|---|
| `reservation_id` | PydanticObjectId | Reserva afectada |
| `payment_proof_id` | PydanticObjectId? | Comprobante afectado |
| `actor_user_id` | PydanticObjectId | Quien ejecutó la acción |
| `actor_role` | UserRole | Rol del actor |
| `action` | str | `payment_proof.approved` o `payment_proof.rejected` |
| `previous_status` | str | Estado anterior del comprobante |
| `new_status` | str | Nuevo estado |
| `reason` | str? | Motivo (obligatorio en rechazo) |
| `source` | str | Origen: `mobile_app` |
| `metadata` | dict | Datos adicionales |

## Almacenamiento de comprobantes

Los bytes del archivo se almacenan directamente en MongoDB, en el campo `file_data: bytes` del documento `PaymentProofDocument`.

### Flujo de descarga

```
GET /api/v1/payment-proofs/{id}/download

1. ¿doc.file_data no es null?   → servir bytes directo (content-type + bytes)
2. ¿storage_key empieza con "whatsapp/" y size_bytes == 1? → 202 pending
3. Fallback: leer de adapter.read_bytes(storage_key) → legacy proofs
```

**Sin archivos físicos en disco o S3.** Solo MongoDB. Esto evita llenar el servidor de archivos y simplifica el deploy.

### Excepciones

- `file_data` **no se expone** en `PaymentProofResponseSchema` (solo se sirve via streaming/download endpoint).
- Si `file_data` es `null` (proofs legacy de WhatsApp/S3), se usa el storage adapter como fallback.

### Migración de proofs sintéticos

El script `app.seed_proof_file_data` busca proofs con `storage_key` que empiezan con `synthetic/` o `seed/` y sin `file_data`, y les asigna los bytes de la imagen local (`pago-example.png`) o un placeholder mínimo.

```bash
python -m app.seed_proof_file_data
```

## Reglas de negocio

1. Sin conexión → no se puede aprobar/rechazar. Acciones financieras son online-only.
2. No hay cola offline para estas acciones.
3. Aprobar no equivale a confirmar reserva.
4. Rechazar requiere motivo obligatorio (min 1 carácter).
5. Admin puede ver, descargar, aprobar y rechazar.
6. Guía puede ver y descargar comprobantes, pero NO aprobar ni rechazar.
7. La UI oculta los comprobantes al guía, pero el backend también bloquea por permisos.
8. Doble-tap bloqueado en UI: no se puede enviar dos veces la misma acción.
9. Los archivos se almacenan en MongoDB (`file_data`), no en disco/S3.
