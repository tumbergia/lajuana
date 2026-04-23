# Backend Offline + Sync v1

Fecha: 2026-04-22

## Objetivo

Definir y dejar implementado el contrato backend para operacion offline-first del frontend mobile, sin duplicar logica de negocio.

## Componentes incorporados

- Endpoints nuevos:
  - `GET /api/v1/sync/bootstrap`
  - `POST /api/v1/sync/pull`
  - `POST /api/v1/sync/push`
  - `POST /api/v1/files/init-upload`
  - `POST /api/v1/files/{upload_id}/complete`
- Colecciones tecnicas nuevas:
  - `sync_changes`
  - `sync_operation_receipts`
  - `file_uploads`
- Metadatos aditivos de sync en entidades mutables:
  - `version`
  - `created_at`
  - `updated_at`
  - `deleted_at`

## Reglas de sincronizacion

- La app sincroniza por streams mediante cursor incremental.
- `push` usa idempotencia por `idempotency_key` y conserva recibos para reintentos seguros.
- Las operaciones de `push` delegan en servicios existentes de dominio; no existe logica paralela.
- `base_version` se valida en updates para evitar merges silenciosos (`sync.stale_version` en conflicto).

## Archivos y comprobantes

- Se adopta flujo de upload en dos pasos:
  1. `init-upload` para presigned URL S3.
  2. `complete` para consolidar estado `ready`.
- `payment_proofs` solo consolida metadata cuando `storage_key` ya esta en estado `ready`.

## Migracion

- Se agrega migracion one-shot en `apps/api/app/migrations/backfill_sync_metadata.py` para normalizar metadatos de sync en datos existentes.
