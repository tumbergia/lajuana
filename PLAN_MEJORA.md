# PLAN DE MEJORA — La Juana

> Auditoría arquitectónica, performance y calidad. Junio 2026.
> Generado a partir de auditoría cruzada (Sócrates, Grace Hopper, Isaac Newton, Napoleón Bonaparte).

---

## Resumen ejecutivo

**Calidad actual: C+.** El sistema funciona en producción pero arrastra:

| Dimensión | Estado | Objetivo |
|-----------|--------|----------|
| Sobreingeniería | 4 directorios vacíos + 4 packages scaffold + use cases ceremonial | Eliminar ~3000 líneas muertas |
| Acoplamiento | Services se instancian entre sí (no hay DI) | Introducir DI container |
| Errores silenciados | 172+ try/except, muchos con `pass` | Logging sistemático |
| Performance | 19 `find_all().to_list()` sin paginación, N+1 en WhatsApp | Paginación obligatoria + batching |
| Tests | 15/26 services sin test, 19/23 endpoints sin test | Cobertura mínima 40% en módulos críticos |
| Duplicación | 2 pipelines WhatsApp, schemas REST↔MCP, mapeo manual 416 líneas | Unificar + automatizar |

**Tres fases, 8 semanas estimadas:**

| Fase | Semanas | Líneas eliminadas | Riesgo |
|------|---------|-------------------|--------|
| **1.** Limpieza inicial | 1 | ~500 | Bajo |
| **2.** Consolidación | 3 | ~2000 | Medio |
| **3.** Arquitectura + Tests | 4 | — (refactor) | Alto |

---

## Fase 1 — Limpieza inicial (Semana 1)

**Objetivo:** Eliminar código muerto, directorios fantasma y ruido estructural. 0 riesgo de regresión.

### 1.1 Directorios vacíos — DELETE

| Ruta | Contenido | Evidencia |
|------|-----------|-----------|
| `apps/api/app/domain/` | Solo `__init__.py` + `.gitkeep` | `rg "from app.domain"` → 0 matches |
| `apps/api/app/repositories/` | Solo `__init__.py` + `.gitkeep` | `rg "from app.repositories"` → 0 matches |
| `apps/api/app/utils/` | Solo `__init__.py` + `fonts/` vacío | `rg "from app.utils"` → 0 matches |
| `apps/api/app/utils/fonts/` | Vacío | Sin archivos |
| `apps/mobile/lib/src/` | Solo `.gitkeep` | Sin archivos .dart |

**Acción:** `git rm -r` cada directorio.
**Riesgo:** Nulo.
**Payoff:** −4 directorios, −5 archivos.

### 1.2 Archivos placeholder/muertos — DELETE

| Ruta | Líneas | Evidencia |
|------|--------|-----------|
| `apps/mobile/lib/app/router.dart` | 1 | Comentario "Router placeholder". 0 imports |
| `apps/mobile/lib/app/navigation/route_guards.dart` | 4 | Clase vacía. 0 imports |
| `apps/mobile/lib/app/navigation/app_router.dart` | 19 | `AppRouter` nunca instanciado. 0 imports |
| `apps/mobile/lib/app/shell/widgets/shell_page_slot.dart` | ~30 | 0 imports |
| `apps/mobile/lib/playground/design_system_playground.dart` | 430 | Reemplazado por `widget_museum_screen.dart`. 0 imports |
| `apps/mobile/lib/features/equines/presentation/models/equine_demo_record.dart` | 15 | 0 referencias externas |
| `apps/api/app/services/sync_change_service.py` | 36 | Función `record_document_change()` definida pero nunca llamada |
| `apps/api/seed_equines_rf14.py` (raíz) | 320 | Copia exacta de `app/seed_equines_rf14.py` |
| `apps/mobile/pubspec.yaml` — dep `cupertino_icons` | — | No se usa en ningún `.dart`. Usan `material_symbols_icons` |

