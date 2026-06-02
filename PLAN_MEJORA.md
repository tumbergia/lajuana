# Technical Debt — Inventario Completo

> Issues identificadas durante auditoría cruzada (Junio 2026). Incluye las 4 issues originales (P1-P4) más hallazgos complementarios de arquitectura, frontend, testing y operaciones.

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

**Dónde:** `apps/api/app/services/mappers.py:96-106`

**Problema:** Cada vez que se resuelve un `AssignmentResponseSchema`, se hacen 3 queries individuales (`ParticipantDocument.get`, `EquineDocument.get`, `SaddleDocument.get`) para resolver nombres. Si un endpoint devuelve N assignments, son 3N queries.

**Impacto:** Bajo hoy (solo 1 assignment por response). Crece si hay endpoints batch que devuelvan listas de assignments.

**Solución posible:**
- Aceptar parámetros opcionales `participant_name`, `equine_name`, `saddle_label` en `assignment_to_response` para que el caller pueda resolverlos en batch.
- O denormalizar nombres directamente en `AssignmentDocument` (estilo MongoDB embed).

**Prioridad:** Low

---

## P2. `finalize_all` / `unfinalize_all` — audit logs no están en bulk

**Dónde:** `apps/api/app/services/assignment_service.py:249-258` y `302-311`

**Problema:** Los updates de estado se envían con `bulk_write`, pero los audit logs siguen siendo inserts individuales en un loop. Con N=20 assignments: 20 inserts secuenciales.

**Impacto:** Bajo. Los inserts individuales son baratos. Mejora marginal.

**Solución posible:** Usar `insert_many` con una lista de `ReservationAuditLogDocument`.

**Prioridad:** Low

---

## P3. Equinos envían `is_available` redundante en el board

**Dónde:** `apps/api/app/schemas/assignment.py:87-94` y `apps/api/app/services/assignment_service.py:594`

**Problema:** `AssignmentBoardEquineSchema` incluye `is_available: bool` además de `block_reason: str | None`. La disponibilidad se puede derivar de `block_reason == null`. Es el mismo problema que se arregló para sillas (Fase 5.2) pero para equinos quedó pendiente.

**Impacto:** Bajo. Carga 1 campo extra innecesario en la respuesta del board.

**Solución:** Eliminar `is_available` de `AssignmentBoardEquineSchema` y derivarlo de `block_reason` en el frontend.

**Prioridad:** Medium

---

## P4. Índice único en `SaddleDocument.code`

**Dónde:** `apps/api/app/documents/saddle_document.py:8`

**Problema:** El campo `code` está declarado como `Indexed(str, unique=True)`, pero la validación de unicidad se hace en `SaddleService.create/update` a nivel aplicación. Si el índice único de MongoDB no existe (por migración incompleta o datos previos duplicados), podrían crearse sillas con el mismo código.

**Impacto:** Medio — violación de integridad de datos.

**Solución:** Verificar que el índice único existe en la colección `saddles`. Si no, crearlo con `ensure_index`. Mantener validación a nivel aplicación como defensa adicional.

**Prioridad:** Medium

---

# HALLAZGOS COMPLEMENTARIOS

---

## A. ARQUITECTURA

---

### A1. Mobile packages declarados pero vacíos

**Dónde:** `packages/mobile_ui/`, `packages/mobile_domain/`, `packages/mobile_mocks/`

**Problema:** AGENTS.md define estos paquetes como parte de la arquitectura, pero contienen solo `.gitkeep`. El código real de UI, dominio y mocks está inline en `apps/mobile/lib/features/`. La separación prometida no existe.

**Impacto:** Alto — la arquitectura documentada no refleja la realidad. Dificulta el reuse, el testing aislado y la evolución independiente de capas.

**Solución:** Poblarlos progresivamente extrayendo código desde `apps/mobile`. O actualizar AGENTS.md/docs para reflejar la arquitectura real (monolito modular en `apps/mobile`).

**Prioridad:** High

---

### A2. Modelos de dominio duplicados entre mobile y backend

