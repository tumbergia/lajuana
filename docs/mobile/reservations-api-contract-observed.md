# Contrato API de Reservas observado

> Fecha: 2026-05-26
> Fuente: `apps/api/app/schemas/reservation.py`, `apps/api/app/services/mappers.py`

## GET /api/v1/reservations

### Response: `list[ReservationListItemSchema]`

```json
[
  {
    "id": "660000000000000000000201",
    "code": "RES-SEED-001",
    "status": "pending_payment",
    "participant_count": 2,
    "payment_status": "verified",
    "holder_name": "Carlos Mejia",
    "holder_phone": "3000000001",
    "experience_id": "660000000000000000000101",
    "experience_name": "Los Chorros",
    "schedule_id": "660000000000000000000401",
    "requested_date": "2026-05-10",
    "scheduled_date": "2026-05-10",
    "start_time": "09:00:00",
    "expected_participants_count": 2,
    "participants_completed_count": 1,
    "participant_form_status": "partial",
    "channel": "whatsapp",
    "version": 3,
    "created_at": "2026-05-25T12:00:00Z",
    "updated_at": "2026-05-25T12:00:00Z",
    "deleted_at": null
  }
]
```

### Fields

| Campo | Tipo | Nullable | Notas |
|-------|------|----------|-------|
| `id` | `string` | No | ObjectId hex |
| `code` | `string` | No | Código legible |
| `status` | `string` | No | Enum completo de estado |
| `participant_count` | `int` | No | Cantidad de participantes |
| `payment_status` | `string` | No | Enum: `pending`, `received`, `verified`, `rejected` |
| `holder_name` | `string?` | Sí | Nombre del titular |
| `holder_phone` | `string?` | Sí | Teléfono del titular |
| `experience_id` | `string` | No | Ref a experiencia |
| `experience_name` | `string?` | Sí | Nombre denormalizado |
| `schedule_id` | `string?` | Sí | Ref a schedule |
| `requested_date` | `date?` | Sí | Fecha solicitada |
| `scheduled_date` | `string?` | Sí | Fecha operativa |
| `start_time` | `string?` | Sí | Hora operativa |
| `expected_participants_count` | `int?` | Sí | Cupo formulario |
| `participants_completed_count` | `int` | No | Completitud |
| `participant_form_status` | `string` | No | Estado formulario |
| `channel` | `string?` | Sí | Canal de origen |
| `version` | `int` | No | |
| `created_at` | `datetime` | No | |
| `updated_at` | `datetime` | No | |
| `deleted_at` | `datetime?` | Sí | |

### Datos ausentes (a propósito)

No se incluyen en el listado porque no son necesarios para la card:
- `holder_email`
- `quoted_total_amount`, `currency`, `form_url`
- `confirmed_at`, `cancelled_at`, `completed_at`

Esos campos se obtienen de `GET /api/v1/reservations/{id}` al abrir el detalle.

**Estrategia**: el listado es autosuficiente para renderizar la card. No se necesita hidratación por detalle.

---

## GET /api/v1/reservations/{reservation_id}

### Response: `ReservationResponseSchema`

```json
{
  "id": "660000000000000000000201",
  "code": "RES-SEED-001",
  "experience_id": "660000000000000000000101",
  "schedule_id": "660000000000000000000401",
  "channel": "whatsapp",
  "status": "pending_payment",
  "participant_count": 2,
  "payment_status": "verified",
  "holder_name": "Carlos Mejia",
  "holder_email": "carlos@example.com",
  "holder_phone": "3000000001",
  "requested_date": "2026-05-10",
  "quoted_total_amount": "180000",
  "currency": "COP",
  "expected_participants_count": 2,
  "participants_completed_count": 1,
  "participant_form_status": "partial",
  "form_url": "https://example.test/form",
  "confirmed_at": null,
  "cancelled_at": null,
  "completed_at": null,
  "version": 3,
  "created_at": "2026-05-25T12:00:00Z",
  "updated_at": "2026-05-25T12:00:00Z",
  "deleted_at": null,
  "participants": [
    {
      "id": "660000000000000000000301",
      "reservation_id": "660000000000000000000201",
      "first_name": "Carlos",
      "last_name": "Mejia",
      "birth_date": "1990-05-15",
      "document_type": "cc",
      "document_number": "80000001",
      "phone": "3110000001",
      "country": "Colombia",
      "city": "Manizales",
      "height_cm": "175.0",
      "weight_kg": "70.0",
      "experience_level": "intermediate",
      "dietary_restrictions": null,
      "blood_type": null,
      "eps_or_travel_insurance": null,
      "health_conditions": null,
      "sensory_disabilities": null,
      "emergency_contact": {
        "name": "Contacto",
        "phone": "3200000001",
        "relationship": "familiar"
      },
      "accepted_data_processing": true,
      "accepted_media_usage": true,
      "accepted_risk_release": true,
      "is_completed": true
    }
  ],
  "payment_proofs": [
    {
      "id": "660000000000000000000401",
      "reservation_id": "660000000000000000000201",
      "storage_key": "seed/RES-SEED-001.pdf",
      "filename": "RES-SEED-001.pdf",
      "content_type": "application/pdf",
      "size_bytes": 2048,
      "sha256": "abc123",
      "status": "verified",
      "uploaded_at": "2026-05-25T12:00:00Z"
    }
  ]
}
```

