# ADR: Separación enlace / reachability / auth en mobile

## Contexto

La app mezclaba el estado del plugin `connectivity_plus`, decisiones de negocio (bloquear login sin “internet”) y la disponibilidad real del backend. Eso generaba falsos “offline” y cortaba operaciones que debían fallar solo ante error HTTP/red real.

## Decisión

1. **ConnectivityService** (`infrastructure/connectivity/`): solo traduce el tipo de enlace del dispositivo a `LinkType` (offline, mobile, wifi, other).
2. **BackendReachabilityService**: hace un GET técnico a `/health` bajo la misma `API_BASE_URL` que el cliente API (incluye `/api/v1`), sin lógica de negocio.
3. **NetworkStatusResolver**: compone `NetworkStatus` para UI, banners y telemetría; no actúa como guardián duro antes de cada login.
4. **AuthRepositoryImpl**: `signIn`, `register` y `changePassword` siempre intentan HTTP; `bootstrapSession` y `refreshSession` degradan a modo local solo ante fallos `network.*` tras intentar el backend; `syncProfileFromRemote` no corta por heurística de enlace.
5. **AuthOperationPolicy** (`application/`): documenta qué operaciones requieren backend vs pueden degradar a local.

## Consecuencias

- La UI puede distinguir “sin enlace”, “enlace pero servidor no responde” y “conectado al backend”.
- Configuración incorrecta de `API_BASE_URL` sigue siendo visible vía reachability, sin sustituir al fallo real en operaciones de auth.