**Dónde:** `apps/mobile/lib/features/*/domain/models/*.dart` vs `apps/api/app/schemas/*.py` y `apps/api/app/documents/*.py`

**Problema:** No existe generación de código ni compartido de tipos. Los modelos Dart duplican los schemas Python manualmente. `ReservationStatus`, `AssignmentStatus`, `ParticipantFormStatus` existen en ambos lados sin contrato formal. Cualquier cambio en backend requiere actualización manual en frontend.

**Impacto:** Alto — riesgo de drift. Errores silenciosos si un enum cambia en backend pero no en frontend.

**Solución:** Evaluar OpenAPI generator para Dart, o al menos documentar como ADR y agregar tests de contrato que verifiquen matching.

**Prioridad:** High

---

### A3. Servicios con too-many-dependencies (constructores masivos)

**Dónde:** `apps/api/app/services/sync_service.py:286-299` (10 dependencias), `SyncOperationExecutor:72-94` (10 dependencias)

**Problema:** `SyncService` y `SyncOperationExecutor` reciben ~10 servicios cada uno en el constructor. Esto es señal de que `SyncService` viola SRP — orquesta demasiados dominios.

**Impacto:** Medio — difícil de testear, acoplamiento alto, viola Law of Demeter.

**Solución:** Dividir `SyncService` por dominio (ej: `ExperienceSyncHandler`, `ReservationSyncHandler`) o usar un patrón visitor. Cada handler con 1-2 dependencias.

**Prioridad:** Medium

---

### A4. Servicios CRUD boilerplate repetitivo

**Dónde:** `apps/api/app/services/provider_service.py`, `policy_service.py`, `service_log_service.py`, `saddle_service.py`, `equine_service.py`

**Problema:** Patrón casi idéntico en cada servicio: `get(id) → raise 404 si no existe`, `create(payload) → doc.insert()`, `update(id, payload) → get + setattr + save`. Esto es ~80% código repetido.

**Impacto:** Medio — mantenimiento costoso, bugs por copiar/pegar, cambios cross-cutting (ej: agregar audit log a todas las operaciones) requiere tocar N archivos.

**Solución:** Crear un `BaseService[DocumentType]` con create/update/get/soft_delete genéricos, y que los servicios específicos solo agreguen validación de dominio.

**Prioridad:** Medium

---

### A5. `except Exception: pass` generalizado

**Dónde:**
- `apps/api/app/services/assignment_service.py:267-268`, `320-321`, `453-454`
- `apps/api/app/services/reservation_service.py` (múltiples ocasiones)
- `apps/api/app/services/notification_service.py`
- `apps/api/app/services/sync_service.py`
- `apps/api/app/services/storage.py:72`

**Problema:** Swallowing de excepciones sin logging ni manejo. Oculta errores reales en producción. Varios casos documentados como "best-effort" o "non-critical" pero sin metricas ni alertas.

**Impacto:** Alto — bugs silenciosos en producción. Dificulta debugging de fallos intermitentes en notificaciones, auditoría, etc.

**Solución:** Mínimo: `logger.exception(...)` dentro del except. Ideal: definir política de "fail-open" vs "fail-fast" con trazabilidad explícita.

**Prioridad:** High

---

### A6. `validate_assignment_candidate` duplica lógica de `_validate_and_prepare`

**Dónde:** `apps/api/app/services/assignment_service.py:697-788`

**Problema:** `validate_assignment_candidate` (línea 763) repite el pipeline de validación de `_validate_and_prepare` (línea 697) en lugar de llamarlo con un flag dry-run. Casi 90 líneas de código duplicado.

**Impacto:** Medio — bug si una validación se actualiza en un método pero no en el otro.

**Solución:** Hacer que `validate_assignment_candidate` llame a `_validate_and_prepare` con un flag `dry_run=True` y descarte el resultado.

**Prioridad:** Medium

---

### A7. `EquineService.list_items()` es idéntico a `list()`

**Dónde:** `apps/api/app/services/equine_service.py:68-85`