**Acción:** `git rm` cada archivo.
**Riesgo:** Nulo (verificado con grep).
**Payoff:** −9 archivos, ~855 líneas.

### 1.3 .gitkeep obsoletos — DELETE

| Ruta | Motivo |
|------|--------|
| `apps/api/app/services/.gitkeep` | Directorio con 29 .py reales |
| `apps/api/app/schemas/.gitkeep` | Directorio con 25 schemas |
| `apps/api/app/api/.gitkeep` | Directorio con endpoints/, router.py, deps.py |
| `apps/api/app/core/.gitkeep` | Directorio con config.py, db.py, errors.py |
| `apps/api/tests/.gitkeep` | Directorio con 37 tests |
| `apps/api/app/repositories/.gitkeep` | Directorio eliminado en 1.1 |
| `apps/api/app/domain/.gitkeep` | Directorio eliminado en 1.1 |
| `docs/setup/.gitkeep` | Directorio con 4 .md + README |
| `docs/decisions/.gitkeep` | Directorio con 8 ADRs + README |
| `docs/architecture/.gitkeep` | Directorio con 8 docs + README |
| `.github/workflows/.gitkeep` | Directorio con `quality.yml` |
| `packages/mobile_core/.gitkeep` | Directorio con código real |
| `apps/mobile/lib/src/.gitkeep` | Directorio eliminado en 1.1 |

**Acción:** `git rm` cada .gitkeep.
**Riesgo:** Nulo.
**Payoff:** −13 archivos.

### Resultado esperado Fase 1

| Métrica | Antes | Después |
|---------|-------|---------|
| Archivos totales API Python | ~202 | ~190 |
| Archivos totales Mobile Dart | ~192 | ~184 |
| Directorios fantasma | 4 | 0 |
| Código muerto confirmado | ~1355 líneas | 0 |
| Tiempo estimado | — | 1 día |

**Gate de verificación:**
```bash
# API
pytest apps/api/tests/ -q --tb=short  # 0 rotos
ruff check apps/api/app/               # 0 nuevos errores

# Mobile
cd apps/mobile && flutter analyze      # 0 errores
cd apps/mobile && flutter test          # 0 rotos
```

---

## Fase 2 — Consolidación (Semanas 2-4)

**Objetivo:** Eliminar duplicación masiva, reducir archivos enorme y unificar pipelines paralelos.

### 2.1 Unificar navegación mobile (Día 1)

**Problema:** 6 archivos de navegación para 1 esquema `onGenerateRoute`.

**Archivos involucrados:**
- `lib/app/navigation/route_names.dart` (constantes)
- `lib/features/auth/presentation/auth_routes.dart` (mismas constantes)
- `lib/app/navigation/app_router.dart` (no usado)
- `lib/app/navigation/route_guards.dart` (vacío, ya eliminado en F1)
- `lib/app/navigation/feature_route_registry.dart` (no usado)
- `lib/app/router.dart` (placeholder, ya eliminado en F1)

**Acción:**
1. Conservar `auth_routes.dart` como única fuente de verdad para rutas.
2. Eliminar `route_names.dart` (redundante).
3. Eliminar `app_router.dart`.
4. Eliminar `feature_route_registry.dart`.
5. El `onGenerateRoute` en `app.dart` ya funciona; dejar intacto.

**Riesgo:** Bajo. Las rutas se usan por nombre desde `Navigator.pushNamed()`.
**Payoff:** −3 archivos, −60 líneas.

### 2.2 Consolidar tema (Día 2)

**Problema:** `app_theme.dart` tiene métodos `light()` y `dark()` que son ~95% idénticos. Cualquier cambio de estilo se duplica.

**Archivo:** `lib/app/theme/app_theme.dart` (242 líneas)

