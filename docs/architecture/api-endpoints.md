# Endpoints API (Referencia Completa)

Este documento lista todos los endpoints expuestos por `apps/api` según el esquema OpenAPI actual (`/openapi.json`).

## Convenciones

- Prefijo base: `/api/v1`
- Contrato de error: `ApiErrorResponse { code, message, details? }`
- Las validaciones de negocio y conflicto usan códigos estables de `ErrorCode`.
- El frontend debe depender de `code`, no del texto de `message`.

## Health y Diagnostics

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/health` | `health_api_v1_health_get` | — | `200` health payload | `200` |
| POST | `/api/v1/diagnostics/ping` | `create_ping_api_v1_diagnostics_ping_post` | — | `200` ping creado | `200` |
| GET | `/api/v1/diagnostics/ping/latest` | `get_latest_ping_api_v1_diagnostics_ping_latest_get` | — | `200` último ping | `200` |

## Authentication

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/auth/register` | `registerPublicUser` | `RegisterRequest` | `201 UserResponseSchema` | `201, 409, 422` |
| POST | `/api/v1/auth/login` | `loginUser` | `UserLoginSchema` | `200 TokenResponseSchema` | `200, 401, 422` |
| POST | `/api/v1/auth/refresh` | `refreshToken` | — | `200 TokenResponseSchema` | `200, 401, 422` |
| POST | `/api/v1/auth/logout` | `logoutUser` | — | `200` | `200, 401` |
| POST | `/api/v1/auth/change-password` | `changePassword` | `UserChangePasswordSchema` | `200` | `200, 400, 401, 422` |
| GET | `/api/v1/auth/me` | `getCurrentUser` | — | `200 UserResponseSchema` | `200, 401, 404` |

## Users

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/users` | `listUsers` | — | `200 list[UserResponseSchema]` | `200, 401, 403` |
| POST | `/api/v1/users` | `createUser` | `UserCreateSchema` | `201 UserResponseSchema` | `201, 400, 401, 403, 409, 422` |
| GET | `/api/v1/users/{user_id}` | `getUserById` | — | `200 UserResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/users/{user_id}` | `updateUserById` | `UserUpdateSchema` | `200 UserResponseSchema` | `200, 400, 401, 403, 404, 409, 422` |
| DELETE | `/api/v1/users/{user_id}` | `softDeleteUserById` | — | `200` | `200, 401, 403, 404, 409, 422` |

## Experiences

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/experiences` | `createExperience` | `ExperienceCreateSchema` | `201 ExperienceResponseSchema` | `201, 400, 401, 403, 409, 422` |
| GET | `/api/v1/experiences` | `listExperiences` | — | `200 list[ExperienceResponseSchema]` | `200, 401, 422` |
| GET | `/api/v1/experiences/{experience_id}` | `getExperienceById` | — | `200 ExperienceResponseSchema` | `200, 401, 404, 422` |
| PATCH | `/api/v1/experiences/{experience_id}` | `updateExperienceById` | `ExperienceUpdateSchema` | `200 ExperienceResponseSchema` | `200, 400, 401, 403, 404, 409, 422` |
| DELETE | `/api/v1/experiences/{experience_id}` | `deactivateExperienceById` | — | `200 ExperienceResponseSchema` | `200, 401, 403, 404, 422` |
| POST | `/api/v1/experiences/{experience_id}/quote` | `quoteExperienceById` | `ExperienceQuoteRequestSchema` | `200 ExperienceQuoteResponseSchema` | `200, 400, 401, 404, 422` |