**Problema:** El método `list_items()` dice "Retorna solo los campos del list item (usa el mismo query pero más liviano)" pero en realidad llama a `self.list(...)` con los mismos parámetros y sin proyección. No es más liviano.

**Impacto:** Bajo — ruido solamente, pero es engañoso.

**Solución:** Eliminar `list_items()` o implementar proyección real de campos.

**Prioridad:** Low

---

### A8. `_FallbackS3Client` — cliente falso sin隔离

**Dónde:** `apps/api/app/services/storage.py:96-115`

**Problema:** Cuando boto3 no está instalado, se usa un `_FallbackS3Client` que hace no-ops y retorna URLs falsas. Esto puede generar Side Effects silenciosos: operaciones de escritura que "funcionan" pero no persisten nada. Además, el `generate_presigned_url` retorna una URL que no funciona.

**Impacto:** Medio — en entornos sin boto3, las operaciones de storage fallan silenciosamente.

**Solución:** Usar `LocalStorageAdapter` como fallback en lugar de un cliente falso. O lanzar error en init si boto3 no está disponible y el entorno requiere S3.

**Prioridad:** Medium

---

### A9. Nombres de depósitos/colecciones inconsistentes entre `collections.py` y su uso

**Dónde:** `apps/api/app/common/collections.py` — `SUPPLIES` declarado pero sin documento asociado. `app_config` usado como nombre de colección pero `AppConfigDocument.Settings.name` usa `Collections.APP_CONFIG`.

**Problema:** La colección `SUPPLIES = "supplies"` está definida pero no existe ningún documento Beanie que la use. Es código muerto.

**Impacto:** Bajo.

**Solución:** Eliminar `SUPPLIES` de `Collections`.

**Prioridad:** Low

---

### A10. `AssignmentDocument.priority` y `assigned_manually` deprecated pero activos

**Dónde:** `apps/api/app/documents/assignment_document.py:34-35`

**Problema:** Documentados como "Deprecated (mantener para backward compat con docs existentes)" pero el código sigue seteando `priority="standard"` y `assigned_manually=True` en `_validate_and_prepare` (línea 758-759). Si ya no se usan, no deberían setearse.

**Impacto:** Bajo — campos extra en DB, confusión semántica.

**Solución:** Dejar de setearlos en el código nuevo; mantener en el documento solo para lectura de datos legacy.

**Prioridad:** Low

---

## B. BACKEND: RENDIMIENTO Y DATOS

---

### B1. `experience_catalog_resolver.resolve()` carga TODAS las experiencias activas en memoria

**Dónde:** `apps/api/app/services/experience_catalog_resolver.py:78-81`

**Problema:** Si no se pasan `experiences`, resuelve cargando toda la colección `{"is_active": True}` a memoria. Luego itera linealmente para matching token-overlap. Sin paginación ni límite.

**Impacto:** Medio — con ~100+ experiencias es aceptable, pero no escala. Podría afectar el bucket de memoria en Lambda si hay muchas.

**Solución:** Usar text index de MongoDB para token overlap, o imponer un límite en la API.

**Prioridad:** Medium

---

### B2. `reservation_to_response` hace N+1 queries de participantes

**Dónde:** `apps/api/app/services/mappers.py:126-162`

**Problema:** Participantes se cargan con un `$in` query (batch), pero el mapeo individual podría beneficiarse de eager loading de PaymentProofs. Además, el fallback por `reservation_id` (legacy) es otro query.

**Impacto:** Bajo hoy (batch query, no N+1). Pero el fallback legacy añade complejidad.

**Solución:** Eliminar fallback legacy cuando se migren datos antiguos.

**Prioridad:** Low

---

### B3. `equine_service.list_available_for_reservation()` carga todos los equinos

**Dónde:** `apps/api/app/services/equine_service.py:201`

**Problema:** A pesar de aceptar `limit`/`skip`, el método se usa desde `get_board` sin paginación, cargando todos los equinos (línea 201: `EquineDocument.find({})`). Lo mismo en `saddle_service.list_available_for_reservation()`.