**Acción:**
1. Extraer método privado:
```dart
ThemeData _themeData(ColorScheme colorScheme, Brightness brightness) {
  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: colorScheme,
    appBarTheme: _appBarTheme(colorScheme),
    cardTheme: _cardTheme(colorScheme),
    inputDecorationTheme: _inputDecorationTheme(colorScheme),
    elevatedButtonTheme: _elevatedButtonTheme(colorScheme),
    // ... todo lo demás parametrizado por colorScheme
  );
}
```
2. `light()` y `dark()` solo pasan `ColorScheme.fromSeed()` + `Brightness`.
3. Cada sub-tema (`_appBarTheme`, `_cardTheme`, etc.) es una función privada.

**Riesgo:** Bajo. Solo refactor interno, API pública no cambia.
**Payoff:** ~120 líneas eliminadas.

### 2.3 Romper widget monolítico de 1811 líneas (Días 3-5)

**Problema:** `reservation_detail_shell_screen.dart` es un `StatefulWidget` de 1811 líneas que mezcla UI, lógica de negocio, formateo, diálogos, caché de imágenes, y un `_FallbackRepository` inline.

**Acción por pasos:**

**2.3.1** Extraer funciones de estado duplicadas a un mixin o helper:

| Función | Ocurrencias |
|----------|-------------|
| `_paymentStatusLabel` | 2 (líneas 1051 y 1542) |
| `_formStatusLabel` | 2 (líneas 1019 y 1559) |
| `_paymentProofStatusLabel` / `_paymentProofStatusLabelStatic` | 2 (líneas 1109 y 1781) |
| `_paymentProofStatusTone` / `_paymentProofStatusToneStatic` | 2 (líneas 1124 y 1796) |
| `_formatColombianPrice` | 1 (líneas 506-537) — mover a `mobile_core` |

Crear archivo `lib/features/reservations/presentation/helpers/reservation_status_labels.dart`.

**2.3.2** Extraer `_FallbackRepository` a archivo compartido:

Actualmente definido 2 veces:
- `reservations_module_screen.dart:320-390`
- `reservation_detail_shell_screen.dart:1174-1244`

Mover a `lib/features/reservations/infrastructure/repositories/fallback_repository.dart`.

**2.3.3** Extraer sub-vistas inline en widgets separados:

| Widget inline | Nuevo archivo | Líneas aprox |
|---------------|---------------|-------------|
| `_ProofImageViewer` | `reservation_proof_image_viewer.dart` | ~120 |
| `_ClientDetailView` | `reservation_client_detail_view.dart` | ~140 |
| `_ParticipantDetailView` | `reservation_participant_detail_view.dart` | ~100 |

**2.3.4** Extraer diálogos inline:

| Diálogo | Nuevo archivo |
|---------|---------------|
| `_showApproveConfirmation` | `reservation_approve_dialog.dart` |
| `_showRejectDialog` | `reservation_reject_dialog.dart` |

**2.3.5** Mover `_formatColombiaPrice` a `packages/mobile_core/lib/src/formatting.dart`.

**Riesgo:** Medio. Requiere verificar que todos los parámetros se pasan correctamente a los nuevos widgets.
**Payoff:** Archivo principal ~800 líneas (vs 1811). −1000 líneas en el monolito.

### 2.4 Eliminar use cases ceremonial (Días 6-7)

**Problema:** 9 de 9 use cases en `auth/application/` son wrappers 1:1 sin lógica.

**Archivos a eliminar:**

| Use case | Líneas | Delega a |
|----------|--------|----------|
| `sign_in_use_case.dart` | 15 | `AuthRepository.signIn` |
| `bootstrap_session_use_case.dart` | 12 | `AuthRepository.bootstrapSession` |
| `logout_use_case.dart` | 12 | `AuthRepository.logout` |
| `change_password_use_case.dart` | 13 | `AuthRepository.changePassword` |
| `register_use_case.dart` | 13 | `AuthRepository.register` |
| `refresh_session_use_case.dart` | 12 | `AuthRepository.refreshSession` |
| `sync_profile_from_remote_use_case.dart` | 12 | `AuthRepository.syncProfileFromRemote` |
| `get_current_local_session_use_case.dart` | 10 | `AuthRepository.getCurrentLocalSession` |
| `enter_local_mode_use_case.dart` | 10 | `AuthRepository.enterLocalMode` |

