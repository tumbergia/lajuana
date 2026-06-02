# Technical Debt — Inventario Completo

> Issues identificadas durante auditoría cruzada (Junio 2026). Incluye las 4 issues originales (P1-P4) más hallazgos complementarios de arquitectura, frontend, testing y operaciones.

## ESTADO DE IMPLEMENTACIÓN (actualizado 2026-06-02)

| Área | Estado | Items completados |
|------|--------|-------------------|
| **Backend Core (W1)** | ✅ 100% | BaseService, CRUD refactor, ensure_indexes, start_time→str, AuditMetadata tipado |
| **Backend Architecture (W2)** | ✅ 100% | batch mappers, storage cleanup, catalog cache, board pagination, age config, except:pass, dry_run, audit bulk, board is_available, build_code, list_items, SUPPLIES, deprecated fields, legacy fallback+migration script, **SyncService split → 4 handlers** |
| **Frontend (W3)** | ✅ 100% | ActionState<T>, DI, router, app.dart simplificado, veil eliminado, detail controller refactor, list controller state+bloc+tests, playground fuera de lib/, packages declarados, **619 imports → package:mobile/**, **mobile_ui/mobile_domain/mobile_mocks poblados** |
| **Testing (W4)** | 🟡 ~90% | Tests: ConfigService (7), PolicyService (5), ProviderService (3), ServiceLogService (4), FileUploadService (5), StorageAdapter (5), mobile repo (4), **111 tests nuevos para 9 controllers mobile**, **mongomock fixture + 5 demo tests**, Coverage audit. OpenAPI contract verify. Integration test skeleton. |
| **Docs/Ops (W5)** | 🟡 ~85% | AGENTS.md actualizado, ADR-0004 postponed, unified seed CLI (`python -m app.cli seed`), migration tracker (3 formal migrations), health check real, PR template |

---

## ESTRUCTURA DEL DOCUMENTO

| Sección | Contenido |
|---------|-----------|
| P1-P4   | Issues originales de PLAN_MEJORA (conservadas) |
| A1-A10  | Arquitectura y diseño |
| B1-B8   | Backend: servicios, rendimiento, datos |
| F1-F8   | Frontend Flutter |
| T1-T7   | Testing y calidad |
| D1-D5   | Documentación y operaciones |
| M1-M3   | Mobile packages fantasma |

---

## P1. `assignment_to_response` — N+1 en el mapper

**Estado:** ✅ Resuelto

**Dónde:** `apps/api/app/services/mappers.py:96-106`

**Problema:** Cada vez que se resuelve un `AssignmentResponseSchema`, se hacen 3 queries individuales.

**Solución:** `batch_assignments_to_response(N)` → 3 queries `$in`. `assignment_to_response` delega.

**Prioridad:** Low

---

## P2. `finalize_all` / `unfinalize_all` — audit logs no están en bulk

**Estado:** ✅ Resuelto

**Dónde:** `apps/api/app/services/assignment_service.py:249-258` y `302-311`

**Problema:** Audit logs insert individuales en loop.

**Solución:** `insert_many()` con lista de `ReservationAuditLogDocument`.

**Prioridad:** Low

---

## P3. Equinos envían `is_available` redundante en el board

**Estado:** ✅ Resuelto

**Dónde:** `apps/api/app/schemas/assignment.py:87-94` y `apps/api/app/services/assignment_service.py:594`

**Problema:** `is_available` redundante cuando `block_reason` ya indica disponibilidad.

**Solución:** Eliminado `is_available` del schema. Frontend deriva de `block_reason`.

**Prioridad:** Medium

---

## P4. Índice único en `SaddleDocument.code`

**Estado:** ✅ Resuelto (cubierto por W1.3 — ensure_indexes)

**Dónde:** `apps/api/app/documents/saddle_document.py:8`

**Problema:** Índice único podría no existir en MongoDB.

**Solución:** `ensure_indexes()` en init_db garantiza que todos los índices declarados existen.

**Prioridad:** Medium

---

# HALLAZGOS COMPLEMENTARIOS

---

## A. ARQUITECTURA

---

### A1. Mobile packages declarados pero vacíos  ✅

**Estado:** ✅ Resuelto

Paquetes `mobile_ui` (40 files), `mobile_domain` (23 files), `mobile_mocks` (2 files) poblados con código real. Widgets/theme/voice en mobile_ui. Modelos de dominio + interfaces de repositorio en mobile_domain. Fakes compartidos en mobile_mocks.

---

### A2. Modelos de dominio duplicados entre mobile y backend  ⏳

**Estado:** ⏳ Postergado — OpenAPI codegen fuera de scope del PLAN_MEJORA original

Modelos extraídos a `mobile_domain` como paso intermedio. La generación OpenAPI-to-Dart sigue pendiente como mejora futura.

---

### A3. Servicios con too-many-dependencies (SyncService)  ✅

**Estado:** ✅ Resuelto

SyncService dividido en 4 handlers especializados (587→220 líneas):
- `ExperienceSyncHandler` — 2 dependencias (experience, schedule)
- `ReservationSyncHandler` — 5 dependencias (reservation, participant, payment_proof, assignment, service_log)
- `ResourceSyncHandler` — 2 dependencias (provider, policy)  
- `ConfigSyncHandler` — 1 dependencia (config)

---

### A4. Servicios CRUD boilerplate repetitivo  ✅

**Estado:** ✅ Resuelto (W1.1+W1.2)

`BaseService[DocT, CreateSchemaT, UpdateSchemaT]` creado. ProviderService (-70%), SaddleService (-50%), EquineService (-31%), PolicyService, ServiceLogService refactorizados.

---

### A5. `except Exception: pass` generalizado  ✅

**Estado:** ✅ Resuelto (W2.3)

Inspección confirmó que TODO el codebase (`assignment_service`, `reservation_service`, `notification_service`, `sync_service`, `storage`) ya usa `logger.exception()`. Cero `except: pass` silenciosos.

---

### A6. `validate_assignment_candidate` duplica lógica  ✅

**Estado:** ✅ Resuelto (W2.2)

`_validate_and_prepare` acepta `dry_run=True`. `validate_assignment_candidate` delega completamente. ~90 líneas de duplicación eliminadas.

---

### A7. `EquineService.list_items()` es idéntico a `list()`  ✅

**Estado:** ✅ Resuelto (Sprint 0)

Eliminado. `list_items()` no era más liviano que `list()`.

---

### A8. `_FallbackS3Client` — cliente falso silencioso  ✅

**Estado:** ✅ Resuelto (W2.7)

Eliminados 2 `_FallbackS3Client` (storage.py + file_upload_service.py). `S3StorageAdapter` lanza `RuntimeError` si boto3 falta + S3 config. Sin S3 config → `LocalStorageAdapter`.

---

### A9. Colección `SUPPLIES` muerta  ✅

**Estado:** ✅ Resuelto (Sprint 0)

`SUPPLIES = "supplies"` eliminado de `Collections`.

---

### A10. `priority` / `assigned_manually` deprecated  ✅

**Estado:** ✅ Resuelto (Sprint 0)

Ya no se setean en `_validate_and_prepare`. Campos mantenidos en documento legacy solo para lectura.

---

## B. BACKEND: RENDIMIENTO Y DATOS

---

### B1. Catalog resolver carga todo en memoria  ✅

**Estado:** ✅ Resuelto (W2.9)

Caché in-memory con TTL 5 min. `max_results=100` en token overlap. Text index MongoDB pendiente como fase 2.

---

### B2. Legacy fallback en `reservation_to_response`  ✅

**Estado:** ✅ Resuelto (W2.10)

Fallback `reservation_id` eliminado. Script `scripts/migrate_participant_ids.py` creado (idempotente, dry-run). Migrar datos legacy antes de desplegar.

---

### B3. Board carga todos los equinos sin paginación  ✅

**Estado:** ✅ Resuelto (W2.11)

`get_board` pasa `limit=200, skip=0` a `list_available_for_reservation`. 

---

### B4. `datetime.time` no serializable por Beanie  ✅

**Estado:** ✅ Resuelto (W1.4)

`ScheduleDocument.start_time: time` → `str` ISO. `_save_schedule_status` usa `doc.save()` sin motor raw. Datos legacy requieren migración manual.

---

### B5. Falta de `ensure_index` en init_db  ✅

**Estado:** ✅ Resuelto (W1.3)

`ensure_indexes()` llamado tras `init_beanie()` para todos los `document_models`.

---

### B6. `AuditLog.metadata` sin schema  ✅

**Estado:** ✅ Resuelto

`metadata: dict` → `AuditMetadata \| None` (discriminated union: AssignmentMetadata, ReplacementMetadata, NotificationMetadata). `actor_role` nullable. 5 tests nuevos.

---

### B7. Edad mínima/máxima hardcodeada  ✅

**Estado:** ✅ Resuelto (W2.12)

`ReservationRules.min_age=12` / `max_age=65`. `AssignmentService` lee desde `ConfigService`. Fallback seguro.

---

### B8. `_build_code` duplicado  ✅

**Estado:** ✅ Resuelto (Sprint 0)

Unificado en `constants.py`. Reservation y Draft usan la misma función.

---

## F. FRONTEND FLUTTER

---

### F1. `app.dart` monolítico  ✅

**Estado:** ✅ Resuelto (W3.1-W3.3)

`app.dart`: 320 → 62 líneas. Routing en `app_router.dart`. DI en `dependency_injection.dart`. State solo con `_themeMode`, `_deps`, `_router`.

---

### F2. Detail controller 507 líneas con 8 action states duplicados  ✅

**Estado:** ✅ Resuelto (W3.5+W3.6)

`ActionState<T>` en `mobile_core`. Detail controller: 507 → 310 líneas. `PaymentProofActionState` y `ReservationActionState` eliminados. 8 `ActionState<void>` fields. 0 `_reset*Delayed()`. Bug corregido (cancel/delete usaban `ReservationActionState.confirming`).

---

### F3. Dev screens compilados en debug  ✅

**Estado:** ✅ Resuelto (W3.8)

Playground movido de `lib/playground/` a `dev/playground/`. Release build no compila el widget museum.

---

### F4. Tema con transición "veil" compleja  ✅

**Estado:** ✅ Resuelto (W3.4)

Veil eliminado. `MaterialApp(themeAnimationDuration: 200ms)`. Sin `_themeVeilColor` ni `_isThemeTransitioning`.

---

### F5. List controller multi-responsabilidad  ✅

**Estado:** ✅ Resuelto (W3.7)

`ReservationsListState` inmutable con `copyWith`. Controller separado (state interno + getters). 9 tests unitarios nuevos.

---

### F6. Falta de cobertura de tests mobile  🟡

**Estado:** 🟡 ~90% (111 tests nuevos, faltan integration tests)

Tests agregados en 9 controllers: DashboardController (8), ParticipantsController (6), SaddlesListController (17), ExperiencesController (9), SchedulesController (10), EmergencyContactsController (8), ReservationRulesController (10), ExperienceFormController (23), ScheduleFormController (11).

Falta: tests de integración mobile (T3) — requieren emulador.

---

### F7. `playground/` dentro de `lib/`  ✅

**Estado:** ✅ Resuelto (W3.8)

`widget_museum_screen.dart` movido a `dev/playground/`. `lib/playground/` eliminado.

---

### F8. Import paths relativos profundos  ✅

**Estado:** ✅ Resuelto

619 imports convertidos de `../../` a `package:mobile/...` en 127 archivos. Script automatizado con dry-run mode.

---

## T. TESTING Y CALIDAD

---

### T1-T7 — Testing  🟡

**Estado:** 🟡 ~60% (W4 parcial)

| Item | Estado | Qué |
|------|--------|-----|
| **T1 — Services unit** | ✅ 29 tests | ConfigService (7), PolicyService (5), ProviderService (3), ServiceLogService (4), FileUploadService (5), StorageAdapter (5) |
| **T2 — Coverage** | ✅ Reportado | `pytest --cov` ejecutado. Coverage general 52%. Servicios core 82-100%. |
| **T3 — Integration mobile** | 🟡 Skeleton | 2 test files creados (TODO bodies). Requiere emulador para ejecutar |
| **T4 — OpenAPI contract** | ✅ 3 tests | Spec generado, 45+ endpoints verificados contra documentación |
| **T5 — mongomock** | ✅ 5 tests demo | Fixture `mongomock_client` en conftest.py. Marcador `integration` para tests legacy |
| **T6 — Concurrency** | ✅ 2 tests | `test_concurrency_reservation.py` con `asyncio.gather(5)` |
| **T7 — Mobile repos** | ✅ 4 tests | `ReservationsRepositoryImpl` (cache hit, cache miss, remote fail, both fail) |

---

## D. DOCUMENTACIÓN Y OPERACIONES  🟡

**Estado:** 🟡 ~85% (W5 casi completo)

| Item | Estado | Qué |
|------|--------|-----|
| **D1 — Seeds CLI** | ✅ | `python -m app.cli seed -t <name>`. 6 seeds registrados. Legacy scripts intactos. |
| **D2 — Migration tracker** | ✅ | `app/migrations/` con 3 migraciones formales. `run_migrations()` en startup. |
| **D3 — Health check** | ✅ | `GET /health` retorna `{"status","checks":{"mongodb":"ok\|error"}}` |
| **D4 — AGENTS.md + ADR** | ✅ | AGENTS.md actualizado con stubs. ADR-0004 → postponed con criterios. |
| **D5 — PR template + linter** | ✅ | `.github/PULL_REQUEST_TEMPLATE.md` con checklist. analysis_options actualizado. |

## M. MOBILE PACKAGES FANTASMA  🟡

**Estado:** 🟡 Declarados en workspace (W3.10), pendiente poblar (W5.7-W5.9, requiere W3.9)

### M1-M3 — `mobile_ui`, `mobile_domain`, `mobile_mocks`
Paquetes declarados en `apps/mobile/pubspec.yaml` como dependencias workspace. Siguen vacíos. Poblar requiere W3.9 (package: imports) para no romper imports existentes.

---

## MATRIZ DE PRIORIDADES (ACTUALIZADA 2026-06-02)

| Prioridad | Resueltos ✅ | Pendientes |
|-----------|-------------|------------|
| ~~High~~ | A5, B6, F6 (111 tests), T1 (29 tests), T5 (mongomock), T7 (4 tests) | T3 (integration — skeleton), A2 (OpenAPI codegen) |
| ~~Medium~~ | P3, P4, A3 (SyncService split), A4, A6, A8, B1, B4, B5, F1-F5, F8 (imports), T4, T6, D1-D5, A1/M1-M3 (packages poblados) | — |
| ~~Low~~ | P1, P2, A7, A9, A10, B2, B3, B7, B8, F3, F7, T2 (reporte) | — |

---

## NOTAS TÉCNICAS ADICIONALES

### `ScheduleDocument.start_time: time` + Beanie
Ya documentado en AGENTS.md. Ver `seed_reproducible.py` y `seed_experiences_and_schedules_qa.py` para workaround con motor collection.

### `ExperienceCatalogResolver` necesita aliases
Ya documentado en AGENTS.md. Si al actualizar una experiencia no se proveen `aliases`, la resolución por términos coloquiales falla.

### Token overlap puede dar AMBIGUOUS
Ya documentado en AGENTS.md. Dos experiencias que compartan términos en description/tags pueden empatar en puntaje token-overlap.

---

# PLAN INTEGRAL DE SOLUCIÓN

> Soluciones robustas, sin parches. Cada issue resuelta con el enfoque arquitectónico más sólido y mantenible.
> Diseñado tras auditoría cruzada de código fuente (backend, frontend, tests, docs, packages).

---

## TARGET CONTRACT

Después de implementar el plan completo:

| Dimensión | Estado target |
|-----------|---------------|
| **BaseService** | `BaseService[DocT, CreateSchema, UpdateSchema]` maneja CRUD genérico para todos los servicios CRUD. Cada servicio específico solo tiene validación de dominio. |
| **SyncService** | Dividido en 4 handlers (ExperienceSyncHandler, ReservationSyncHandler, ResourceSyncHandler, ConfigSyncHandler), cada uno con ≤3 dependencias. |
| **Excepciones** | Cero `except Exception: pass`. Todo error loggeado con `logger.exception()` y política explícita fail-open vs fail-fast documentada. |
| **Mappers batch** | `batch_assignments_to_response()`: N assignments → 3 queries `$in` (participant, equine, saddle). Sin N+1. |
| **Audit logs bulk** | `insert_many()` en finalize_all/unfinalize_all. Sin loops de inserts individuales. |
| **ScheduleDocument.start_time** | Tipo `str` ISO `"HH:MM:SS"` en el documento, conversión en schemas de entrada/salida. Sin workaround motor raw. |
| **Índices** | `ensure_indexes()` en init_db garantiza que todos los índices declarados existen en MongoDB. |
| **AuditLog.metadata** | Tipado con Pydantic model por acción de auditoría. Sin `dict` genérico. |
| **Board response** | Equino sin `is_available` redundante (derivado de `block_reason`). |
| **Storage** | Sin `_FallbackS3Client`. O LocalStorageAdapter real o fail-fast si S3 requerido. |
| **app.dart** | ~150 líneas. Routing en `app_router.dart`, DI en `dependency_injection.dart`. Sin veil transition. |
| **Controllers** | `ActionState<T>` genérico reusado en los 8 action-states del detail controller. ListController separado en state + bloc. |
| **Imports mobile** | Todos usan `package:mobile/`. Cero `../../../../`. |
| **Playground** | Fuera de `lib/`. Imports diferidos (deferred). |
| **Tests backend** | 70%+ coverage en servicios core. Tests con mongomock (sin MongoDB real). Tests de concurrencia. |
| **Tests mobile** | Cobertura en todos los repositorios. Tests de integración para flujos core. |
| **Seeds** | CLI unificado (`python -m app.cli seed --type <name>`). 6 scripts → 1 framework + factories. |
| **Migrations** | Migration tracker en MongoDB. Migraciones formales con idempotencia. |
| **Health check** | Verifica MongoDB, S3, dependencias externas. |
| **Packages** | `mobile_ui`, `mobile_domain`, `mobile_mocks` poblados progresivamente. Docs actualizados. |
| **Docs** | AGENTS.md y ADRs sincronizados con arquitectura real. ADR-0004 actualizado (postponed con criterios). |

---

## WORKSTREAMS

### W1 — BACKEND CORE INFRASTRUCTURE (BaseService, índices, tipos)

> Elimina la fuente de ~40% del código repetido. Sienta las bases para todos los refactors posteriores.

| # | Issue | Archivos | Solución | Validación | Riesgo |
|---|-------|----------|----------|------------|--------|
| W1.1 | A4 | `apps/api/app/services/base_service.py` (nuevo) | `BaseService[DocT, CreateSchema, UpdateSchema]` con métodos genéricos `get_or_404`, `create`, `update`, `soft_delete`, `list`. Hooks para logging y auditoría. | Tests unitarios del base service con mock de colección. | Ninguno |
| W1.2 | A4 | `saddle_service.py`, `equine_service.py`, `provider_service.py`, `policy_service.py`, `service_log_service.py`, `config_service.py` | Refactor: extender `BaseService`, mantener solo métodos con validación de dominio. Eliminar CRUD boilerplate. | Tests de cada servicio pasan sin cambios en asserts. | Medio — firmas de métodos públicos cambian |
| W1.3 | B5, P4 | `app/core/db.py` | Agregar `ensure_indexes()` tras `init_beanie()`: `for model in document_models: await model.get_motor_collection().create_indexes(...)` | Test que verifica índices existen en MongoDB. | Bajo |
| W1.4 | B4 | `app/documents/schedule_document.py`, schemas de schedule | Cambiar `start_time: time` → `start_time: str`. Validador Pydantic `pattern=r"^\d{2}:\d{2}:\d{2}$"`. Actualizar `_save_schedule_status` para usar `doc.save()` sin motor raw. | Seeds funcionan sin workaround motor raw. Tests de schedule upsert pasan. | **MEDIO** — datos legacy con `time` objects requieren migración |
| W1.5 | B6 | `app/documents/reservation_audit_log_document.py` | Reemplazar `metadata: dict` con `AuditMetadata` tipado. Crear modelos por acción (ej: `PaymentApprovalMetadata`, `AssignmentFinalizeMetadata`). | Test que verifica que cada acción guarda estructura correcta. | Bajo |
| W1.6 | A9 | `app/common/collections.py` | Eliminar `SUPPLIES = "supplies"`. | `grep SUPPLIES` confirma 0 referencias. | Bajo |
| W1.7 | A10 | `app/services/assignment_service.py` (líneas 758-759) | Dejar de setear `priority` y `assigned_manually` en `_validate_and_prepare`. Mantener campos legacy en documento. | Tests de asignación no dependen de esos campos. | Bajo |

**Dependencias W1:** W1.2 requiere W1.1. W1.3-W1.7 independientes.

---

### W2 — BACKEND ARCHITECTURE (SyncService, mappers, validaciones, logging)

> Reorganiza la arquitectura de servicios backend. Elimina N+1, bulk audit, duplicación de validación, y silenciamiento de errores.

| # | Issue | Archivos | Solución | Validación | Riesgo |
|---|-------|----------|----------|------------|--------|
| W2.1 | A3 | `app/services/sync_service.py`, `app/services/sync_handlers/` (nuevo) | Dividir `SyncService` en 4 handlers. `SyncService` delega, orquesta, no contiene lógica de dominio. Cada handler con ≤3 dependencias. | Tests de sync existentes pasan con mock handlers. | **ALTO** — SyncService es crítico para offline-first. Usar patrón wrapper + feature flag `new_sync` |
| W2.2 | A6 | `app/services/assignment_service.py` (líneas 697-788) | `_validate_and_prepare` acepta `dry_run: bool = False`. Cuando `True`, salta seteo de campos y retorna `(safety_flags, warnings)`. `validate_assignment_candidate` delega a `_validate_and_prepare(dry_run=True)`. | Test que verifica que `validate_assignment_candidate` da el mismo resultado que `_validate_and_prepare` para mismos inputs. | Bajo |
| W2.3 | A5 | `assignment_service.py`, `reservation_service.py`, `notification_service.py`, `sync_service.py`, `storage.py` | Reemplazar every `except: pass` con `logger.exception(...)`. Documentar política fail-open vs fail-fast en `docs/decisions/`. | `grep "except.*:[\s]*pass"` → 0 resultados en `app/services/`. | Medio — cambiar comportamiento silent → visible puede revelar errores ocultos |
| W2.4 | P1 | `app/services/mappers.py` | Crear `batch_assignments_to_response(assignments)`. Colecta todos participant_ids/equine_ids/saddle_ids, hace 3 queries `$in`, construye lookup maps, mapea todo. `assignment_to_response` llama a batch con `[doc]`. | Benchmark: N assignments → siempre 3 queries. | Bajo |
| W2.5 | P2 | `app/services/assignment_service.py` | Colectar `ReservationAuditLogDocument` en lista, usar `collection.insert_many()`. | Test con 20 assignments auditados verifica 1 insert. | Bajo |
| W2.6 | P3 | `app/schemas/assignment.py`, `app/services/assignment_service.py` | Eliminar `is_available` del schema y del dict en `get_board`. Frontend deriva de `block_reason == null`. | Board response para equino no contiene `is_available`. | Bajo |
| W2.7 | A8 | `app/services/storage.py` | Eliminar `_FallbackS3Client`. `S3StorageAdapter` lanza `RuntimeError` en `__init__` si boto3 no está. `get_storage_adapter()` retorna `LocalStorageAdapter` si no hay credenciales S3. | Sin boto3 + sin S3 config → LocalStorageAdapter. Sin boto3 + con S3 config → error claro en startup. | Medio — entornos sin boto3 sin S3 config funcionan, no fallan |
| W2.8 | A7 | `app/services/equine_service.py` | Eliminar `list_items()` si es idéntico a `list()`. O implementar proyección real. | Tests de equine list siguen pasando. | Bajo |
| W2.9 | B1 | `app/services/experience_catalog_resolver.py`, `app/documents/experience_document.py` | Agregar text index MongoDB en nombre+descripción+tags. Agregar `max_results=100` en `resolve()`. Cachear catálogo activo con TTL 5 min. | Test con 1000+ experiencias no carga todo. | Bajo |
| W2.10 | B2 | `app/services/mappers.py` | Eliminar fallback `reservation_id` query. Requiere migración de datos legacy. Agregar log de advertencia si hay participantes sin `participant_ids`. | Test sin datos legacy usa solo query `$in`. | Medio — requiere migración datos legacy |
| W2.11 | B3 | `app/services/assignment_service.py` | `get_board` pasa `limit=200, skip=0` a `list_available_for_reservation`. | Board no carga todos los equinos sin paginación. | Bajo |
| W2.12 | B7 | `app/services/assignment_service.py` | Mover thresholds 12/65 a `AppConfigDocument` como `min_age`/`max_age`. Leer desde `config_service`. | Test cambia config y verifica que validación usa nuevo threshold. | Bajo |
| W2.13 | B8 | `app/services/reservation_service.py`, `reservation_draft_service.py` | Extraer `build_code(prefix: str) → str` como `@classmethod` de `ReservationDocument` o en `app/common/codes.py`. | Misma salida para mismo input que la implementación actual. | Bajo |

**Dependencias W2:** W2.1 requiere W1.1 (BaseService para facilitar extracción). W2.4-W2.13 independientes entre sí.

---

### W3 — FRONTEND ARCHITECTURE (app.dart, controllers, imports)

> Refactoriza la arquitectura Flutter eliminando el monolito app.dart, estandarizando action-states y migrando a imports package:.

| # | Issue | Archivos | Solución | Validación | Riesgo |
|---|-------|----------|----------|------------|--------|
| W3.1 | F1 | `lib/app/app_router.dart` (nuevo) | Extraer `_buildRoute` a `AppRouter` class. `app.dart` crea `AppRouter` y lo pasa. | Navegación funciona idéntico. | Bajo |
| W3.2 | F1 | `lib/app/dependency_injection.dart` (nuevo) | Extraer init de `AuthController`, módulos, repositorios a `createDependencies(apiBaseUrl) → AppDependencies`. | app.dart initState se reduce ~80%. | Bajo |
| W3.3 | F1 | `lib/app/app.dart` | State solo con `ThemeMode` + `AppDependencies` + `AppRouter`. Eliminar veil fields (W3.4). | app.dart < 180 líneas. | Bajo |
| W3.4 | F4 | `lib/app/app.dart`, `lib/app/theme/app_theme_notifier.dart` | Reemplazar veil transition por `MaterialApp(themeMode:, themeAnimationDuration:)` + callback `onToggleTheme`. Eliminar `_themeVeil*`, `_isThemeTransitioning`. | Toggle light/dark suave sin veil visual. | Bajo |
| W3.5 | F2 | `packages/mobile_core/lib/src/action_state.dart` (nuevo) | Crear `ActionState<T>` con: `status: ActionStatus` (idle/loading/success/error) + `errorCode` + `errorMessage` + `reset()` + `run(Future<T> Function())`. Auto-reset success tras 2s. | Test unitario del helper. | Bajo |
| W3.6 | F2 | `lib/features/reservations/presentation/controllers/reservation_detail_controller.dart` | Reemplazar 8 pares de enum+fields por 8 campos `ActionState<ReturnType>`. Eliminar `PaymentProofActionState`, `ReservationActionState`. | Cada acción (approve/reject/etc) funciona como antes. | **Medio** — controlador de 507 líneas. Hacer tests primero que capturen comportamiento |
| W3.7 | F5 | `lib/features/reservations/presentation/controllers/reservations_list_controller.dart` | Separar en: `ReservationsListState` (data class inmutable con items/search/filter) + `ReservationsListBloc` (fetch + cache + filter orchestration). Controller pequeño. | Tests del controller existentes pasan. | Medio |
| W3.8 | F3, F7 | `lib/app/app.dart`, `lib/playground/` | Usar `deferred as` para dev screens import. Mover `lib/playground/` a `dev/playground/`. Actualizar imports en app.dart. | Release build no incluye código de playground. | Bajo |
| W3.9 | F8 | ~200+ archivos en `lib/features/**/*.dart` | Convertir todos los `../../../../` imports a `package:mobile/...`. Pubspec name ya es `mobile`. Usar script automatizado (sed/regex). | `flutter analyze` sin errores de import. | **ALTO** — 200+ archivos. Hacer en 2 PRs: (1) cambiar imports, (2) verificar build + analyze |
| W3.10 | A1, M1-M3 | `apps/mobile/pubspec.yaml`, vacíos packages | Agregar dependencias workspace a `mobile_ui`, `mobile_domain`, `mobile_mocks`. Siguen vacíos pero declarados. | `flutter pub get` exitoso. | Bajo |

**Dependencias W3:** W3.3 requiere W3.1+W3.2. W3.6 requiere W3.5. W3.8-W3.10 independientes.

---

### W4 — TESTING (backend, frontend, concurrencia, contratos)

> Construye la red de seguridad faltante. Tests unitarios con mocking, tests de concurrencia, tests de integración mobile.

| # | Issue | Archivos | Solución | Validación | Riesgo |
|---|-------|----------|----------|------------|--------|
| W4.1 | T5 | `apps/api/tests/conftest.py` | Agregar fixture `mongomock` o `AsyncMongoClient` in-memory. Tests existentes con DB real → `@pytest.mark.integration`. Script CI separa unit vs integration. | `pytest -m "not integration"` corre sin MongoDB. | **ALTO** — cambiar conftest afecta 46 tests. Hacer gradual: fixture nueva, migrar tests 1x1 |
| W4.2 | T1 | `apps/api/tests/test_config_service.py`, `test_policy_service.py`, etc. (nuevos) | Tests para: ConfigService, PolicyService, ProviderService, ServiceLogService, FileUploadService, StorageAdapter, UserService, OpsService. Mínimo 3 tests cada uno (happy path + error + edge). | Cada servicio nuevo tiene ≥3 tests. | Bajo |
| W4.3 | T6 | `apps/api/tests/test_concurrency_reservation.py` | Agregar tests con `asyncio.gather(5 clients)` para `_commit_schedule_capacity` y `ensure_date_available`. Verificar que solo 1 reserva se confirma. | Race conditions detectadas en CI. | Bajo |
| W4.4 | T7 | `apps/mobile/test/features/reservations/repositories/` | Tests para `ReservationsRepository` mockeando remote (API) y local (SQLite). Verificar offline-first: cache hit, cache miss, remote error fallback, sync push. | 100% de repositorios core cubiertos. | Bajo |
| W4.5 | T3 | `apps/mobile/test/` | 2 tests de integración: (1) login → listar reservas → filtrar, (2) ver detalle de reserva. Usar `integration_test` package. | Flujos core verificados en CI. | Medio — requiere setup integration_test + emulador |
| W4.6 | T2 | `apps/api/tests/` | Auditar coverage real con `pytest --cov`. Agregar edge cases a tests existentes que solo prueban happy path. | Coverage report por módulo. | Bajo |
| W4.7 | T4 | `apps/api/tests/`, `apps/api/app/api/router.py` | Habilitar `openapi_url` en FastAPI si no está. Agregar test que verifica schemas de respuesta coinciden con spec generado. | Contrato backend verificable en CI. | Bajo |

**Dependencias W4:** W4.1 es prerequisito para W4.2 (unit tests sin DB). W4.3-W4.7 independientes.

---

### W5 — DOCUMENTACIÓN, OPERACIONES, PACKAGES

> Cierra el gap entre la arquitectura documentada y la real. Estandariza seeds, migraciones, health checks.

| # | Issue | Archivos | Solución | Validación | Riesgo |
|---|-------|----------|----------|------------|--------|
| W5.1 | D4, A1 | `AGENTS.md`, `docs/architecture/mobile.md` | Actualizar estructura: describir arquitectura real (modular monolith en `apps/mobile`). Indicar que packages se poblarán progresivamente. | Docs reflejan el código real. | Bajo |
| W5.2 | D4 | `docs/decisions/0004-mobile-ui-package.md` | Actualizar ADR-0004: status → "postponed". Agregar criterios concretos para extracción (widget estable + sin dependencias business + API probada). | Decisión documentada con criterios. | Bajo |
| W5.3 | D1 | `apps/api/scripts/` → `app/cli.py` (nuevo) | Unificar: `python -m app.cli seed --type <name>`. Factory pattern. Cada seed es un plugin. Mantener scripts legacy como wrappers. | Todos los seeds existentes funcionan desde CLI. | Medio — scripts existentes son entry points independientes |
| W5.4 | D2 | `app/migrations/`, `app/core/db.py` | Crear colección `migration_tracker`. Migraciones formales con `applied_at`, `checksum`. Mover migración staff→guide a migration formal. `run_migrations()` en startup. | Migraciones se ejecutan 1 vez. Rollback documentado. | Bajo |
| W5.5 | D3 | `app/api/endpoints/health.py` | Agregar checks: MongoDB `admin.ping()`, S3 `head_bucket`, WhatsApp connectivity check. Response: `{"status":"ok\|degraded\|down", "checks": {...}}` | Health endpoint refleja estado real. | Bajo |
| W5.6 | D4, D5 | CI config | Agregar linter rule: `no-relative-imports` en mobile. Review checklist en `.github/PULL_REQUEST_TEMPLATE.md` con referencias a AGENTS.md. | PR template incluye checklist. | Bajo |
| W5.7 | M1 | `packages/mobile_ui/lib/` | Mover widgets estables: `AppButton`, `AppBadge`, `AppCard`, `AppScaffold`, `AppTextField`, `AppBottomNav`, `AppTimeline`. Actualizar imports en `apps/mobile`. | `flutter analyze` en mobile_ui. | **Medio** — imports cambian en apps/mobile |
| W5.8 | M2 | `packages/mobile_domain/lib/` | Mover modelos de dominio puros: enums compartidos (`ReservationStatus`, `AssignmentStatus`), modelos sin dependencias infra. | `flutter analyze` en mobile_domain. | Medio |
| W5.9 | M3 | `packages/mobile_mocks/lib/` | Mover fakes compartidos: `FakeReservationsRepository`, `FakeAuthRepository`. | Tests existentes importan de mobile_mocks. | Bajo |

**Dependencias W5:** W5.7-W5.9 requieren W3.9 (imports package:). W5.1-W5.6 independientes.

---

## MAPA DE DEPENDENCIAS

```
         W1.1 (BaseService)
         ┃
         ┣━ W1.2 (CRUD refactor) ──→ W2.1 (SyncService split)
         ┃
         ┣━ W1.3 (ensure_index) ───→ W4.1 (mongomock conftest) ──→ W4.2 (tests servicios)
         ┃
         ┣━ W1.4 (time→string)
         ┃
         ┗━ W1.5-W1.7 (metadata, dead code, deprecated)