**Impacto:** Bajo (pocos equinos), pero con crecimiento es N+1 inverso.

**Solución:** Asegurar paginación desde el board o cachear catálogo de equinos.

**Prioridad:** Low

---

### B4. `datetime.time` no serializable por Beanie — workaround motor raw

**Dónde:** `apps/api/app/documents/schedule_document.py:14` y `apps/api/app/services/reservation_service.py:96-114`

**Problema:** Beanie no puede insertar/actualizar documentos con campos `time` directamente. Requiere usar `motor collection.update_one()` con string ISO (`"08:00:00"`) en lugar de `doc.save()`. Esto fuerza a que `_save_schedule_status` use motor raw, rompiendo la abstracción de Beanie.

**Impacto:** Medio — código más frágil, workaround que puede romperse con upgrades de Beanie. Ya documentado en AGENTS.md.

**Solución:** Cambiar `start_time` a string (`"HH:MM:SS"`) en `ScheduleDocument` y convertir en los edges (API/input). O migrar a `datetime` combinado.

**Prioridad:** Medium

---

### B5. Falta de `ensure_index` en init_db para índices declarados en Beanie

**Dónde:** `apps/api/app/core/db.py:46-101`

**Problema:** `init_beanie` no garantiza que los índices declarados en los `Settings.indexes` existan realmente en MongoDB. Solo se crean si el documento se inicializa con `Document`.

**Solución:** Llamar a `Document.settings.ensure_indexes()` después de init_beanie, o verificar con `list_indexes`.

**Prioridad:** Medium

---

### B6. `ReservationAuditLogDocument.metadata` sin schema de validación

**Dónde:** `apps/api/app/documents/reservation_audit_log_document.py:18`

**Problema:** `metadata: dict = {}` acepta cualquier estructura. No hay contrato sobre qué metadatos guarda cada acción de auditoría. Dificulta queries y reportes.

**Impacto:** Medio — datos no estructurados en colección de auditoría.

**Solución:** Usar `pydantic.BaseModel` tipado para metadatos, o al menos documentar el schema esperado por acción.

**Prioridad:** Medium

---

### B7. Edad mínima/máxima hardcodeada en validación de participantes (12 y 65)

**Dónde:** `apps/api/app/services/assignment_service.py:630-633`

**Problema:** Los thresholds de edad (12 y 65 años) están hardcodeados en el servicio de asignación. No son configurables y no hay regla de negocio documentada.

**Impacto:** Bajo — difícil de modificar si el negocio cambia.

**Solución:** Mover a configuración del sistema (AppConfigDocument) o constantes con nombre.

**Prioridad:** Low

---

### B8. `_build_code` duplicado en `reservation_service.py` y `reservation_draft_service.py`

**Dónde:** `apps/api/app/services/reservation_service.py:870-871` y `reservation_draft_service.py:142-143`

**Problema:** Lógica de generación de código duplicada (cambia solo prefijo: `RES` vs `PR-`).

**Impacto:** Bajo — pero es un micro-derivado de A4 (CRUD boilerplate).

**Solución:** Unificar en un helper compartido o en `ReservationDocument` como classmethod.

**Prioridad:** Low

---

## F. FRONTEND FLUTTER

---

### F1. `app.dart` — controlador monolítico de 320 líneas

**Dónde:** `apps/mobile/lib/app/app.dart`

**Problema:** `_LaJuanaAppState` maneja: init de dependencias, route builder (switch de 15 rutas), tema, transiciones, dev screens, todo junto. SRP violado.

**Impacto:** Medio — difícil de leer, testear y modificar.

**Solución:** Extraer route builder a `app_router.dart`. Extraer init de dependencias a `dependency_injection.dart` o similar.

**Prioridad:** Medium

---

### F2. `ReservationDetailController` — 507 líneas con ~8 action states duplicados

**Dónde:** `apps/mobile/lib/features/reservations/presentation/controllers/reservation_detail_controller.dart`

**Problema:** Cada acción (approve, reject, unverify, unreject, confirm, cancel, delete, restore) tiene su propio enum de estado ± errorCode ± errorMessage ± resetDelayed. El patrón es casi idéntico 8 veces. Código copiado/pegado.