**Acción:**
1. Eliminar `lib/features/auth/application/` directorio completo.
2. Refactorizar `AuthController` para llamar a `AuthRepository` directamente.
3. Conservar `auth_operation_policy.dart` si tiene lógica real (25 líneas, pero no se referencia — evaluar si se elimina también).

**Riesgo:** Medio. `AuthController` inyecta los use cases actualmente. Hay que cambiar constructor para inyectar `AuthRepository` directamente.
**Payoff:** −9 archivos, ~110 líneas.

### 2.5 Unificar pipeline de notificaciones WhatsApp (Semanas 2-3)

**Problema:** Existen dos pipelines paralelos:

| Pipeline | Entry point | Encolamiento | Reintentos | Idempotencia |
|----------|-------------|-------------|------------|-------------|
| A: `NotificationService` | `reservation_service.py:454` | Sí (outbox) | Sí (max_attempts) | dedup_key |
| B: `ReservationWhatsAppNotificationService` | `reservation_service.py:477` | No (síncrono) | No | Auditoría en reserva |

**Acción:**
1. Migrar funcionalidad de `ReservationWhatsAppNotificationService` a usar el outbox de `NotificationService`.
2. Eliminar `reservation_whatsapp_notification_service.py`.
3. Unificar en `notification_service.py` con un único método `enqueue_reservation_confirmed_logistics()`.

**Riesgo:** Alto — toca flujo de confirmación de reserva. Requiere:
- Test de integración que verifique que el mensaje llega a WhatsApp (vía mock del provider).
- Feature flag para rollout gradual.
- Rollback plan: restaurar pipeline B.

**Payoff:** −1 archivo (~400 líneas), 1 pipeline de notificación.

### 2.6 Mover seed scripts a `scripts/` (Día 8)

**Archivos:**
- `apps/api/app/seed_experiences_and_schedules_qa.py` (777 líneas)
- `apps/api/app/seed_reproducible.py` (934 líneas)
- `apps/api/app/seed_equines_rf14.py` (320 líneas)
- `apps/api/app/seed_form_test.py` (164 líneas)
- `apps/api/app/seed_proof_file_data.py` (96 líneas)
- `apps/api/app/seed_schedules_2026_q2.py` (857 líneas)
- `apps/api/app/migrations/backfill_schedule_is_active.py` (15 líneas)
- `apps/api/app/migrations/backfill_sync_metadata.py` (46 líneas)
- `apps/api/app/migrations/notify_existing_payments.py` (75 líneas)
- `apps/api/app/migrations/reset_reminders.py` (28 líneas)

**Acción:**
1. Crear `apps/api/scripts/` y `apps/api/scripts/migrations/`.
2. Mover scripts. Conservar imports absolutos (ajustar sys.path si es necesario).
3. Conservar `apps/api/app/migrations/seed_notification_templates.py` (importado en `lifespan.py`).

**Riesgo:** Bajo. No hay imports productivos de estos archivos.
**Payoff:** Código productivo más limpio, 10 archivos menos en `app/`.

### Resultado esperado Fase 2

| Métrica | Antes | Después |
|---------|-------|---------|
| Widget monolítico | 1811 líneas | ~800 líneas |
| Archivos navegación | 4 | 1 |
| Use cases ceremonial | 9 | 0 |
| Pipelines WhatsApp | 2 | 1 |
| Tema duplicado | 242 líneas | ~120 líneas |
| Seed scripts en `app/` | 6 | 0 |