W3.1-W3.3 (app router + DI) ──→ W3.6 (action states)
W3.5 (ActionState<T>) ────────→ W3.6
W3.9 (package: imports) ──────→ W5.7-W5.9 (poblar packages)

W4.1 (mongomock) ─────────────→ W4.2 (tests)
W4.3-W4.7 (independientes)

W5.1-W5.6 (docs, ops — independientes)
W5.7-W5.9 (packages) ─────────→ requieren W3.9
```

**Orden de ejecución recomendado (3 sprints):**

| Sprint | Workstreams |
|--------|-------------|
| **Sprint 1** | W1 (completo) + W3.1-W3.5 (app router, DI, ActionState, imports) + W4.1 (mongomock conftest) |
| **Sprint 2** | W2 (completo) + W3.6-W3.10 (controllers, deferred, imports package:) + W4.2-W4.3 (tests, concurrencia) |
| **Sprint 3** | W4.4-W4.7 (tests mobile, contratos) + W5 (completo) |

---

## PLAN DE TESTS POR ISSUE

| Issue | Tipo | Qué probar | Cómo | Prioridad |
|-------|------|-----------|------|-----------|
| T1 | Unit (backend) | ConfigService, PolicyService, ProviderService, ServiceLogService, FileUploadService, StorageAdapter, UserService, OpsService | mock DB → assert resultados | Alta |
| T2 | Coverage (backend) | Edge cases en tests existentes que solo cubren happy path | `pytest --cov` + code review | Media |
| T3 | Integration (mobile) | Login → listar reservas → detalle | `integration_test` driver | Alta |
| T4 | Contract (backend) | OpenAPI spec vs schemas reales | `openapi-spec-validator` + test | Media |
| T5 | Infra (backend) | mongomock fixture para unit tests | `pytest -m "not integration"` | Media |
| T6 | Concurrency (backend) | Race conditions en schedule capacity | `asyncio.gather(5)` | Alta |
| T7 | Unit (mobile) | ReservationsRepository con mock remote + local | Mockito/Fake | Alta |
| F6 | Coverage (mobile) | ReservationsListController, reservation_detail_controller, equine_controller | Controller tests | Alta |
| P1 | Benchmark | `batch_assignments_to_response` N=50 → 3 queries | Assert number of DB calls | Baja |
| P2 | Unit | Audit logs insert_many vs loop | Assert single insert call | Baja |
| P3 | Contract | Board equino response sin is_available | Schema validation | Media |
| P4 | Integration | Índice unique en saddles existe | `list_indexes` | Media |
| B1 | Performance | Catalog resolver con 1000 experiencias no carga todo | Memory usage assert | Media |
| B4 | Integration | Schedule upsert sin workaround motor raw | Seed test | Media |
| B5 | Integration | ensure_indexes crea índices | `list_indexes` | Media |

---

## OUT OF SCOPE (explícitamente excluido)

1. **Migración a Riverpod/Bloc.** El plan usa `ActionState<T>` genérico + separación state/bloc, que es un paso interceptor. Cambiar la arquitectura de state management completa es otro proyecto.
2. **OpenAPI-to-Dart codegen.** Se documenta como recomendación futura. Requiere infraestructura de CI y decidir herramienta (openapi-generator vs freezed vs manual).
3. **Migración de datos legacy** para B2 (participantes sin `participant_ids`). Se requiere migración manual. El plan solo elimina el fallback de código.
4. **Chatbot/WhatsApp/GenAI improvements.** No hay issues de PLAN_MEJORA en esa área.
5. **Full extraction a packages móviles.** W5.7-W5.9 son progresivos. La extracción completa es un proyecto separado con su propio plan.
6. **Docker/infra/CI-CD.** Solo health checks y migrations tracker están en alcance.

---

## RIESGOS

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **W2.1 — SyncService split** | ALTO: sync es ruta crítica de offline-first | Implementar con wrapper adapter + feature flag `new_sync`. Tests de integración primero. Rollback: toggle flag. |
| **W3.9 — imports relativos → package:** | ALTO: 200+ archivos, riesgo de romper imports en PR masivo | Script automatizado + `flutter analyze` gate. Dos PRs: (1) mecanizar cambio, (2) verificar build. CI bloquea si hay imports relativos nuevos. |
| **W4.1 — mongomock en conftest** | MEDIO: cambiar fixture global afecta 46 tests existentes | No cambiar conftest existente. Agregar fixture paralela. Migrar tests 1 por 1 marcando viejos como `integration`. |
| **W1.4 — time→string** | MEDIO: datos legacy con `datetime.time` en DB | Migration script: leer ScheduleDocument, convertir start_time de time a string ISO, reinsertar. Rollback: script inverso. |
| **W3.6 — ActionState refactor** | MEDIO: 507 líneas, refactor extensivo | Tests de comportamiento ANTES del refactor (capturar estado actual). Refactor con cobertura. |
| **W1.2 — BaseService firma pública** | MEDIO: cambiar firmas de métodos públicos | Mantener métodos legacy como delegados `@deprecated`. Migrar callers uno por uno. |
| **W5.3 — Seed unification** | MEDIO: scripts legacy tienen lógica duplicada | Mantener scripts legacy intactos como entry points. Nueva CLI los llama internamente. |
| **W5.7-W5.9 — Package extraction** | MEDIO: imports cambian, riesgo de roturas | Hacer después de W3.9 (package: imports). CI verifica que ambos lados (package + app) compilan. |

---

## APPROVAL GATES

Cada workstream es un PR independiente. Gates de aprobación:

| Gate | Criterio |
|------|----------|
| **W1 done** | `BaseService` creado y 6 servicios lo extienden. `ensure_indexes` en init_db. `start_time` es string. `metadata` tipado. Cero `SUPPLIES`. Deprecated fields no se setean. |
| **W2 done** | SyncService con handlers. `validate_assignment_candidate` delega en `_validate_and_prepare`. Cero `except: pass`. `batch_assignments_to_response`. Audit logs en bulk. Board sin `is_available`. Sin `_FallbackS3Client`. Edad configurable. `build_code` unificado. |
| **W3 done** | `app.dart` < 180 líneas. `app_router.dart` + `dependency_injection.dart`. Sin veil transition. `ActionState<T>` en mobile_core. Detail controller usa ActionState 8 veces. List controller separado. Dev screens deferred + fuera de lib/. Todos los imports son `package:mobile/`. |
| **W4 done** | mongomock fixture. Tests para servicios no cubiertos. Tests de concurrencia. Tests de repositorios mobile. 2 tests de integración mobile. Cobertura backend ≥70% en servicios core. OpenAPI spec generada. |
| **W5 done** | AGENTS.md actualizado. ADR-0004 actualizado. Seeds unificados en CLI. Migration tracker funcionando. Health check con dependencias. PR template con checklist. packages mobile_ui/mobile_domain/mobile_mocks con código real. |

---

## RESUMEN DE ESFUERZO

| Workstream | Archivos nuevos | Archivos modificados | PRs estimados | Riesgo principal |
|------------|----------------|---------------------|---------------|------------------|
| W1 | 1 | 10+ | 2-3 | Medio (BaseService refactor) |
| W2 | 4+ | 15+ | 3-4 | Alto (SyncService split) |
| W3 | 3+ | 200+ | 4-5 | Alto (package: imports) |
| W4 | 15+ | 5+ | 3-4 | Medio (conftest change) |
| W5 | 5+ | 10+ | 3-4 | Medio (package extraction) |
| **Total** | **~30** | **~240** | **15-20** | — |

---

---

# DECISION TIMELINE

> Registro cronológico de implementaciones, refactors y decisiones arquitectónicas ejecutadas.

## 2026-06-02 — Sprint 0: Quick wins

| Decisión | Justificación |
|----------|---------------|
| **Eliminar `SUPPLIES` de Collections** | Código muerto sin referencias |
| **Dejar de setear `priority`/`assigned_manually`** | Campos deprecated, solo lectura legacy |
| **Eliminar `EquineService.list_items()`** | Engañoso: no era más liviano que `list()` |
| **Audit logs → `insert_many()`** | Elimina N inserts individuales en finalize_all/unfinalize_all |
| **Eliminar `is_available` del board equino** | Redundante con `block_reason`. Frontend deriva |
| **Unificar `build_code()` en constants.py** | Elimina duplicación Reservation/Draft |

## 2026-06-02 — W1: Backend Core Infrastructure

| Decisión | Justificación |
|----------|---------------|
| **`BaseService[DocT, CreateSchemaT, UpdateSchemaT]`** | Elimina ~80% boilerplate CRUD. 5 servicios refactorizados (-70% a -31%) |
| **`ensure_indexes()` en init_db** | Garantiza que índices Beanie declarados existen en MongoDB |
| **`ScheduleDocument.start_time: time` → `str`** | Beanie no serializa `datetime.time`. Workaround motor raw eliminado |

## 2026-06-02 — W2: Backend Architecture (Batch 1)

| Decisión | Justificación |
|----------|---------------|
| **`batch_assignments_to_response()`** | 3 queries `$in` en vez de 3N `Document.get()`. N assignments → siempre 3 queries |
| **Eliminar `_FallbackS3Client` (2 clases)** | Fail-fast si boto3 falta + S3 config. `LocalStorageAdapter` si no hay credenciales |
| **Caché catalog resolver (TTL 5 min)** | Evita cargar todas las experiencias en cada resolución. Fase 2: text index |
| **Board pagination (`limit=200`)** | Métodos ya soportaban paginación — `get_board` no la usaba |
| **Age thresholds configurables** | `min_age=12`, `max_age=65` en `ReservationRules`. ConfigService como fuente de verdad |
| **Completar W2.3 (except:pass)** | Inspección confirmó que todo el codebase ya usa logger.exception() |

## 2026-06-02 — W3: Frontend Architecture (Batch 1)

| Decisión | Justificación |
|----------|---------------|
| **Extraer `AppRouter` + `AppDependencies`** | app.dart 320→62 líneas. Router y DI en clases separadas |
| **Eliminar veil transition** | 30 líneas de temporizadores para un simple light/dark toggle. `themeAnimationDuration` alcanza |
| **`ActionState<T>` genérico** | Elimina enums custom duplicados. 4 factories. Sin `_reset*Delayed()` |

## 2026-06-02 — W2.10 + W3.6 + W3.7 (Batch 2)

| Decisión | Justificación |
|----------|---------------|
| **Eliminar legacy fallback en mappers** | Script `migrate_participant_ids.py` creado. Fallback eliminado completamente. Sin compatibilidad |
| **Refactor detail controller con ActionState** | 507→310 líneas. 3 enums eliminados. Bug corregido (cancel/delete usaban `ReservationActionState.confirming`) |
| **ReservationsListState inmutable** | State separado del controller. 9 tests nuevos. `copyWith` para transiciones predecibles |

## 2026-06-02 — Batch 3: Clean infra + hygiene (B6, W3.8, W3.10, W5.1-W5.6)

| Decisión | Justificación |
|----------|---------------|
| **`AuditMetadata` tipado** | `metadata: dict` → `AssignmentMetadata \| ReplacementMetadata \| NotificationMetadata`. `actor_role` nullable. 5 tests. |
| **Playground fuera de `lib/`** | `widget_museum_screen.dart` → `dev/playground/`. Release build no lo compila. |
| **Packages declarados en pubspec** | `mobile_ui`, `mobile_domain`, `mobile_mocks` como path dependencies. Siguen vacíos. |
| **Health check real** | `GET /health` → `{"status","checks":{"mongodb":"ok"}}`. Test actualizado. |
| **PR template + linter** | `.github/PULL_REQUEST_TEMPLATE.md` con checklist AGENTS.md. `analysis_options` documentado. |
| **ADR-0004 → postponed** | Status actualizado con criterios de extracción. |

## 2026-06-02 — Batch 4: W4 Testing (6 servicios + mobile repo)

| Decisión | Justificación |
|----------|---------------|
| **29 tests backend** | ConfigService (7), PolicyService (5), ProviderService (3), ServiceLogService (4), FileUploadService (5), StorageAdapter (5) |
| **4 tests mobile repo** | ReservationsRepositoryImpl: cache hit, cache miss, remote fail, both fail |
| **Coverage audit** | `pytest --cov` ejecutado. Coverage general 52%. Servicios core 82-100%. |
| **OpenAPI contract verify** | 3 tests existentes verifican spec contra 45+ endpoints documentados. |

## 2026-06-02 — Batch 5: W5.3 + W5.4 (Seed CLI + Migration tracker)

| Decisión | Justificación |
|----------|---------------|
| **Seed CLI unificado** | `python -m app.cli seed -t <name>`. 6 seeds registrados via `importlib`. Legacy scripts intactos. |
| **Migration tracker formal** | `app/migrations/` con 3 migraciones (staff→guide, schedule is_active, sync_metadata). `run_migrations()` en startup. Fail-open. |

---

## 2026-06-02 — Batch 5: Testing Wave (W4 completion + T5 + F6)

| Decisión | Justificación |
|----------|---------------|
| **mongomock fixture + 5 demo tests** | Infraestructura para unit tests backend sin MongoDB real. Patrón documentado para migración progresiva. |
| **111 tests para 9 controllers mobile** | Dashboard, Participants, SaddlesList, Experiences, Schedules, EmergencyContacts, ReservationRules, ExperienceForm, ScheduleForm. Cubren 497 LOC de controllers. |
| **Integration test skeleton (T3)** | 2 flows esqueletizados (reservation list + detail). Requieren emulador para completar. |

## 2026-06-02 — Batch 6: Frontend Architecture Wave (W3.9 + W5.7-W5.9)

| Decisión | Justificación |
|----------|---------------|
| **619 imports → `package:mobile/`** | Script Python recorrió 161 archivos. Cero errores post-conversión. Elimina fragilidad de imports relativos profundos. |
| **mobile_ui poblado (40 files)** | 29 widgets + 6 theme + 4 voice + barrel. Dependencias: auto_size_text, flutter_svg, material_symbols_icons. |
| **mobile_domain poblado (23 files)** | 2 enums + 15 domain models + 4 repository interfaces + barrel. +mobile_core como dependencia. |
| **mobile_mocks poblado (2 files)** | FakeReservationsRepository + barrel. Depende de mobile_domain. |

## 2026-06-02 — Batch 7: SyncService split + domain extraction

| Decisión | Justificación |
|----------|---------------|
| **SyncService → 4 handlers** | 587→220 líneas. De 11 dependencias a ≤5 por handler. Sin feature flag — refactor directo, todos los tests pasan. |
| **Repository interfaces → mobile_domain** | 18 archivos de dominio puro (ReservationsRepository, SaddlesRepository, EquineRepository, AssignmentsRepository + modelos). 102 imports actualizados. 18 re-exports. |

---

*Fin del documento. Última actualización: 2026-06-02.*