## Fechas Operativas (Schedules)

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/schedules` | `createSchedule` | `ScheduleCreateSchema` | `201 ScheduleResponseSchema` | `201, 400, 401, 403, 404, 422` |
| GET | `/api/v1/schedules` | `listSchedules` | — | `200 list[ScheduleResponseSchema]` | `200, 401, 422` |
| GET | `/api/v1/schedules/{schedule_id}` | `getScheduleById` | — | `200 ScheduleResponseSchema` | `200, 401, 404, 422` |
| PATCH | `/api/v1/schedules/{schedule_id}` | `updateScheduleById` | `ScheduleUpdateSchema` | `200 ScheduleResponseSchema` | `200, 400, 401, 403, 404, 422` |
| DELETE | `/api/v1/schedules/{schedule_id}` | `deactivateScheduleById` | — | `200 ScheduleResponseSchema` | `200, 401, 403, 404, 422` |

## Reservations

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/reservations` | `listReservations` | — | `200 list[ReservationListItemSchema]` | `200, 401, 403` |
| POST | `/api/v1/reservations` | `createReservation` | `ReservationCreateSchema` | `201 ReservationResponseSchema` | `201, 400, 401, 403, 404, 422` |
| GET | `/api/v1/reservations/{reservation_id}` | `getReservationById` | — | `200 ReservationResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/reservations/{reservation_id}` | `updateReservationById` | `ReservationUpdateSchema` | `200 ReservationResponseSchema` | `200, 400, 401, 403, 404, 409, 422` |
| POST | `/api/v1/reservations/{reservation_id}/confirm` | `confirmReservationById` | `ReservationConfirmSchema` | `200 ReservationResponseSchema` | `200, 400, 401, 403, 404, 409, 422` |
| POST | `/api/v1/reservations/{reservation_id}/status` | `transitionReservationStatusById` | `ReservationStatusTransitionSchema` | `200 ReservationResponseSchema` | `200, 401, 403, 404, 409, 422` |
| POST | `/api/v1/reservations/{reservation_id}/cancel` | `cancelReservationById` | `ReservationCancelSchema` | `200 ReservationResponseSchema` | `200, 400, 401, 403, 404, 409, 422` |
| POST | `/api/v1/reservations/self-cancel` | `selfCancelReservation` | `ReservationSelfCancelSchema` | `200 ReservationResponseSchema` | `200, 404, 409, 422` |
| POST | `/api/v1/reservations/{reservation_id}/payment-proofs` | `createPaymentProofForReservation` | `PaymentProofCreateSchema` | `201 PaymentProofResponseSchema` | `201, 400, 401, 403, 404, 422` |
| POST | `/api/v1/reservations/{reservation_id}/participants` | `createParticipantForReservation` | `ParticipantCreateSchema` | `201 ParticipantResponseSchema` | `201, 400, 401, 403, 404, 422` |

## Payment Proofs

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/payment-proofs/{payment_proof_id}` | `getPaymentProofById` | — | `200 PaymentProofResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/payment-proofs/{payment_proof_id}` | `updatePaymentProofById` | `PaymentProofUpdateSchema` | `200 PaymentProofResponseSchema` | `200, 401, 403, 404, 409, 422` |
| POST | `/api/v1/payment-proofs/{payment_proof_id}/verify` | `verifyPaymentProofById` | `PaymentProofVerifySchema` | `200 PaymentProofResponseSchema` | `200, 401, 403, 404, 409, 422` |
| POST | `/api/v1/payment-proofs/{payment_proof_id}/reject` | `rejectPaymentProofById` | `PaymentProofRejectSchema` | `200 PaymentProofResponseSchema` | `200, 401, 403, 404, 409, 422` |

## Participants

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/participants/{participant_id}` | `getParticipantById` | — | `200 ParticipantResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/participants/{participant_id}` | `updateParticipantById` | `ParticipantUpdateSchema` | `200 ParticipantResponseSchema` | `200, 400, 401, 403, 404, 422` |

## Configuration

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/config/emergency-contacts` | `getEmergencyContacts` | — | `200 EmergencyContactsResponseSchema` | `200` |
| GET | `/api/v1/config/reservation-rules` | `getReservationRules` | — | `200 ReservationRulesSchema` | `200, 401, 403, 404` |
| PATCH | `/api/v1/config/reservation-rules` | `updateReservationRules` | `ReservationRulesUpdateSchema` | `200 ReservationRulesSchema` | `200, 400, 401, 403, 404, 422` |

## Equines

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/equines` | `listEquines` | — | `200 list[EquineResponseSchema]` | `200, 401` |
| POST | `/api/v1/equines` | `createEquine` | `EquineCreateSchema` | `201 EquineResponseSchema` | `201, 400, 401, 403, 422` |
| GET | `/api/v1/equines/{equine_id}` | `getEquineById` | — | `200 EquineResponseSchema` | `200, 401, 404, 422` |
| PATCH | `/api/v1/equines/{equine_id}` | `updateEquineById` | `EquineUpdateSchema` | `200 EquineResponseSchema` | `200, 400, 401, 403, 404, 422` |
| DELETE | `/api/v1/equines/{equine_id}` | `deactivateEquineById` | — | `200 EquineResponseSchema` | `200, 401, 403, 404, 422` |