**Gate de verificación:**
```bash
# API
pytest apps/api/tests/ -q --tb=short
ruff check apps/api/app/

# Mobile
cd apps/mobile && flutter analyze
cd apps/mobile && flutter test
cd apps/mobile && flutter build apk --debug  # build check
```

---

## Fase 3 — Arquitectura + Tests (Semanas 5-8)

**Objetivo:** Desacoplar dependencias, eliminar fugas de performance, y cubrir brechas de test críticas.

### 3.1 Introducir DI container (Semana 5)

**Problema:** Services crean sus dependencias en `__init__`:
```python
# reservation_service.py:72-74
self.config_service = ConfigService()
self.notification_service = NotificationService()
self.participant_form_link_service = ParticipantFormLinkService()
```

**Acción:**
1. Crear `apps/api/app/core/di.py` como registry centralizado:
```python
class Container:
    _instance = None
    
    def __init__(self):
        self.config_service: Optional[ConfigService] = None
        self.notification_service: Optional[NotificationService] = None
        # ...
    
    @classmethod
    def init(cls):
        c = cls()
        c.config_service = ConfigService()
        c.notification_service = NotificationService(c.config_service)
        # ... orden de inicialición respetando dependencias
        cls._instance = c
        return c
    
    @classmethod
    def get(cls):
        return cls._instance
```
2. Inicializar en `lifespan.py` startup.
3. Cada service recibe dependencias por constructor (inyección).
4. Opcional: usar `fastapi.Depends` para endpoints:
```python
@router.get("/reservations")
async def list_reservations(
    service: ReservationService = Depends(get_reservation_service)
):
```

**Riesgo:** Alto. Cambia la forma en que se construye cada service. Requiere:
- Refactor de los 29 services para recibir dependencias por constructor.
- Refactor de los 25 endpoints que instancian services como singletons a nivel módulo.
- Test de integración que verifique que el grafo de dependencias se construye correctamente.

**Payoff:** 
- Testeabilidad inmediata de todos los services.
- Fin del monkey-patching en tests.
- Orden explícito de inicialización.

### 3.2 Reemplazar mapeo manual con `model_dump` (Semana 5, paralelo a 3.1)

**Problema:** `mappers.py` (416 líneas) copia campo por campo de cada Document a su Schema:
```python
# mappers.py:97-153 — 30+ asignaciones manuales
return ReservationResponseSchema(
    id=str(doc.id),
    code=doc.code,
    status=doc.status,
    experience_id=str(doc.experience_id),
    ...
)
```

**Acción:**
1. Usar `Document.model_dump()` con exclusión selectiva:
```python
def document_to_schema(doc: BaseDocument, schema_cls: Type[T], exclude: set[str] = None) -> T:
    """Convierte un Document Beanie a Schema Pydantic usando model_dump."""
    data = doc.model_dump(exclude=exclude or {"id", "revision_id"})
    data["id"] = str(doc.id)
    return schema_cls(**data)
```
2. Para casos complejos (cálculos, joins), usar hełper.
3. Agregar test que verifique que todos los campos del Document existen en el Schema:
```python
def test_all_reservation_fields_mapped():
    doc_fields = set(ReservationDocument.model_fields.keys())
    schema_fields = set(ReservationResponseSchema.model_fields.keys())
    unmapped = doc_fields - schema_fields - {"revision_id", "id"}
    assert not unmapped, f"Fields not in schema: {unmapped}"
```

**Riesgo:** Medio. `model_dump()` puede no serializar correctamente tipos anidados (ObjectId, datetime). Requiere verificación manual de cada Schema de salida.
**Payoff:** −350 líneas de mapeo manual. Zero mantenimiento al agregar campos.

### 3.3 Paginación obligatoria (Semana 6)

**Problema:** 19 endpoints/servicios cargan colecciones completas con `find_all().to_list()`.

**Acción:**

**3.3.1** Endpoints REST — agregar `limit`/`skip`:

```python
# En todos los endpoints LIST
@router.get("/reservations")
async def list_reservations(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: ReservationService = Depends(get_reservation_service)
):
    return await service.list(limit=limit, offset=offset)
```

**3.3.2** Servicios — refactorizar queries:
```python
# Antes
return await ReservationDocument.find_all().to_list()

# Después
return await ReservationDocument.find_all().skip(offset).limit(limit).to_list()
```

**3.3.3** Analytics — reemplazar carga completa con aggregation pipeline:

| Archivo | Línea | Agregación MongoDB |
|---------|-------|-------------------|
| `analytics.py:116` | `reservations = await ReservationDocument.find_all().to_list()` | `$group` + `$count` |
| `analytics.py:192` | idem | `$match` + `$group` |
| `analytics.py:277` | idem | `$bucket` por estado |
| `analytics.py:456` | `equines = await EquineDocument.find_all().to_list()` | `$count` + `$group` |

**3.3.4** Colecciones pequeñas conocidas (< 100 docs esperados): mantener `find_all().to_list()` pero agregar comentario `# known-small: <reason>`.

Ejemplo: `NotificationTemplateDocument.find_all().to_list()` (decenas de templates).

**Riesgo:** Medio. Pueden romperse clients que dependen de respuestas sin paginación. Agregar header `X-Total-Count`.
**Payoff:** Protección contra crecimiento. 0 posibilidade de OOM con 100k+ documentos.

### 3.4 Eliminar N+1 queries (Semana 6, paralelo)

**3.4.1** WhatsApp events — `conversation_turn_worker.py:168-173`:
```python
# ANTES
for msg_id in reloaded.message_ids:
    event = await WhatsAppInboundEventDocument.find_one({"wa_message_id": msg_id})
# DESPUÉS
events_docs = await WhatsAppInboundEventDocument.find(
    {"wa_message_id": {"$in": reloaded.message_ids}}
).to_list()
events_dict = {str(e.wa_message_id): e for e in events_docs}
```

**3.4.2** Notificaciones internas — `notification_service.py:127-151`:
```python
# ANTES
for user in internal_users:
    entry = await self.enqueue(...)  # 2 queries + 1 insert cada uno
# DESPUÉS
template = await NotificationTemplateDocument.find_one({"key": template_key})
entries = [NotificationOutboxDocument(user_id=user.id, ...) for user in internal_users]
await NotificationOutboxDocument.insert_many(entries)
```

**3.4.3** AssignmentService — paralelizar gets independientes:
```python
# ANTES
reservation = await ReservationDocument.get(...)
participant = await ParticipantDocument.get(...)
equine = await EquineDocument.get(...)
# DESPUÉS
reservation, participant, equine = await asyncio.gather(
    ReservationDocument.get(...),
    ParticipantDocument.get(...),
    EquineDocument.get(...),
)
```

**Riesgo:** Bajo-Medio. Cambios localizados.
**Payoff:** −15x queries en WhatsApp, −Nx en notificaciones.

### 3.5 Logging en lugar de `except: pass` (Semana 7)

**Problema:** 172+ bloques `try/except` — muchos silencian errores:
```python
# reservation_service.py:262
except Exception:
    pass  # notificación que falla sin registro
```