### Fields

| Campo | Tipo | Nullable | Notas |
|-------|------|----------|-------|
| `id` | `string` | No | ObjectId hex |
| `code` | `string` | No | Código legible |
| `experience_id` | `string` | No | Referencia a Experience |
| `schedule_id` | `string?` | Sí | Referencia a Schedule |
| `channel` | `string` | No | `facebook`, `instagram`, `whatsapp`, `email` |
| `status` | `string` | No | Enum de estado |
| `participant_count` | `int` | No | |
| `payment_status` | `string` | No | `pending`, `received`, `verified`, `rejected` |
| `holder_name` | `string?` | Sí | Nombre del titular |
| `holder_email` | `string?` | Sí | Email del titular |
| `holder_phone` | `string?` | Sí | Teléfono del titular |
| `requested_date` | `date?` | Sí | Fecha solicitada (ISO 8601 date) |
| `quoted_total_amount` | `Decimal?` | Sí | Se serializa como string |
| `currency` | `string` | No | `COP` por defecto |
| `expected_participants_count` | `int?` | Sí | Cupo del formulario |
| `participants_completed_count` | `int` | No | Completitud de formulario |
| `participant_form_status` | `string` | No | `not_sent`, `sent`, `partial`, `complete`, `revoked` |
| `form_url` | `string?` | Sí | URL del formulario público |
| `confirmed_at` | `datetime?` | Sí | |
| `cancelled_at` | `datetime?` | Sí | |
| `completed_at` | `datetime?` | Sí | |
| `version` | `int` | No | |
| `created_at` | `datetime` | No | |
| `updated_at` | `datetime` | No | |
| `deleted_at` | `datetime?` | Sí | |
| `participants` | `list<ParticipantResponseSchema>` | No (default `[]`) | Participantes con datos completos. Resueltos mediante `$in` query sobre `participant_ids`. |
| `payment_proofs` | `list<PaymentProofResponseSchema>` | No (default `[]`) | Comprobantes de pago. Resueltos mediante `$in` query sobre `payment_proof_ids`. |

### Datos ausentes (aún no incluidos)

- `assignments` (asignaciones equino/silla) — no incluida (para fase v3)
- `logs` (bitácora) — no incluida (para fase v3)
- `timeline` (línea de tiempo construida) — no incluida (se deriva en frontend)
- `operational_alerts` — no incluida (se computa en frontend)
- `quote_snapshot` — existe en documento pero no en response (pendiente)
- `payment_proof_ids` — existe en documento pero no en response

---

## POST /api/v1/reservations/{id}/payment-proofs

Crea comprobante asociado a una reserva. Cuerpo:

```json
{
  "filename": "comprobante.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2048,
  "sha256": "abc123",
  "storage_key": "proofs/res-001.pdf"
}
```

Response: `PaymentProofResponseSchema`.

---

## POST /api/v1/reservations/{id}/participants

Crea participante asociado a una reserva. Cuerpo completo en `apps/api/app/schemas/participant.py:ParticipantCreateSchema`.

Response: `ParticipantResponseSchema`.

---

## GET /api/v1/reservations/{reservation_id}/participant-form-link

Responde con el enlace de formulario activo o el último generado. Response nullable.

---

## POST /api/v1/reservations/{reservation_id}/confirm

Confirma una reserva (admin-only, online-only). Ver `docs/mobile/reservation-confirmation-contract.md` para el contrato completo.

**Request body:**
```json
{
  "notes": "Opcional — comentario interno del administrador"
}
```

**Response (200):** `ReservationResponseSchema` con `status: confirmed`, `confirmed_at` timestamp, `form_url` generado.

---

## API Error Contract

Toda respuesta de error sigue `ApiErrorResponse`:

```json
{
  "code": "reservation.not_found",
  "message": "Reserva no encontrada.",
  "details": null
}
```

Códigos relevantes para `GET` endpoints:
- `auth.unauthorized` (401)
- `auth.forbidden` (403)
- `reservation.not_found` (404)
- `common.validation_error` (422)

---

## Riesgos

1. **Denormalización `experience_name`**: se resuelve en backend mediante batch fetch (aprox. 2 queries extra por listado). Si crece mucho el número de experiencias únicas, monitorear performance.
2. **`start_time` como string**: viene de `ScheduleDocument.start_time` que es `datetime.time`. Se serializa como ISO string (`"09:00:00"`). El frontend debe tolerar formato.
3. **Frontend sin catálogos locales**: el summary ahora trae `experience_name` directamente, así que no se necesita lookup local. Bueno.
4. **Contrato detalle v2**: desde 2026-05-26 el endpoint GET /reservations/{id} incluye `participants[]` y `payment_proofs[]` resueltos por `$in` query usando `participant_ids` y `payment_proof_ids`. Se evita N+1 desde el frontend. Asignaciones y bitácora siguen pendientes para fase v3.
5. **Payload size increment**: incluir `participants[]` y `payment_proofs[]` puede duplicar el tamaño del response (~2-10 KB extra para 2-10 participantes). No se espera problema en redes móviles típicas, pero monitorear si reservas con 20+ participantes degradan rendimiento.