## Saddles

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/saddles` | `listSaddles` | — | `200 list[SaddleResponseSchema]` | `200, 401` |
| POST | `/api/v1/saddles` | `createSaddle` | `SaddleCreateSchema` | `201 SaddleResponseSchema` | `201, 401, 403, 409, 422` |
| GET | `/api/v1/saddles/{saddle_id}` | `getSaddleById` | — | `200 SaddleResponseSchema` | `200, 401, 404, 422` |
| PATCH | `/api/v1/saddles/{saddle_id}` | `updateSaddleById` | `SaddleUpdateSchema` | `200 SaddleResponseSchema` | `200, 401, 403, 404, 409, 422` |

## Assignments

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/assignments` | `createAssignment` | `AssignmentCreateSchema` | `201 AssignmentResponseSchema` | `201, 400, 401, 403, 404, 409, 422` |
| GET | `/api/v1/assignments/{assignment_id}` | `getAssignmentById` | — | `200 AssignmentResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/assignments/{assignment_id}` | `updateAssignmentById` | `AssignmentUpdateSchema` | `200 AssignmentResponseSchema` | `200, 401, 403, 404, 409, 422` |

## Service Logs

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/logs` | `createLog` | `ServiceLogCreateSchema` | `201 ServiceLogResponseSchema` | `201, 400, 401, 403, 404, 422` |
| GET | `/api/v1/logs/{log_id}` | `getLogById` | — | `200 ServiceLogResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/logs/{log_id}` | `updateLogById` | `ServiceLogUpdateSchema` | `200 ServiceLogResponseSchema` | `200, 400, 401, 403, 404, 422` |

## Providers

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/providers` | `createProvider` | `ProviderCreateSchema` | `201 ProviderResponseSchema` | `201, 401, 403, 422` |
| GET | `/api/v1/providers/{provider_id}` | `getProviderById` | — | `200 ProviderResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/providers/{provider_id}` | `updateProviderById` | `ProviderUpdateSchema` | `200 ProviderResponseSchema` | `200, 401, 403, 404, 422` |
| DELETE | `/api/v1/providers/{provider_id}` | `deactivateProviderById` | — | `200 ProviderResponseSchema` | `200, 401, 403, 404, 422` |

## Policies

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/policies` | `createPolicy` | `PolicyCreateSchema` | `201 PolicyResponseSchema` | `201, 401, 403, 404, 422` |
| GET | `/api/v1/policies/{policy_id}` | `getPolicyById` | — | `200 PolicyResponseSchema` | `200, 401, 403, 404, 422` |
| PATCH | `/api/v1/policies/{policy_id}` | `updatePolicyById` | `PolicyUpdateSchema` | `200 PolicyResponseSchema` | `200, 401, 403, 404, 409, 422` |

## Files

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/files/init-upload` | `initFileUpload` | `FileInitUploadRequestSchema` | `200 FileInitUploadResponseSchema` | `200, 400, 401, 422` |
| POST | `/api/v1/files/{upload_id}/complete` | `completeFileUpload` | `FileCompleteUploadRequestSchema` | `200 FileCompleteUploadResponseSchema` | `200, 400, 401, 404, 422` |

