# ADR-0008: Protocolo offline-first sync

**Fecha:** 2026-06-01  
**Estado:** ✅ Aceptado  

## Contexto

La app móvil es el punto de operación principal y debe funcionar con conectividad intermitente (zonas rurales, montaña). Sin sync offline, el sistema no es operativo.

## Decisión

Protocolo basado en cambios incrementales:
- `SyncChangeDocument` registra cada cambio por entidad
- `GET /sync/pull` devuelve cambios desde un cursor
- `POST /sync/push` recibe cambios locales y los aplica
- `SyncOperationReceipt` garantiza idempotencia
- 4 handlers especializados: Experience, Reservation, Resource, Config

Mobile side:
- SQLite cachea datos remotos
- Repository pattern: remote → cache → fallback
- Connectivity monitoring: `ConnectivityPlusService` + `HttpBackendReachabilityService` → `NetworkStatusResolver`

## Consecuencias

- Operación fluida con conectividad intermitente
- Sin conflictos de escritura (push sincrónico, lock por entidad)
- Caché SQLite permite UI inmediata sin esperar red
- 4 handlers en backend, cada uno con ≤5 dependencias
- SyncService: 587 → 220 líneas post-refactor
