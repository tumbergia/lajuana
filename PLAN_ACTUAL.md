# PLAN_ACTUAL — Progreso de Implementación

> Fecha: 2026-06-02 · Rama: `develop`
> Última auditoría: 457 tests, 0 fallas

---

## MAPA DE AVANCE

| Workstream | Items | Estado | Prioridad |
|-----------|-------|--------|-----------|
| **Sprint 0** | W1.6, W1.7, W2.8, W2.5, W2.6, W2.13 | ✅ **Completado** | Bajo |
| **W1 Backend Core** | W1.1, W1.2, W1.3, W1.4 | ✅ **Completado** | Medio |
| **W2 Backend Architecture** | W2.2 | ✅ **Completado** | Medio |
| **W2 Backend Architecture** | W2.3 (parcial: assignment_service) | 🟡 **Parcial** | Alto |
| **W2 Backend Architecture** | W2.1, W2.4, W2.7, W2.9, W2.10, W2.11, W2.12 | ❌ Pendiente | — |
| **W3 Frontend** | W3.1-W3.10 | ❌ Pendiente | — |
| **W4 Testing** | W4.1-W4.7 | ❌ Pendiente | — |
| **W5 Docs/Operations** | W5.1-W5.9 | ❌ Pendiente | — |

---

## SPRINT 0 — Bajo Riesgo ✅

| Item | Issue | Cambio | Archivos |
|------|-------|--------|----------|
| W1.6 | A9 | Eliminado `SUPPLIES = "supplies"` muerto | `collections.py` |
| W1.7 | A10 | Dejado de setear `priority`/`assigned_manually` (campos legacy) | `assignment_service.py` |
| W2.8 | A7 | Eliminado `list_items()` engañoso (no era más liviano) | `equine_service.py`, `equines.py` |
| W2.5 | P2 | Audit logs: `for doc: insert()` → `insert_many()` en `finalize_all`/`unfinalize_all` | `assignment_service.py` |
| W2.6 | P3 | Eliminado `is_available` redundante del schema equino en board. Frontend ya deriva de `block_reason`. | `assignment.py` schema, `assignment_service.py` |
| W2.13 | B8 | Unificado `build_code()` en `constants.py`. Reservation y Draft usan la misma función. | `constants.py`, `reservation_service.py`, `reservation_draft_service.py` |

**Tests pre-existentes arreglados** (4 fallas → 0):
- `business_errors.py`: Agregados `equines_timeline`, `equines_available_for_reservation`, `assignments_replace` a la matriz
- `test_endpoint_docs_contract.py`: Corregido `operation_id` de `deactivateEquineById` → `deleteEquine`
- `equines.py`: Alineado summary/description del endpoint DELETE con doc centralizado

---

## W1 — BACKEND CORE INFRASTRUCTURE ✅

### W1.1 — BaseService genérico

**Archivo nuevo:** `apps/api/app/services/base_service.py`

```python
BaseService[DocT, CreateSchemaT, UpdateSchemaT]
 ├── get(id) → doc | ApiError 404
 ├── create(payload) → doc
 ├── update(id, payload) → doc
 ├── soft_delete(id) → doc (marca deleted_at)
 ├── restore(id) → doc (limpia deleted_at)
 ├── list(include_deleted, limit, skip) → list[doc]
 └── count(include_deleted) → int
```

**Configuración por subclase:**
- `document_class` → clase del documento Beanie
- `not_found_code` → ErrorCode para 404
- `not_found_message` → mensaje de error

**Tests:** 11 unit tests con mocking (`test_base_service.py`)
**Riesgo:** ⚠️ Monkeypatching debe ir a la clase del documento directamente (ej: `EquineDocument.get`), no al módulo del servicio.

### W1.2 — Refactor servicios → BaseService

| Servicio | Antes | Después | Reducción | Observaciones |
|----------|-------|---------|-----------|---------------|
| **ProviderService** | 33 líneas | 10 | **~70%** | `delete()` preservado (usa `is_active`, no `deleted_at`) |
| **PolicyService** | 62 líneas | 55 | ~11% | `create()`/`update()` preservados (validación dominio) |
| **ServiceLogService** | 58 líneas | 51 | ~12% | `create()`/`update()` preservados (validación event_type) |
| **SaddleService** | 115 líneas | 58 | **~50%** | `create()`/`update()` preservados (validación código único). `update()` ahora usa `super().update()` |
| **EquineService** | 240 líneas | 165 | **~31%** | `list()`/`count()` con filtros preservados. `soft_delete()` preservado (también desactiva). `restore()` ahora reactiva `is_active` |
| **ConfigService** | — | — | — | No aplica (no es CRUD) |