## Notifications

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/notifications/templates` | `listNotificationTemplates` | — | `200 list[NotificationTemplateResponseSchema]` | `200, 401, 403` |
| POST | `/api/v1/notifications/reset/{reservation_id}` | `resetReservationNotifications` | — | `200` | `200, 401, 403` |
| POST | `/api/v1/notifications/test/{reservation_id}` | `testSendNotification` | — | `200 NotificationOutboxResponseSchema` | `200, 401, 403, 404` |
| GET | `/api/v1/notifications/outbox/{notification_id}` | `getNotificationOutbox` | — | `200 NotificationOutboxResponseSchema` | `200, 401, 403, 404` |
| POST | `/api/v1/notifications/outbox/{notification_id}/retry` | `retryNotification` | — | `200 NotificationOutboxResponseSchema` | `200, 401, 403, 404` |
| POST | `/api/v1/notifications/outbox/{notification_id}/cancel` | `cancelNotification` | — | `200 NotificationOutboxResponseSchema` | `200, 401, 403, 404` |
| GET | `/api/v1/notifications/in-app` | `listInAppNotifications` | — | `200 list[InAppNotificationResponseSchema]` | `200, 401, 403` |

## Participant Forms

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/public/participant-forms/{token}/validate` | `validateParticipantFormToken` | — | `200 ParticipantFormTokenValidationResponse` | `200, 404, 422` |
| GET | `/api/v1/public/participant-form/{token}` | `validateParticipantFormTokenVercel` | — | `200 ParticipantFormTokenValidationResponse` | `200, 404, 422` |
| POST | `/api/v1/public/participant-form/{token}` | `createParticipantViaFormVercel` | `ParticipantPublicCreateSchema` | `201 ParticipantResponseSchema` | `201, 400, 404, 422` |
| GET | `/api/v1/public/participant-forms/{token}/status` | `getPublicParticipantFormStatus` | — | `200 ParticipantFormPublicStatusResponse` | `200, 404` |
| POST | `/api/v1/public/participant-forms/{token}/participants` | `createParticipantViaForm` | `ParticipantPublicCreateSchema` | `201 ParticipantResponseSchema` | `201, 400, 404, 422` |
| GET | `/api/v1/public/participant-forms/risk-release-text` | `getRiskReleaseText` | — | `200` | `200` |
| POST | `/api/v1/reservations/{reservation_id}/participant-form-link` | `generateParticipantFormLink` | `ParticipantFormLinkGenerateRequest` | `201 ParticipantFormLinkGenerateResponse` | `201, 400, 404, 422` |
| POST | `/api/v1/reservations/{reservation_id}/participant-form-link/revoke` | `revokeParticipantFormLink` | — | `200 ParticipantFormLinkStatusResponse` | `200, 404` |
| POST | `/api/v1/reservations/{reservation_id}/participant-form-link/resend` | `resendParticipantFormLink` | — | `200 ReservationResponseSchema` | `200, 401, 403, 404` |
| GET | `/api/v1/reservations/{reservation_id}/participant-form-link` | `getParticipantFormLinkStatus` | — | `200 ParticipantFormLinkStatusResponse \| null` | `200` |

## Sync

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/sync/bootstrap` | `getSyncBootstrap` | — | `200` bootstrap payload | `200, 401` |
| POST | `/api/v1/sync/pull` | `pullSyncChanges` | `SyncPullRequestSchema` | `200 SyncPullResponseSchema` | `200, 400, 401, 422` |
| POST | `/api/v1/sync/push` | `pushSyncOperations` | `SyncPushRequestSchema` | `200 SyncPushResponseSchema` | `200, 400, 401, 409, 422` |

## WhatsApp Webhooks

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| GET | `/api/v1/whatsapp/webhook` | `verifyWebhook` | — | `200` challenge response | `200, 403` |
| POST | `/api/v1/whatsapp/webhook` | `receiveWebhook` | `dict` (raw Meta payload) | `200` | `200` |

## Assistant / Ask

| Método | Ruta | operation_id | Request body | Respuesta principal | Códigos HTTP |
|---|---|---|---|---|---|
| POST | `/api/v1/ask` | `ask_api_v1_ask_post` | `AskRequest` | `200 AskResponse` | `200` |
| POST | `/api/v1/admin/ask` | — (inline) | `AdminAskRequest` | `200 AskResponse` | `200, 401, 403` |

## Notas de mantenimiento

- Esta referencia debe actualizarse cuando cambie cualquier ruta, schema de entrada/salida, `operation_id` o códigos HTTP.
- La fuente de verdad contractual sigue siendo OpenAPI + `ENDPOINT_DOCS` + `BUSINESS_ERROR_CASES`.
- Para detalle narrativo de reglas de negocio, usar `docs/architecture/api.md`.
- Para detalle del pipeline del asistente AI, usar `docs/architecture/chatbot-whatsapp-v2.md`.
- Para detalle de tools MCP internas, usar `docs/architecture/tools.md`.
- Para contratos observados de reservas, usar `docs/mobile/reservations-api-contract-observed.md`.