**Impacto:** Medio — un bug en el patrón se replica 8 veces. Difícil de mantener.

**Solución:** Crear un helper genérico `ActionState<T>` que maneje idle/loading/success/error + reset, y reusarlo.

**Prioridad:** Medium

---

### F3. Dev screens compilados en debug via imports directos

**Dónde:** `apps/mobile/lib/app/app.dart:33` — import de `widget_museum_screen.dart`
**Dónde:** `apps/mobile/lib/app/app.dart:31` — import de `dev_loader_screen.dart`

**Problema:** Aunque hay un `kReleaseMode` guard, los imports son directos (no deferred). El código de playground viaja en el bundle debug.

**Impacto:** Bajo en release (tree-shaking lo elimina), pero en debug aumenta tamaño y expone funcionalidad interna.

**Solución:** Usar `import` diferido (`deferred as`) para dev/playground screens.

**Prioridad:** Low

---

### F4. Tema con transición "veil" innecesariamente compleja

**Dónde:** `apps/mobile/lib/app/app.dart:48-54, 183-210`

**Problema:** El toggle de tema usa un sistema de "veil" con 3 constantes de duración, opacidad variable, color variable, y temporizadores. Para un simple light/dark switch.

**Impacto:** Bajo — pero complejidad innecesaria. Posibles bugs con `mounted` checks.

**Solución:** Usar `ThemeMode` directamente con `AnimatedTheme` o `animationDuration` del `MaterialApp`.

**Prioridad:** Low

---

### F5. Controllers con doble-responsabilidad: filter + fetch + cache + notify

**Dónde:** `apps/mobile/lib/features/reservations/presentation/controllers/reservations_list_controller.dart`

**Problema:** `ReservationsListController` mezcla estado de UI (loadState), datos (items, _allItems), filtros (filterGroup, searchQuery), fetch (loadInitial, refresh, _fetchFromRemote) y caché. 158 líneas que hacen de todo.

**Impacto:** Medio — difícil de testear (depende de repository real o mocking manual).

**Solución:** Separar en `ReservationsListState` (datos + filtros) y `ReservationsListBloc` (fetch + cache).

**Prioridad:** Medium

---

### F6. Falta de cobertura de tests en la mayoría de features

**Dónde:** `apps/mobile/test/`

**Problema:** Solo 12 archivos de test para 8 features. Features enteras sin test: `dashboard`, `configuration`, `catalogs`, `participants`, `providers`, `saddles` no tienen tests. De las que tienen, la cobertura es parcial.

**Impacto:** Alto — regresiones no detectadas en UI, controllers y mappers.

**Solución:** Priorizar tests de controllers y repositorios para features core (reservations, assignments, auth).

**Prioridad:** High

---

### F7. `playground/` linked to production app module

**Dónde:** `apps/mobile/lib/playground/widget_museum_screen.dart`

**Problema:** El directorio `playground` está dentro de `lib/` (no en un directorio separado). Aunque el código está protegido por `kReleaseMode`, su presencia en `lib/` sugiere que es código de producción.

**Solución:** Mover playground a un directorio fuera de `lib/` (ej: `dev/playground/`) o usar un entry point separado.

**Prioridad:** Low

---

### F8. Import paths relativos profundos

**Dónde:** Múltiples archivos en `apps/mobile/lib/features/*/presentation/**/*.dart`

**Problema:** Los imports usan rutas relativas estilo `../../domain/repositories/...` que son frágiles ante reestructuración de directorios.

**Impacto:** Bajo — pero dificulta refactors. Síntoma de que el modular extraction (A1) no ocurrió.

**Solución:** Usar `package:` imports desde el `name` en pubspec.yaml.

**Prioridad:** Low

---

## T. TESTING Y CALIDAD

---

### T1. Backend: servicios sin tests dedicados

**Dónde:** `apps/api/tests/`