**Acción:**
1. Crear decorador `@log_error(logger, reraise=False)`:
```python
def log_error(logger: logging.Logger, reraise: bool = False, message: str = ""):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{message or func.__name__}: {e}", exc_info=True)
                if reraise:
                    raise
        return wrapper
    return decorator
```
2. Refactorizar por módulo, priorizando servicios críticos:
   - `reservation_service.py` (11 bloques — prioridad #1)
   - Core de notificaciones
   - MCP tools (logging manual repetitivo ~40 ocurrencias → decorador)

**Riesgo:** Medio. Cambiar `except: pass` a logging puede revelar errores existentes. Planeado: monitorear logs post-deploy 48h.
**Payoff:** Errores visibles. Sin fallos silenciosos.

### 3.6 Tests críticos (Semanas 7-8)

Priorizados por riesgo de negocio:

| Prioridad | Test | Archivo | Líneas est. | Depende de |
|-----------|------|---------|-------------|------------|
| P0 | PaymentProofService — verify/reject/approve/rollback | `test_payment_proof_service.py` | 200 | Fase 3.1 (DI) |
| P0 | Cancelación en cada estado de reserva | `test_reservation_service_cancel.py` | 250 | Fase 3.1 (DI) |
| P0 | Concurrencia — dos confirmaciones simultáneas | `test_concurrency_reservation.py` | 100 | Fase 3.1 (DI) |
| P1 | BookingService — flujo quote→pre-reserve→confirm | `test_booking_service.py` | 300 | Fase 3.1 (DI) |
| P1 | No-show transitions | Extender `test_reservation_transitions.py` | 150 | — |
| P1 | EquineService CRUD | `test_equine_service.py` | 150 | Fase 3.1 (DI) |
| P1 | UserService CRUD | `test_user_service.py` | 150 | Fase 3.1 (DI) |
| P2 | 10 endpoints REST principales (happy path + 400/404) | Por endpoint | 50 c/u | — |
| P2 | LLM provider — timeouts, 503, malformed | Extender `test_gemini_provider.py` | 100 | — |

**Recomendación:** No esperar a que Fase 3.1 termine para empezar tests. Los tests de integración con TestClient + MongoDB mock pueden escribirse en paralelo.

### Resultado esperado Fase 3

| Métrica | Antes | Después |
|---------|-------|---------|
| Services sin test | 15/26 | 5/26 |
| Endpoints sin test | 19/23 | 9/23 |
| Cobertura estimada | ~15% | ~40% |
| `find_all().to_list()` | 19 | 3 (con comentario `known-small`) |
| N+1 queries WhatsApp | 15 por turno | 1 |
| `except: pass` silencioso | ~30 | 0 |
| Mapeo manual frágil | 416 líneas | ~50 (helpers genéricos) |

---

## Resumen de esfuerzo y payoff

| Fase | Semanas | Archivos tocados | Líneas eliminadas | Líneas agregadas | Neto | Riesgo |
|------|---------|-----------------|-------------------|------------------|------|--------|
| 1. Limpieza | 1 | ~30 | ~1355 | 0 | **−1355** | Bajo |
| 2. Consolidación | 3 | ~25 | ~2000 | ~400 | **−1600** | Medio |
| 3. Arquitectura + Tests | 4 | ~60 | ~800 | ~2500 | **+1700** | Alto |
| **Total** | **8** | **~115** | **~4155** | **~2900** | **−1255** | — |

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Regresión en Fase 2.5 (WhatsApp pipeline) | Media | Alto (notificaciones caídas) | Feature flag, rollout gradual, rollback plan |
| model_dump() falla en tipos anidados | Media | Medio | Test de integración por Schema antes del deploy |
| DI container mal configurado | Baja | Alto (app no inicia) | Test de integración que verifica grafo de dependencias |
| Paginación rompe clients mobile | Alta | Medio | Header `X-Total-Count`, versionar API o comunicar cambio |
| Logging revela errores existentes | Alta | Bajo (monitoreo, no bug) | Alertar al equipo, no silenciar de vuelta |

## Checklist de pre-requisitos

- [ ] Git branch `feat/plan-mejora` creada desde `main`
- [ ] Todos los tests existentes pasan antes de empezar
- [ ] CI pipeline configurado (o verificación manual por fase)
- [ ] Feature flag para Fase 2.5 (WhatsApp pipeline)
- [ ] Acceso a logs de producción para monitoreo post-Fase 3.5

---

*Fin del plan. Generado a partir de auditoría cruzada multigente.*

*Próximo paso: ¿ejecuto Fase 1 (limpieza inicial)?*
