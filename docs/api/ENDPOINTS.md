# API Endpoints

Base path: `/api/v1`

Documentation: auto-generated OpenAPI available at `/api/v1/docs` (Swagger UI).

---

## Health

Prefix: _(none — tag: health)_

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | System health check (MongoDB ping, aggregated status) |

---

## Auth

Prefix: `/auth` — tag: Autenticacion

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register a new public user |
| POST | `/api/v1/auth/login` | Login, returns JWT access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh an expired access token |
| POST | `/api/v1/auth/logout` | Invalidate the current session |
| POST | `/api/v1/auth/change-password` | Change authenticated user's password |
| GET | `/api/v1/auth/me` | Get authenticated user profile |

---

## Users

Prefix: `/users` — tag: Usuarios

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/users` | Create a new internal user (admin) |
| GET | `/api/v1/users` | List internal users (paginated, X-Total-Count header) |
| GET | `/api/v1/users/{user_id}` | Get user by ID |
| PATCH | `/api/v1/users/{user_id}` | Update user |
| DELETE | `/api/v1/users/{user_id}` | Soft-delete user |

---

## Experiences

Prefix: `/experiences` — tag: Experiencias

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/experiences` | Create a new experience |
| GET | `/api/v1/experiences` | List experiences (with is_active filter, paginated) |
| GET | `/api/v1/experiences/{experience_id}` | Get experience by ID |
| PATCH | `/api/v1/experiences/{experience_id}` | Update experience |
| DELETE | `/api/v1/experiences/{experience_id}` | Deactivate experience (soft) |
| POST | `/api/v1/experiences/{experience_id}/quote` | Quote experience pricing by participant count |

---

## Reservations

Prefix: `/reservations` — tag: Reservas

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/reservations` | Create a new reservation |
| GET | `/api/v1/reservations` | List reservations (paginated, X-Total-Count) |
| GET | `/api/v1/reservations/availability` | Check availability for a given date |
| GET | `/api/v1/reservations/{reservation_id}` | Get reservation by ID |
| GET | `/api/v1/reservations/{reservation_id}/timeline` | Unified reservation logbook timeline |
| PATCH | `/api/v1/reservations/{reservation_id}` | Update reservation |
| POST | `/api/v1/reservations/{reservation_id}/confirm` | Confirm reservation |
| POST | `/api/v1/reservations/{reservation_id}/status` | Transition reservation status |
| POST | `/api/v1/reservations/{reservation_id}/cancel` | Cancel a reservation (admin) |
| DELETE | `/api/v1/reservations/{reservation_id}` | Soft-delete reservation |
| POST | `/api/v1/reservations/{reservation_id}/restore` | Restore soft-deleted reservation |
| POST | `/api/v1/reservations/self-cancel` | Self-cancel by code + phone (public) |
| POST | `/api/v1/reservations/{reservation_id}/payment-proofs` | Attach payment proof to reservation |
| POST | `/api/v1/reservations/{reservation_id}/participants` | Add participant to reservation |

---

## Equines

Prefix: `/equines` — tag: Equinos

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/equines` | Create an equine |
| GET | `/api/v1/equines` | List equines (filtered, paginated) |
| GET | `/api/v1/equines/list` | Compact listing for mobile cards |
| GET | `/api/v1/equines/{equine_id}` | Get equine by ID |
| GET | `/api/v1/equines/{equine_id}/timeline` | Get equine service log timeline |
| GET | `/api/v1/equines/available-for-reservation/{reservation_id}` | List equines available for a reservation (with block_reason) |
| PATCH | `/api/v1/equines/{equine_id}` | Update equine |
| DELETE | `/api/v1/equines/{equine_id}` | Soft-delete equine |
| POST | `/api/v1/equines/{equine_id}/restore` | Restore soft-deleted equine |

---

## Saddles