### W1.3 — ensure_indexes en init_db

**Archivo:** `app/core/db.py`

Después de `init_beanie()`, itera sobre todos los `document_models` y llama a `create_indexes()` para cada uno con sus índices declarados en `Settings.indexes`.

Cubre el caso donde `init_beanie` no garantiza que los índices existan (issue P4/B5).

### W1.4 — start_time: time → str

| Archivo | Cambio |
|---------|--------|
| `schedule_document.py` | `start_time: time` → `start_time: str` + validador `pattern=r"^\d{2}:\d{2}:\d{2}$"` |
| `schedule.py` (schemas) | `ScheduleCreateSchema` y `ScheduleResponseSchema`: `time` → `str` |
| `reservation_service.py` | `_save_schedule_status` simplificado: usa `doc.save()` sin motor raw. Eliminado import `CollectionWasNotInitialized` |
| `seed_reproducible.py` | `time(hour=8, minute=0)` → `"08:00:00"` |

**Riesgo:** ⚠️ Datos legacy en MongoDB con `datetime.time` requieren migración (script manual o batch).

---

## W2 — BACKEND ARCHITECTURE (parcial)

### W2.2 — dry_run en validación de asignaciones

**Antes:** 90 líneas de validación duplicadas en `validate_assignment_candidate` y `_validate_and_prepare`.

**Después:** `_validate_and_prepare` acepta `dry_run: bool = False`. Cuando `True`, retorna `(safety_flags, warnings)` sin construir document kwargs. `validate_assignment_candidate` delega completamente.

### W2.3 — except:pass → logger.exception (parcial)

Completado en `assignment_service.py` (6 ocurrencias). Pendiente en el resto del codebase:
- `reservation_service.py`
- `notification_service.py`
- `sync_service.py`
- `storage.py`

---

## AUDITORÍA — Issues encontrados y resueltos

| Issue | Detectado en | Fix |
|-------|-------------|-----|
| `EquineService.restore()` no reactivaba `is_active` | Auditoría W1.2 | ✅ Override añadido con `doc.is_active = True` |
| `SaddleService.update()` duplicaba loop setattr/save | Auditoría W1.2 | ✅ Refactorizado: valida código, luego `super().update()` |
| `except: pass` silencioso en assignment_service | Auditoría W2.5 | ✅ 6 ocurrencias → `logger.exception()` |
| `validate_assignment_candidate` tests fallaban por falta de mocks de `find_one`/`find` | Implementación W2.2 | ✅ Mocks agregados a `_patch_validate_base` |
| 4 tests de contrato fallaban (endpoints faltantes en matriz) | Sprint 0 | ✅ `business_errors.py` + `test_endpoint_docs_contract.py` + `equines.py` |

---

## TARGET CONTRACT — Estado actual

| Dimensión | Target | Actual |
|-----------|--------|--------|
| **BaseService** | CRUD genérico para todos los servicios | ✅ 5/6 servicios refactorizados (ConfigService no aplica) |
| **Audit logs bulk** | `insert_many()` sin loops | ✅ `finalize_all`/`unfinalize_all` |
| **ScheduleDocument.start_time** | `str` ISO sin motor raw | ✅ Implementado |
| **Índices** | `ensure_indexes()` en init_db | ✅ Implementado |
| **Board response** | equino sin `is_available` | ✅ Eliminado |
| **Excepciones** | Cero `except: pass` | 🟡 Parcial (solo assignment_service) |
| **Mappers batch** | N assignments → 3 queries | ❌ Pendiente |
| **SyncService** | Dividido en handlers | ❌ Pendiente |
| **Resto** | — | ❌ Pendiente |

---

## PRÓXIMOS PASOS RECOMENDADOS

1. **W2.3** — Eliminar `except: pass` en `reservation_service.py`, `notification_service.py`, `sync_service.py`, `storage.py` (alto impacto calidad)
2. **W2.9** — Caché + text index para `experience_catalog_resolver` (escalabilidad)
3. **W3.1-W3.3** — Frontend: app_router, DI, simplificar app.dart
4. **W2.4** — `batch_assignments_to_response` (N+1 mappers)