**Problema:** No hay tests para: `ConfigService`, `PolicyService`, `ProviderService`, `ServiceLogService`, `FileUploadService`, `UserService`, `OpsService`, `StorageAdapter`, `NotificationService` (solo parcial).

**Impacto:** Alto — cambios en estos servicios no tienen red de seguridad.

**Solución:** Agregar tests unitarios para cada service (al menos happy path + error path).

**Prioridad:** High

---

### T2. Backend: tests existentes con coverage limitado

**Dónde:** `apps/api/tests/`

**Problema:** De 49 archivos de test, varios son smoke tests que prueban solo un caso feliz. Ej: `test_config_service.py` no existe, `test_provider_service.py` no existe.

**Impacto:** Medio — falsa sensación de seguridad por cantidad de test files.

**Solución:** Auditar coverage real por módulo.

**Prioridad:** Medium

---

### T3. Mobile: sin tests de integración

**Dónde:** `apps/mobile/test/`

**Problema:** Todos los tests son unitarios. No hay tests de integración (golden, widget, integration driver) que verifiquen flujos completos (login → listar reservas → ver detalle).

**Impacto:** Alto — UI/UX regressions pasan desapercibidas.

**Solución:** Agregar al menos 2-3 tests de integración para flujos core.

**Prioridad:** High

---

### T4. Sin contratos entre API y frontend

**Dónde:** `apps/api/tests/test_endpoint_docs_contract.py` y `test_endpoint_schema_coverage.py`

**Problema:** Existen tests de "contrato" que verifican que los endpoints devuelvan schemas, pero no verifican que el frontend pueda consumirlos. No hay snapshot testing ni OpenAPI spec formal.

**Impacto:** Medio — cambios en respuesta API pueden romper frontend sin ser detectados en CI.

**Solución:** Generar OpenAPI spec (FastAPI ya lo soporta) y usar snapshot testing en frontend.

**Prioridad:** Medium

---

### T5. `test_assignment_service.py` tests end-to-end con base de datos real

**Dónde:** `apps/api/tests/test_assignment_service.py`

**Problema:** Los tests de servicios usan base de datos real (MongoDB via Beanie init), no mocking. Lentos, frágiles, requieren infraestructura.

**Impacto:** Medio — tests lentos, difíciles de ejecutar en CI sin MongoDB.

**Solución:** Usar mongomock o in-memory para tests unitarios de servicios. Reservar DB real solo para integración.

**Prioridad:** Medium

---

### T6. Faltan tests de concurrencia para reservas

**Dónde:** `apps/api/tests/test_concurrency_reservation.py` — revisar cobertura

**Problema:** El archivo existe pero probablemente solo cubre un escenario. Race conditions en `_commit_schedule_capacity` y `ensure_date_available` no están probadas con múltiples clientes simultáneos.

**Impacto:** Alto — bugs de concurrencia en producción son difíciles de diagnosticar.

**Solución:** Agregar tests de concurrencia con `asyncio.gather` simulando N requests simultáneas.

**Prioridad:** High

---

### T7. Mobile: `ReservationsRepository` y sus implementaciones no tienen tests

**Dónde:** `apps/mobile/lib/features/reservations/infrastructure/repositories/`

**Problema:** El repositorio que orquesta remote+local no tiene tests. Es el punto crítico del offline-first.

**Impacto:** Alto — errores de sincronización no detectados.

**Solución:** Tests unitarios con `respositories` mockeando remote y local.

**Prioridad:** High

---

## D. DOCUMENTACIÓN Y OPERACIONES

---

### D1. Seed scripts duplicados con lógica diferente

**Dónde:** `apps/api/scripts/seed_reproducible.py` (934 líneas), `seed_experiences_and_schedules_qa.py`, `seed_schedules_2026_q2.py`, `seed_equines_rf14.py`, `seed_form_test.py`, `seed_proof_file_data.py`

**Problema:** 6 scripts de seed sin estandarización. `seed_reproducible.py` es enorme (934 líneas) y contiene lógica de negocio duplicada (creación de experiencias, equinos, etc.). Los otros son ad-hoc para QA.