Prefix: `/saddles` — tag: Sillas

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/saddles` | Create a saddle |
| GET | `/api/v1/saddles` | List saddles (paginated) |
| GET | `/api/v1/saddles/available-for-reservation/{reservation_id}` | List saddles available for a reservation |
| GET | `/api/v1/saddles/{saddle_id}` | Get saddle by ID |
| PATCH | `/api/v1/saddles/{saddle_id}` | Update saddle |
| DELETE | `/api/v1/saddles/{saddle_id}` | Soft-delete saddle |
| POST | `/api/v1/saddles/{saddle_id}/restore` | Restore soft-deleted saddle |

---

## Assignments

Prefix: `/assignments` — tag: Asignaciones

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/assignments` | Create assignment (equine + saddle to participant) |
| GET | `/api/v1/assignments/{assignment_id}` | Get assignment by ID |
| PATCH | `/api/v1/assignments/{assignment_id}` | Update assignment |
| POST | `/api/v1/assignments/{assignment_id}/finalize` | Finalize an assignment (CONFIRMED → FINAL) |
| POST | `/api/v1/assignments/{assignment_id}/unfinalize` | Revert finalization (FINAL → CONFIRMED) |
| DELETE | `/api/v1/assignments/{assignment_id}` | Remove assignment (mark cancelled) |
| POST | `/api/v1/assignments/{assignment_id}/replace` | Replace a finalized assignment |
| GET | `/api/v1/assignments/board/{reservation_id}` | Get assignment board (participants + assignments + available resources) |
| POST | `/api/v1/assignments/reservation/{reservation_id}/finalize-all` | Finalize all assignments for a reservation |
| POST | `/api/v1/assignments/reservation/{reservation_id}/unfinalize-all` | Revert all finalizations |
| POST | `/api/v1/assignments/reservation/{reservation_id}/batch` | Batch update assignments (local-first flow) |

---

## Participants

Prefix: `/participants` — tag: Participantes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/participants/{participant_id}` | Get participant by ID |
| PATCH | `/api/v1/participants/{participant_id}` | Update participant |

---

## Participant Forms

Prefix: _(mixed paths)_ — tag: Formulario de participantes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/public/participant-forms/{token}/validate` | Validate form token |
| GET | `/api/v1/public/participant-form/{token}` | Validate token (Vercel-compatible alias) |
| POST | `/api/v1/public/participant-form/{token}` | Register participant (Vercel-compatible) |
| GET | `/api/v1/public/participant-forms/{token}/status` | Public form aggregated status |
| POST | `/api/v1/public/participant-forms/{token}/participants` | Register participant from public form |
| GET | `/api/v1/public/participant-forms/risk-release-text` | Get current risk release text |
| POST | `/api/v1/reservations/{reservation_id}/participant-form-link` | Generate participant form link |
| POST | `/api/v1/reservations/{reservation_id}/participant-form-link/revoke` | Revoke form link |
| POST | `/api/v1/reservations/{reservation_id}/participant-form-link/resend` | Resend form link via WhatsApp |
| GET | `/api/v1/reservations/{reservation_id}/participant-form-link` | Get form link status |

---

## Payment Proofs

Prefix: `/payment-proofs` — tag: Comprobantes de pago

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/payment-proofs/{payment_proof_id}/download` | Download payment proof file |
| GET | `/api/v1/payment-proofs/{payment_proof_id}` | Get payment proof by ID |
| PATCH | `/api/v1/payment-proofs/{payment_proof_id}` | Update payment proof metadata |
| POST | `/api/v1/payment-proofs/{payment_proof_id}/verify` | Verify payment proof |
| POST | `/api/v1/payment-proofs/{payment_proof_id}/approve` | Approve payment + notify customer |
| POST | `/api/v1/payment-proofs/{payment_proof_id}/reject` | Reject payment proof |
| POST | `/api/v1/payment-proofs/{payment_proof_id}/unverify` | Unverify payment |
| POST | `/api/v1/payment-proofs/{payment_proof_id}/unreject` | Unreject payment |

---

## Notifications

Prefix: `/notifications` — tag: Notificaciones

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/notifications/templates` | List notification templates |
| POST | `/api/v1/notifications/reset/{reservation_id}` | Cancel pending outbox entries (force regenerate) |
| POST | `/api/v1/notifications/test/{reservation_id}` | Manual test — enqueue and send notification |
| GET | `/api/v1/notifications/outbox/{notification_id}` | Get notification outbox entry |
| POST | `/api/v1/notifications/outbox/{notification_id}/retry` | Retry failed notification |
| POST | `/api/v1/notifications/outbox/{notification_id}/cancel` | Cancel pending notification |
| GET | `/api/v1/notifications/in-app` | List in-app notifications for current user |

