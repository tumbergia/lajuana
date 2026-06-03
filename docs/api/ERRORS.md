# API Error Reference

All API errors follow a consistent format. The system uses an explicit `ApiError` exception and a shared `ErrorCode` vocabulary.

---

## Response Format

Every error response is a JSON object with this shape:

```json
{
  "code": "common.validation_error",
  "message": "Human-readable description",
  "details": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `code` | `string` | Dot-separated domain + specific error (`{domain}.{specific_error}`) |
| `message` | `string` | User-facing description in Spanish |
| `details` | `object\|null` | Optional additional context (e.g. validation field errors) |

The schema is defined in `app/schemas/common.py` — `ApiErrorResponse`.

---

## ApiError Class

Defined in `app/core/errors.py`:

```python
class ApiError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str, details: dict | None = None):
        ...
```

Two required fields plus optional `details`.

### How to raise

```python
from app.common.labels import ErrorCode
from app.core.errors import ApiError

raise ApiError(
    status_code=404,
    code=ErrorCode.RESERVATION_NOT_FOUND,
    message="Reserva no encontrada.",
)
```

### How it's handled

- `ApiError` → `api_error_handler`: serializes to JSON with the matching HTTP status code.
- `RequestValidationError` → `validation_error_handler`: returns 422 with `code: "common.validation_error"` and field-level errors in `details.fields`.
- `HTTPException` → `http_exception_handler`: if `detail` contains `code` and `message`, those are forwarded; otherwise falls back to `common.internal_error` (500+) or `common.conflict`.

Registered in `register_error_handlers()` called during app startup.

---

## Error Domains

Each domain groups related errors. The first segment of `code` identifies the domain.

### `common.*` — Generic

| Code | HTTP | Description |
|------|------|-------------|
| `common.validation_error` | 422 | Request validation failed (Pydantic) |
| `common.resource_not_found` | 404 | Resource not found |
| `common.method_not_allowed` | 405 | HTTP method not allowed |
| `common.conflict` | 409 | Conflict |
| `common.internal_error` | 500 | Unexpected server error |

### `auth.*` — Authentication & Authorization

| Code | HTTP | Description |
|------|------|-------------|
| `auth.invalid_credentials` | 401 | Email/password incorrect |
| `auth.inactive_user` | 401 | User account is inactive |
| `auth.invalid_token` | 401 | JWT token invalid |
| `auth.expired_token` | 401 | JWT token expired |
| `auth.forbidden` | 403 | Insufficient permissions |
| `auth.password_mismatch` | 400 | Current password doesn't match |
| `auth.unauthorized` | 401 | No authentication provided |

### `user.*` — User Management

| Code | HTTP | Description |
|------|------|-------------|
| `user.email_already_exists` | 409 | Duplicate email |
| `user.not_found` | 404 | User not found |
| `user.role_invalid` | 400 | Invalid role assignment |
| `user.self_delete_forbidden` | 403 | Cannot delete own account |
| `user.inactive` | 403 | User is inactive |

### `experience.*` — Experiences

| Code | HTTP | Description |
|------|------|-------------|
| `experience.not_found` | 404 | Experience not found |
| `experience.slug_already_exists` | 409 | Duplicate slug |
| `experience.invalid_duration` | 400 | Invalid duration value |
| `experience.invalid_capacity` | 400 | Invalid capacity value |
| `experience.pricing_tiers_required` | 400 | Pricing tiers are required |
| `experience.pricing_tier_invalid_range` | 400 | Tier range invalid |
| `experience.pricing_tiers_overlap` | 409 | Tier ranges overlap |
| `experience.pricing_tiers_gap` | 400 | Gap between tier ranges |
| `experience.route_duration_exceeds_activity_duration` | 400 | Route longer than activity |
| `experience.standard_capacity_out_of_pricing_range` | 400 | Standard capacity outside pricing |
| `experience.inclusions_required` | 400 | Inclusions list required |
| `experience.inactive` | 400 | Experience is inactive |
| `experience.pricing_missing` | 400 | No pricing configured |
| `experience.pricing_tier_not_found` | 404 | Tier not found |

### `schedule.*` — Schedules

| Code | HTTP | Description |
|------|------|-------------|
| `schedule.not_found` | 404 | Schedule not found |
| `schedule.invalid_capacity` | 400 | Invalid capacity |
| `schedule.invalid_slot_values` | 400 | Invalid slot values |
| `schedule.negative_availability` | 400 | Availability would go negative |
| `schedule.not_open` | 400 | Schedule not open for booking |
| `schedule.already_full` | 409 | Schedule at max capacity |
| `schedule.invalid_status` | 400 | Invalid status transition |
| `schedule.experience_mismatch` | 400 | Schedule belongs to different experience |
| `schedule.hold_failed` | 409 | Failed to hold slots |
| `schedule.held_slots_negative` | 400 | Held slots went negative |

### `reservation.*` — Reservations (central entity)

| Code | HTTP | Description |
|------|------|-------------|
| `reservation.not_found` | 404 | Reservation not found |
| `reservation.invalid_status_transition` | 409 | Status change not allowed |
| `reservation.min_notice_violation` | 400 | Below minimum notice days |
| `reservation.no_availability` | 409 | No available slots |
| `reservation.payment_required` | 402 | Payment required |
| `reservation.payment_not_verified` | 400 | Payment not yet verified |
| `reservation.invalid_participant_count` | 400 | Participant count out of range |
| `reservation.schedule_mismatch` | 400 | Schedule doesn't match reservation |
| `reservation.confirmation_not_allowed` | 409 | Cannot confirm in current state |
| `reservation.cancellation_not_allowed` | 409 | Cannot cancel in current state |
| `reservation.already_cancelled` | 409 | Already cancelled |
| `reservation.already_completed` | 409 | Already completed |
| `reservation.pre_reservation_expired` | 410 | Draft/pre-reservation expired |
| `reservation.already_pre_reserved` | 409 | Already has a draft |
| `reservation.invalid_holder` | 400 | Invalid holder data |
| `reservation.quote_snapshot_required` | 400 | Quote snapshot missing |

### `payment_proof.*` — Payment Proofs

| Code | HTTP | Description |
|------|------|-------------|
| `payment_proof.not_found` | 404 | Payment proof not found |
| `payment_proof.storage_key_required` | 400 | Storage key missing |
| `payment_proof.invalid_content_type` | 400 | Unsupported file type |
| `payment_proof.invalid_size` | 400 | File size out of bounds |
| `payment_proof.hash_required` | 400 | File hash missing |
| `payment_proof.reservation_mismatch` | 400 | Proof doesn't match reservation |
| `payment_proof.file_not_found` | 404 | File not in storage |

### `participant.*` — Participants

| Code | HTTP | Description |
|------|------|-------------|
| `participant.not_found` | 404 | Participant not found |
| `participant.reservation_mismatch` | 400 | Participant not in this reservation |
| `participant.missing_required_fields` | 400 | Required fields missing |
| `participant.invalid_birth_date` | 400 | Invalid birth date |
| `participant.invalid_weight` | 400 | Invalid weight |
| `participant.invalid_height` | 400 | Invalid height |
| `participant.data_processing_required` | 400 | Must accept data processing |
| `participant.operationally_incomplete` | 400 | Participant not ready for assignment |
| `participant.risk_release_required` | 400 | Risk release not accepted |
| `participant.risk_release_rejected` | 403 | Risk release was rejected |
| `participant.invalid_height_weight` | 400 | Height/weight combination invalid |
| `participant.form_not_complete` | 400 | Participant form not complete |

### `equine.*` — Equines

| Code | HTTP | Description |
|------|------|-------------|
| `equine.not_found` | 404 | Equine not found |
| `equine.unavailable` | 409 | Equine not available |
| `equine.invalid_weight` | 400 | Invalid weight capacity |

### `saddle.*` — Saddles

| Code | HTTP | Description |
|------|------|-------------|
| `saddle.not_found` | 404 | Saddle not found |
| `saddle.code_already_exists` | 409 | Duplicate saddle code |
| `saddle.unavailable` | 409 | Saddle not available |

### `assignment.*` — Assignments

| Code | HTTP | Description |
|------|------|-------------|
| `assignment.not_found` | 404 | Assignment not found |
| `assignment.reservation_not_confirmed` | 400 | Reservation not confirmed |
| `assignment.participant_not_in_reservation` | 400 | Participant not in this reservation |
| `assignment.participant_missing_required_data` | 400 | Participant data incomplete |
| `assignment.equine_not_available` | 409 | Equine not available |
| `assignment.equine_already_assigned` | 409 | Equine already assigned for this date |
| `assignment.saddle_not_available` | 409 | Saddle not available |
| `assignment.saddle_already_assigned` | 409 | Saddle already assigned |
| `assignment.rider_weight_exceeds_equine_limit` | 400 | Rider too heavy for equine |
| `assignment.duplicate_for_participant` | 409 | Participant already has assignment |
| `assignment.unsafe_for_child_or_older_adult` | 400 | Unsafe assignment for minor/elder |
| `assignment.invalid_priority` | 400 | Invalid assignment priority |

### Other domains

| Code | HTTP | Description |
|------|------|-------------|
| `provider.not_found` | 404 | Provider not found |
| `policy.not_found` | 404 | Policy not found |
| `policy.reservation_mismatch` | 400 | Policy doesn't match reservation |
| `config.not_found` | 404 | Config not found |
| `config.invalid_min_days` | 400 | Invalid minimum days config |
| `sync.stale_version` | 409 | Sync version conflict |
| `sync.unsupported_operation` | 400 | Unsupported sync operation |
| `sync.invalid_cursor` | 400 | Invalid sync cursor |
| `file_upload.not_found` | 404 | Upload not found |
| `file_upload.expired` | 410 | Upload expired |
| `file_upload.not_ready` | 400 | Upload not yet complete |
| `log.not_found` | 404 | Service log not found |
| `log.checkpoint_name_required` | 400 | Checkpoint name missing |
| `log.invalid_event_type` | 400 | Invalid event type |
| `notification_template.not_found` | 404 | Template not found |
| `notification_template.key_exists` | 409 | Duplicate template key |
| `notification_template.inactive` | 400 | Template is inactive |
| `notification.not_found` | 404 | Notification not found |
| `notification.send_failed` | 500 | Failed to send notification |
| `notification.invalid_channel` | 400 | Invalid notification channel |
| `notification.outbox_full` | 429 | Outbox queue full |
| `notification.provider_not_configured` | 500 | Notification provider not configured |
| `form_link.not_found` | 404 | Form link not found |
| `form_link.expired` | 410 | Form link expired |
| `form_link.revoked` | 410 | Form link was revoked |
| `form_link.invalid_token` | 400 | Invalid form token |
| `form_link.max_participants_reached` | 409 | Form link max participants reached |
| `form_link.reservation_not_confirmed` | 400 | Reservation not yet confirmed |
| `form_link.already_completed` | 409 | Form already completed |

---

## HTTP Status Codes Summary

| Status | Usage |
|--------|-------|
| 400 | Validation / business rule violation |
| 401 | Missing or invalid authentication |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate, wrong state) |
| 410 | Expired / gone |
| 422 | Request validation error (Pydantic) |
| 429 | Rate limit / queue full |
| 500 | Unexpected server error |