**Impacto:** Medio — inconsistencia entre seeds, difícil mantener.

**Solución:** Centralizar seeds en un comando CLI con factories, y mantener solo 1 script de seed principal + patches para QA específicos.

**Prioridad:** Medium

---

### D2. Solo 1 migration real en `migrations/`

**Dónde:** `apps/api/app/migrations/seed_notification_templates.py`

**Problema:** No hay un sistema de migraciones. La migración staff→guide se hace inline en `init_db`. No hay tracking de migraciones ejecutadas.

**Impacto:** Medio — despliegues en ambientes nuevos requieren ejecutar seeds manualmente.

**Solución:** Usar `alembic` para migraciones de datos (no schema) o un simple `migrations_tracker` en MongoDB.

**Prioridad:** Medium

---

### D3. Sin healthcheck de dependencias externas

**Dónde:** `apps/api/app/api/endpoints/health.py`

**Problema:** El endpoint de health probablemente solo verifica que la app responde, no que MongoDB, S3, WhatsApp API, etc. estén operativos.

**Impacto:** Medio — health check da positivo aunque dependencias críticas estén caídas.

**Solución:** Agregar verificaciones de conectividad a MongoDB, S3, y proveedores de notificaciones.

**Prioridad:** Medium

---

### D4. `docs/` no sincronizado con código real

**Dónde:** `docs/architecture/`, `docs/decisions/`

**Problema:** Los ADRs existen pero no hay mecanismo para verificar cumplimiento. Ej: ADR-0004 propone `mobile_ui` package, pero está vacío (A1).

**Impacto:** Medio — documentación engañosa.

**Solución:** Agregar `docs-adr-validation` en CI que verifique que los ADRs se correspondan con el código, o archive ADRs obsoletos.

**Prioridad:** Medium

---

### D5. AGENTS.md reglas no verificables automáticamente

**Dónde:** `AGENTS.md`

**Problema:** Reglas como "No mezclar componentes reutilizables con lógica de negocio" y "No crear archivos/carpetas sin justificación" son subjetivas y no tienen linter/CI.

**Impacto:** Bajo — dependen del criterio del desarrollador.

**Solución:** Implementar lint rules personalizados o review checklist.

**Prioridad:** Low

---

## M. MOBILE PACKAGES FANTASMA

---

### M1. `mobile_ui` — paquete UI reutilizable vacío

**Dónde:** `packages/mobile_ui/`

**Contenido:** `.gitkeep`, `pubspec.yaml`, `README.md`

**Problema:** Todos los widgets reutilizables están en `apps/mobile/lib/app/widgets/` o dentro de features. No hay nada extraíble aún.

**Impacto:** Ver A1.

---

### M2. `mobile_domain` — contratos y modelos de dominio vacío

**Dónde:** `packages/mobile_domain/`

**Contenido:** `.gitkeep`, `pubspec.yaml`, `README.md`

**Problema:** Los modelos de dominio están en `apps/mobile/lib/features/*/domain/models/`. No hay extracción.

**Impacto:** Ver A1.

---

### M3. `mobile_mocks` — fixtures y fakes vacío

**Dónde:** `packages/mobile_mocks/`

**Contenido:** `.gitkeep`, `pubspec.yaml`, `README.md`

**Problema:** Los mocks están inline en los tests. No hay reutilización cross-feature.

**Impacto:** Ver A1.

---

## MATRIZ DE PRIORIDADES

| Prioridad | IDs | Acción recomendada |
|-----------|-----|-------------------|
| **High** | A1, A2, A5, F6, T1, T3, T6, T7 | Abordar en próximo sprint |
| **Medium** | P3, P4, A3, A4, A6, A8, B1, B4, B5, B6, F1, F2, F5, T2, T4, T5, D1, D2, D3, D4 | Planificar en siguientes 2-3 sprints |
| **Low** | P1, P2, A7, A9, A10, B2, B3, B7, B8, F3, F4, F7, F8, D5 | Backlog — documentar y priorizar según necesidad |

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

*Fin del plan integral. Última actualización: Junio 2026.*