---

## Providers

Prefix: `/providers` — tag: Proveedores

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/providers` | Create a provider |
| GET | `/api/v1/providers/{provider_id}` | Get provider by ID |
| PATCH | `/api/v1/providers/{provider_id}` | Update provider |
| DELETE | `/api/v1/providers/{provider_id}` | Deactivate provider |

---

## Policies

Prefix: `/policies` — tag: Polizas

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/policies` | Create a policy |
| GET | `/api/v1/policies/{policy_id}` | Get policy by ID |
| PATCH | `/api/v1/policies/{policy_id}` | Update policy |

---

## Service Logs

Prefix: `/logs` — tag: Bitacora

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/logs` | Create a service log entry |
| GET | `/api/v1/logs?reservation_id={id}` | List service logs for a reservation |
| GET | `/api/v1/logs/{log_id}` | Get log entry by ID |
| PATCH | `/api/v1/logs/{log_id}` | Update log entry |
| DELETE | `/api/v1/logs/{log_id}` | Soft-delete log entry |

---

## Config

Prefix: `/config` — tag: Configuracion

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/config/emergency-contacts` | Get emergency contact info |
| GET | `/api/v1/config/reservation-rules` | Get reservation rules |
| PATCH | `/api/v1/config/reservation-rules` | Update reservation rules |

---

## Sync (Offline-First)

Prefix: `/sync` — tag: Sync

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/sync/bootstrap` | Get full initial data dump for mobile client |
| POST | `/api/v1/sync/pull` | Pull incremental changes since last cursor |
| POST | `/api/v1/sync/push` | Push local operations to server |

---

## Files

Prefix: `/files` — tag: Files

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/files/init-upload` | Initialize a file upload (returns upload URL) |
| POST | `/api/v1/files/{upload_id}/complete` | Mark upload as complete |

---

## WhatsApp

Prefix: `/whatsapp` — tag: WhatsApp

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/whatsapp/webhook` | WhatsApp webhook verification (Meta challenge) |
| POST | `/api/v1/whatsapp/webhook` | Receive incoming WhatsApp messages |

---

## Assistant / AI

Prefix: _(none)_ — tag: Assistant

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ask` | Public assistant chat (Gemini planner + MCP tools) |
| POST | `/api/v1/admin/ask` | Admin-only assistant chat with full tool access |

---

## Diagnostics

Prefix: `/diagnostics` — tag: diagnostics

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/diagnostics/ping` | Create a MongoDB/Beanie ping document |
| GET | `/api/v1/diagnostics/ping/latest` | Get latest ping status |
| GET | `/api/v1/diagnostics/time` | Get time diagnostics (UTC, Colombia, timezone) |

---

## Common patterns

| Pattern | Behavior |
|---------|----------|
| Pagination | `limit` (1–1000), `skip` params + `X-Total-Count` header |
| Auth | JWT Bearer token via `Authorization` header |
| Permissions | Role-based; each endpoint enumerates required `Permission` enum |
| Soft delete | Entities set `deleted_at`; `include_deleted=false` by default |
| Error format | JSON body with `code`, `message`, optional `details` — see [ERRORS.md](ERRORS.md) |
