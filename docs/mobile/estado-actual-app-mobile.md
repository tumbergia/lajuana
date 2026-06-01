# Estado actual de la app móvil — La Juana

## 1. Resumen ejecutivo

La app móvil de La Juana está **significativamente más avanzada que un prototipo visual**, pero **no está lista para operación real con datos de producción**. La app cuenta con una base sólida: shell autenticado con bottom nav funcional, tema claro/oscuro completo, un catálogo de widgets reutilizables amplio, navegación por tabs con anidación por módulo, y un módulo de auth completo con login, registro, refresh token, sesión local SQLite y detección de conectividad.

**El módulo de reservas ha sido desmockeado y conectado al backend real.** Ya no usa fixtures; consume `GET /api/v1/reservations` y `GET /api/v1/reservations/{id}` con autenticación, cache local SQLite, y sin anti-patrón N+1. El frontend listaba cada reserva con datos de experiencia/schedule resueltos en batch por el backend.

**El detalle de reserva (v2) ahora incluye participantes y comprobantes de pago en modo lectura.** El backend enriqueció `GET /reservations/{id}` con `participants[]` y `payment_proofs[]` resueltos mediante `$in` query sobre `participant_ids` / `payment_proof_ids`. El frontend muestra datos reales en las subrutas Participantes y Pagos, incluyendo alertas operativas con scroll-to-highlight, vista detallada de participante, y visor de comprobantes por streaming.

**Además, el admin puede aprobar, rechazar, deshacer verificación y deshacer rechazo de comprobantes directamente desde la app móvil**, con confirmación explícita, motivo obligatorio en rechazo, auditoría completa y actualización instantánea del detalle de reserva. El guía no ve ni puede ejecutar acciones financieras — el backend bloquea por permisos en dos capas.

**El admin también puede confirmar reservas desde la app una vez validado el pago.** El botón "Confirmar reserva" aparece solo para admin en reservas con pago verificado y estado no terminal. Al confirmar, el sistema revalida disponibilidad y descuenta cupos de forma atómica, genera el enlace de formulario de participantes, crea auditoría (`reservation.confirmed`), y devuelve el detalle actualizado. La retroalimentación se muestra como SnackBar (no inline en el DOM). Doble-tap bloqueado. El confirm requiere conexión — no hay cola offline.

**Parche backend incluido**: Se corrigió un bug donde `schedule.save()` fallaba con `Cannot encode datetime.time` al serializar `start_time` de tipo `time` (problema conocido de Beanie). Se creó `_save_schedule_status()` que usa motor collection `update_one` en producción y cae a `.save()` en tests. También se corrigió un type mismatch en `$ne` que impedía excluir la reserva actual del chequeo de disponibilidad.

Sin embargo, **el resto de módulos funcionales (dashboard, equinos, participantes, proveedores) aún usan únicamente datos mock/fixtures hardcodeados**. 

El módulo de catálogos (`CatalogsModule`) es el más completo: tiene repositorio, sync API, base de datos SQLite local, cola de operaciones offline y sincronización bidireccional con el backend. Pero este módulo solo maneja experiences, schedules, reservation_rules y emergency_contacts — **no maneja reservas, participantes, equinos, asignaciones ni comprobantes de pago**.

Los paquetes `packages/mobile_ui`, `mobile_domain`, `mobile_mocks` siguen **vacíos** (solo `.gitkeep` y `pubspec.yaml`). El paquete `mobile_core` ahora contiene `date_utils.dart` con `formatDate()` para normalización de fechas.

| Área | Estado | Evidencia | Observación |
|---|---|---|---|
| Shell/app base | Implementado | `lib/app/app.dart` + `lib/app/shell/authenticated_shell.dart` | Shell funcional con auth y bottom nav |
| Navegación | Implementado | `lib/app/navigation/` + `authenticated_shell.dart` | Navegación con tabs + Navigator anidado |
| Design system/widgets | Implementado | `lib/app/widgets/` (18 widgets + 8 cards) | Catálogo completo y reutilizable |
| Backend integration | Parcial | `auth_api_client.dart` + `catalogs_sync_api.dart` + `reservations_api_client.dart` | Auth, catálogos y **reservas** conectados; faltan equinos, participantes, etc. El API client ahora soporta descarga de comprobantes por streaming. |
| Persistencia local | Implementado | `sqflite` en `auth_database.dart` + `catalogs_database.dart` + `reservations_database.dart` | SQLite para sesión, catálogos y **cache de reservas** (incluye participantes y comprobantes) |
| Reservas | **Implementado (real + detalle v2)** | `lib/features/reservations/` | **Conectado a backend real con cache SQLite. Detalle incluye participantes, comprobantes y bloqueos operativos.** |
| Equinos | Parcial (mock) | `lib/features/equines/` | UI básica con datos mock |
| Clientes/Participantes | Parcial (mock) | `lib/features/participants/` | UI básica con datos mock |
| Voz/asistente | Implementado | `lib/app/voice/` | Pantalla funcional de voz, sin NLP real |

## 2. Estructura real de carpetas

```txt
apps/mobile/lib/
  main.dart
  bootstrap/
    bootstrap.dart
  app/
    api_base_url.dart
    app.dart                                    # LaJuanaApp (StatefulWidget)
    router.dart                                 # Placeholder (1 línea)
    bootstrap/
      dev_loader_screen.dart                    # Catálogo visual de widgets
      startup_gate.dart                         # Puerta de entrada (bootstrap → login o home)
      startup_orchestrator.dart
      startup_state.dart
    navigation/
      app_router.dart                           # Constantes + debug names
      feature_route_registry.dart               # Mapa AppNavItem → FeatureRootBuilder
      route_guards.dart                         # Vacío (placeholder)
      route_names.dart                          # Constantes de ruta
      shell_navigation_controller.dart          # ChangeNotifier del tab actual
    shell/
      authenticated_shell.dart                  # Scaffold + AppTopBar + BottomNav + tabs
      widgets/
        shell_page_slot.dart                    # Placeholder
        shell_status_region.dart                # Banners de conectividad/sesión
    theme/
      app_colors.dart                          # ColorScheme claro/oscuro
      app_text_theme.dart                      # Manrope + Inter
      app_radii.dart
      app_theme.dart                           # ThemeData light() y dark()
      app_theme_notifier.dart                  # InheritedWidget
      theme_extensions.dart                    # AppThemeTokens
    voice/
      voice_context.dart                       # Enum VoiceContext
      voice_route.dart                         # openVoiceScreen()
      voice_screen.dart                        # UI de voz
      voice_visualizer.dart                    # Barras animadas
    widgets/
      app_badge.dart
      app_bottom_nav.dart                      # AppNavItem enum + bottom bar
      app_breadcrumb.dart
      app_button.dart
      app_card.dart                            # Con soporte flip 3D
      app_centered_loader.dart
      app_entity_row_card.dart
      app_metric_card.dart
      app_scaffold.dart
      app_section_header.dart
      app_segmented_filter.dart
      app_status_banner.dart
      app_term_help.dart
      app_text_field.dart
      app_timeline.dart                        # Timeline + items + entry cards
      app_top_bar.dart                         # Logo + título + botones
      app_voice_fab.dart
      cards/
        app_assignment_card.dart
        app_centered_badge_card.dart
        app_experience_card.dart
        app_image_feature_card.dart
        app_logbook_timeline.dart
        app_pricing_tiers_table.dart
        app_selectable_card.dart
        app_stats_card.dart
  features/
    auth/                                      # Completo (Clean Architecture)
      application/                             # 10 use cases
      domain/                                  # auth_models, auth_enums, auth_repository
      infrastructure/                          # api client, DTOs, DB, data sources, repos
        connectivity/                          # BackendReachability, NetworkStatus
        local/                                 # AuthDatabase, SessionLocalDataSource, UserLocalDataSource
        remote/                                # AuthApiClient, AuthDtos
        repositories/                          # AuthRepositoryImpl
        token_storage.dart
      presentation/                            # AuthController, screens, routes
    catalogs/                                  # Moderadamente completo
      catalogs_module.dart
      catalogs.dart
      data/                                    # CatalogsRepository (~1443 líneas), SyncAPI, DB
      experiences/                             # Domain model + data + presentation (CRUD)
      schedules/                               # Domain model + data + presentation (CRUD)
      reservation_rules/                       # Domain model + data + presentation
      emergency_contacts/                      # Domain model + data + presentation
      presentation/pages/catalogs_home_page.dart
    configuration/
      presentation/screens/more_flow_screen.dart
    dashboard/
      presentation/
        controllers/dashboard_controller.dart
        screens/dashboard_screen.dart
        widgets/ (4 bloques)
    equines/
      presentation/
        controllers/equines_controller.dart
        models/equine_demo_record.dart
        screens/equines_module_screen.dart
    participants/
      presentation/
        controllers/participants_controller.dart
        screens/participants_module_screen.dart
    providers/
      presentation/screens/providers_module_screen.dart   # Placeholder
    reservations/                               # Conectado a backend real
      reservations_module.dart                  # Factory con DI real
      domain/                                   # Modelos de dominio + repositorio
        models/ (9 modelos: detail, list item, status, payment, timeline, alerts, participant_detail, payment_proof_detail)
        repositories/reservations_repository.dart
      infrastructure/
        remote/                                 # ReservationsApiClient + DTOs (incluye proof download)
        local/                                  # ReservationsDatabase + cache SQLite
        mappers/                                # DTO ↔ Domain ↔ ViewModel
        repositories/                           # ReservationsRepositoryImpl
      presentation/
        controllers/ (6 controllers, ahora poblados con datos reales)
        models/reservation_view_models.dart
        screens/ (3 screens)
        widgets/
          reservation_row_card.dart
          payment_status_card.dart
    shared/
      presentation/widgets/module_subroute_header.dart
  playground/
    design_system_playground.dart               # DevWidgetCatalogScreen (767 líneas)
  src/
    .gitkeep                                    # Vacío
```

**Análisis de carpetas:**

- **Infraestructura**: `app/` (shell, theme, navigation, bootstrap, voz, widgets)
- **Pantallas**: `features/auth/presentation/screens`, `features/dashboard/presentation/screens`, `features/reservations/presentation/screens`, `features/equines/presentation/screens`, `features/participants/presentation/screens`, `features/configuration/presentation/screens`, `features/providers/presentation/screens`, `features/catalogs/*/presentation/pages`
- **Widgets reutilizables**: `app/widgets/` (18 widgets) + `app/widgets/cards/` (8 cards) + `features/shared/presentation/widgets/`
- **Prototipo/playground**: `playground/design_system_playground.dart` — catálogo de widgets en modo dev
- **Vacías/infrautilizadas**: `src/` (solo `.gitkeep`), `packages/mobile_ui/`, `packages/mobile_domain/`, `packages/mobile_mocks/` (todos vacíos)
- **`mobile_core`**: ahora poblado con `lib/src/date_utils.dart` — función `formatDate()` para normalización de fechas
- **Router placeholder**: `app/router.dart` — solo un comentario

## 3. Entry point y shell de aplicación

| Archivo | Responsabilidad actual | Estado | Observación |
|---|---|---|---|
| `main.dart` | Llama `bootstrap()` | OK | 5 líneas |
| `bootstrap/bootstrap.dart` | Resuelve API base URL + ejecuta `LaJuanaApp` | OK | Usa `--dart-define API_BASE_URL` |
| `app/api_base_url.dart` | Resuelve URL base según plataforma (Android emulador, web, físico) | OK | Soporta `10.0.2.2`, `localhost`, etc. |
| `app/app.dart` | `LaJuanaApp` → MaterialApp con `onGenerateRoute`, tema claro/oscuro, transición animada | OK | Inicializa `AuthController`, `CatalogsModule` |
| `app/bootstrap/startup_gate.dart` | Pantalla de carga inicial → decide login o home | OK | Usa `StartupOrchestrator` |
| `app/bootstrap/startup_orchestrator.dart` | Delega en `AuthController.appStarted()` | OK | 11 líneas |
| `app/shell/authenticated_shell.dart` | Scaffold principal con `AppTopBar`, `AppBottomNav`, banners, Navigator anidado por tab | OK | Shell real y reusable con navegación por tabs |
| `app/shell/widgets/shell_status_region.dart` | Banners de conectividad/sesión | OK | Reactivo a `AuthController` |
| `app/shell/widgets/shell_page_slot.dart` | Wrapper vacío de documentación | Placeholder | 11 líneas, no se usa |

**El shell actual puede reutilizarse para módulos de Reservas, Equinos, Clientes y Más.** Ya incluye `AppNavItem.reservas`, `AppNavItem.equinos`, `AppNavItem.clientes`, `AppNavItem.mas`.

## 4. Navegación actual

La app usa **`MaterialApp` con `onGenerateRoute` (Navigator 1.0)** y **Navigator anidado** dentro del shell para cada tab.

No usa `go_router` ni Navigator 2.0. El archivo `app/router.dart` es un placeholder: `// Router placeholder — add go_router or Navigator 2.0 setup here when needed.`

| Ruta/Pantalla | Existe | Cómo se navega | Archivo | Problema |
|---|---|---|---|---|
| `/session-gate` | Sí | Ruta inicial en `MaterialApp` | `startup_gate.dart` | OK |
| `/login` | Sí | `pushReplacementNamed` desde startup | `login_screen.dart` | OK |
| `/register` | Sí | `pushNamed` desde login | `register_screen.dart` | OK |
| `/home` | Sí | `pushReplacementNamed` desde startup/login | `authenticated_shell.dart` | Navegación por tabs anidados |
| `/session-view` | Sí | `pushNamed` desde más | `session_view_screen.dart` | OK |
| `/change-password` | Sí | `pushNamed` desde session view | `change_password_screen.dart` | OK |
| `/voice` | Sí | `Navigator.push` desde `openVoiceScreen()` | `voice_route.dart` | Modal de voz |
| Reserva detail | Sí | `Navigator.push` desde `ReservationsModuleScreen` | `reservation_detail_shell_screen.dart` | Sin ruta nombrada, push directo |
| Catálogos (experiencias, schedules, etc.) | Sí | `Navigator.push` desde `MoreFlowScreen` | varios | Sin ruta nombrada, push directo |
| Providers | Sí | Placeholder, sin datos reales | `providers_module_screen.dart` | Placeholder |

**AppBottomNav** no es solo visual. Cambia efectivamente de pantalla mediante el `ShellNavigationController` y `Navigator` anidados en `AuthenticatedShell`. Soporta 5 tabs: Inicio, Reservas, Equinos, Clientes, Más.

## 5. Catálogo real de widgets existentes

### 5.1 Shell y navegación

| Widget | Archivo | Propósito real | Props principales | Usado en | Estado |
|---|---|---|---|---|---|
| `AppScaffold` | `app/widgets/app_scaffold.dart` | Scaffold wrapper con scroll y padding | child, appBar, bottomNav, scrollable, padding | Muchas pantallas | Listo para reutilizar |
| `AppTopBar` | `app/widgets/app_top_bar.dart` | Barra superior con logo, título y botones | logoAssetPath, title, onThemeToggle, onNotificationsTap | `AuthenticatedShell`, `DevWidgetCatalogScreen` | Listo para reutilizar |
| `AppBottomNav` | `app/widgets/app_bottom_nav.dart` | Bottom navigation con 5 tabs + acceso a voz por long-press | current, onTap | `AuthenticatedShell`, `DevWidgetCatalogScreen`, `VoiceScreen` | Listo para reutilizar |
| `AppNavItem` | `app/widgets/app_bottom_nav.dart` | Enum con 5 tabs + `none` | — | `AppBottomNav`, `ShellNavigationController`, etc. | Listo para reutilizar |

### 5.2 Componentes visuales base

| Widget | Archivo | Propósito real | Props principales | Usado en | Estado |
|---|---|---|---|---|---|
| `AppCard` | `app/widgets/app_card.dart` | Card tonal con flip 3D opcional | child, backChild, tone, accentColor, outlined, onTap | Dev catalog, status banners | Listo para reutilizar |
| `AppButton` | `app/widgets/app_button.dart` | Botón primary/secondary/ghost | label, onPressed, icon, variant, expanded, height | Muchas pantallas | Listo para reutilizar |
| `AppBadge` | `app/widgets/app_badge.dart` | Badge con tonos (neutral/primary/success/danger/warning/ghost) | label, tone, size, icon, uppercase | Muchas pantallas | Listo para reutilizar |
| `AppMetricCard` | `app/widgets/app_metric_card.dart` | Card de métrica con valor grande | title, value, suffix, supportingText, icon, tone | Dashboard, Participants | Listo para reutilizar |
| `AppSectionHeader` | `app/widgets/app_section_header.dart` | Encabezado de sección hero/compact | title, eyebrow, subtitle, trailing, variant | Muchas pantallas | Listo para reutilizar |
| `AppEntityRowCard` | `app/widgets/app_entity_row_card.dart` | Fila de entidad con badge, leading, trailing | title, subtitle, badge, selected, onTap, leading, trailing | Dashboard, Reservas, Equinos | Listo para reutilizar |
| `AppBreadcrumb` | `app/widgets/app_breadcrumb.dart` | Navegación tipo breadcrumb | items, separator, currentIndex, onItemTap | Dev catalog (no usado en producción) | Visual/prototipo |
| `AppCenteredLoader` | `app/widgets/app_centered_loader.dart` | Loader centrado | strokeWidth | Dev catalog, MoreFlow | Listo para reutilizar |
| `AppTermHelp` | `app/widgets/app_term_help.dart` | Botón de ayuda con popup | title, message | No identificado en uso real | Visual/prototipo |

### 5.3 Formularios y filtros

| Widget | Archivo | Propósito real | Props principales | Usado en | Estado |
|---|---|---|---|---|---|
| `AppTextField` | `app/widgets/app_text_field.dart` | Campo de texto filled/underlined | controller, label, hintText, suffix, maxLines, variant | Dev catalog, MoreFlow, login | Listo para reutilizar |
| `AppSegmentedFilter` | `app/widgets/app_segmented_filter.dart` | Filtro segmentado horizontal | items, value, onChanged, expanded | Dashboard, Reservas, Detail | Listo para reutilizar |

### 5.4 Timeline y operación

| Widget | Archivo | Propósito real | Props principales | Usado en | Estado |
|---|---|---|---|---|---|
| `AppTimeline` | `app/widgets/app_timeline.dart` | Línea de tiempo vertical | children, lineLeft | Dev catalog, Reservas detail, Equinos | Listo para reutilizar |
| `AppTimelineItem` | `app/widgets/app_timeline.dart` | Item de timeline con nodo | state, child, lineLeft, nodeSize | Con `AppTimeline` | Listo para reutilizar |
| `AppTimelineEntryCard` | `app/widgets/app_timeline.dart` | Card de entrada en timeline | date, title, description, badge, highlightedContent, footer | Con `AppTimelineItem` | Listo para reutilizar |
| `AppTimelineMetrics` | `app/widgets/app_timeline.dart` | Métricas dentro de timeline | items | Dev catalog | Visual/prototipo |
| `AppStatusBanner` | `app/widgets/app_status_banner.dart` | Banner de estado informativo/warning/danger | title, message, tone, icon, badgeLabel, onTap | ShellStatusRegion, Reservation detail | Listo para reutilizar |

### 5.5 Voz/asistente

| Widget | Archivo | Propósito real | Props principales | Usado en | Estado |
|---|---|---|---|---|---|
| `VoiceScreen` | `app/voice/voice_screen.dart` | Pantalla completa de voz | voiceContext | Desde `openVoiceScreen()` | Visual/prototipo |
| `VoiceVisualizer` | `app/voice/voice_visualizer.dart` | Barras animadas de visualización de voz | barCount, color, barWidth, minHeight, maxHeight, gap, isActive | Dentro de `VoiceScreen` | Visual/prototipo |
| `AppVoiceFab` | `app/widgets/app_voice_fab.dart` | FAB de micrófono | onTap, size, elevated, icon | Dev catalog, `VoiceScreen` | Listo para reutilizar |

### 5.6 Cards especializadas

| Widget | Archivo | Propósito real | Props principales | Usado en | Estado |
|---|---|---|---|---|---|
| `AppSelectableCard` | `app/widgets/cards/app_selectable_card.dart` | Card seleccionable | selected, onTap, child | Dev catalog | Listo para reutilizar |
| `AppImageFeatureCard` | `app/widgets/cards/app_image_feature_card.dart` | Card con imagen de feature | title, subtitle, image, selected, badge | Dev catalog | Listo para reutilizar |
| `AppStatsCard` | `app/widgets/cards/app_stats_card.dart` | Card con estadísticas | eyebrow, title, selected, topRight, children | Dev catalog | Listo para reutilizar |
| `AppExperienceCard` | `app/widgets/cards/app_experience_card.dart` | Card de experiencia (commercial/compact/operational) | variant, data, selected, onPrimaryAction | Dev catalog | Visual/prototipo |
| `AppAssignmentCard` | `app/widgets/cards/app_assignment_card.dart` | Card de asignación jinete-equino-silla | startTimeLabel, reservationLabel, participant, equine, saddleLabel, loadRatio, state | Dev catalog | Visual/prototipo |
| `AppCenteredBadgeCard` | `app/widgets/cards/app_centered_badge_card.dart` | Card centrada con badges | kicker, title, subtitle, tone, badges, onTap, onTrailingTap | Dev catalog | Visual/prototipo |
| `AppPricingTiersTable` | `app/widgets/cards/app_pricing_tiers_table.dart` | Tabla de precios por tramos | currency, pricesAreNet, notes, tiers | Dev catalog | Visual/prototipo |
| `AppLogbookTimeline` | `app/widgets/cards/app_logbook_timeline.dart` | Timeline de bitácora con fotos | entries (AppLogbookTimelineEntry) | Dev catalog | Visual/prototipo |

### 5.7 Shared widgets

| Widget | Archivo | Propósito real | Props principales | Usado en | Estado |
|---|---|---|---|---|---|
| `ModuleSubrouteHeader` | `features/shared/presentation/widgets/module_subroute_header.dart` | Cabecera de módulo con filtro segmentado | eyebrow, title, subrouteLabels, currentSubrouteIndex, onSubrouteTap | Dashboard, Reservas, Equinos, Participantes | Listo para reutilizar |

## 6. Pantallas existentes

| Pantalla | Archivo | Propósito aparente | Usa datos reales | Usa mocks | Estado |
|---|---|---|---|---|---|
| `StartupGate` | `app/bootstrap/startup_gate.dart` | Bootstrap + decisión login/home | Sí (auth) | No | OK |
| `LoginScreen` | `features/auth/presentation/screens/login_screen.dart` | Login con email/password | Sí (API) | No | OK |
| `RegisterScreen` | `features/auth/presentation/screens/register_screen.dart` | Registro de usuario | Sí (API) | No | OK |
| `SessionViewScreen` | `features/auth/presentation/screens/session_view_screen.dart` | Ver sesión actual | Sí (local) | No | OK |
| `ChangePasswordScreen` | `features/auth/presentation/screens/change_password_screen.dart` | Cambiar contraseña | Sí (API) | No | OK |
| `DashboardScreen` | `features/dashboard/presentation/screens/dashboard_screen.dart` | Tablero operativo | No | Sí (ReservationPresentationFixtures) | Mockeado |
| `ReservationsModuleScreen` | `features/reservations/presentation/screens/reservations_module_screen.dart` | Listado y gestión de reservas | **Sí (backend real)** | No | **Conectado** |
| `ReservationDetailShellScreen` | `features/reservations/presentation/screens/reservation_detail_shell_screen.dart` | Detalle de reserva con subrutas | **Sí (backend real)** | No | **Conectado** |
| `EquinesModuleScreen` | `features/equines/presentation/screens/equines_module_screen.dart` | Gestión de equinos | No | Sí (EquineDemoRecord hardcodeado) | Mockeado |
| `ParticipantsModuleScreen` | `features/participants/presentation/screens/participants_module_screen.dart` | Gestión de participantes | No | Sí (ReservationPresentationFixtures) | Mockeado |
| `ProvidersModuleScreen` | `features/providers/presentation/screens/providers_module_screen.dart` | Catálogo de proveedores | No | Placeholder | Placeholder |
| `MoreFlowScreen` | `features/configuration/presentation/screens/more_flow_screen.dart` | Menú "Más" (perfil, contactos, catálogos) | Parcial (contactos vía API, catálogos mock) | Parcial | Mixto |
| `CatalogsHomePage` | `features/catalogs/presentation/pages/catalogs_home_page.dart` | Home de catálogos (experiencias, schedules, reglas, contactos) | Sí (desde SQLite/API) | No | OK (usa datos reales) |
| `ExperiencesPage` | `features/catalogs/experiences/presentation/pages/experiences_page.dart` | CRUD de experiencias | Sí (SQLite local) | No | OK |
| `ExperienceDetailPage` | `features/catalogs/experiences/presentation/pages/experience_detail_page.dart` | Detalle de experiencia | Sí | No | OK |
| `ExperienceFormPage` | `features/catalogs/experiences/presentation/pages/experience_form_page.dart` | Formulario de experiencia | Sí | No | OK |
| `SchedulesPage` | `features/catalogs/schedules/presentation/pages/schedules_page.dart` | CRUD de horarios | Sí (SQLite local) | No | OK |
| `ScheduleDetailPage` | `features/catalogs/schedules/presentation/pages/schedule_detail_page.dart` | Detalle de horario | Sí | No | OK |
| `ScheduleFormPage` | `features/catalogs/schedules/presentation/pages/schedule_form_page.dart` | Formulario de horario | Sí | No | OK |
| `ReservationRulesPage` | `features/catalogs/reservation_rules/presentation/pages/reservation_rules_page.dart` | Reglas de reserva | Sí (SQLite) | No | OK |
| `EmergencyContactsPage` | `features/catalogs/emergency_contacts/presentation/pages/emergency_contacts_page.dart` | Contactos de emergencia | Sí (SQLite) | No | OK |
| `VoiceScreen` | `app/voice/voice_screen.dart` | Interfaz de voz (sin NLP real) | No | Sí | Visual/prototipo |
| `DevWidgetCatalogScreen` | `playground/design_system_playground.dart` | Catálogo de widgets en modo dev | No | Sí | Playground |

**El módulo de reservas (`features/reservations/`) está conectado al backend real** con API client, DTOs, mappers, repositorio, y cache SQLite. Lee `GET /api/v1/reservations` y `GET /api/v1/reservations/{id}` (que ahora incluye `participants[]` y `payment_proofs[]`). Las subrutas Participantes y Pagos muestran datos reales con:
- Participantes: métricas (registrados/pendientes), alertas médicas/alimentarias con scroll-to-highlight, cards tappables → vista detalle full-screen con info personal, salud, contacto emergencia, consentimientos
- Pagos: estado del pago, comprobantes con fecha en subtitle, card tappable → visor con zoom para imágenes, cache en memoria. **Admin puede aprobar/rechazar (con motivo obligatorio) y deshacer verificación/rechazo.** Botones por cada comprobante según su estado (received→[Aprobar/Rechazar], verified→[Deshacer], rejected→[Deshacer rechazo]). Confirmación explícita antes de cada acción. Pull-to-refresh en el tab de pagos.
- Resumen: bloqueos operativos computados (pago no verificado, faltan participantes, formularios incompletos, asignaciones pendientes)
- Roles: el guía no ve comprobantes ni botones de acción. El backend bloquea por permisos en dos capas (router + servicio).

Confirmar reserva: implementado desde la app (admin-only, online-only, con validación de pago y disponibilidad). Cancelar reserva: pendiente.

**No existen pantallas de listado de equinos, detalle de equinos, ni CRUD de equinos real. El módulo `features/equines/` es UI mock básica.**

## 7. Estado del diseño visual y tema

| Elemento | Existe | Archivo | Observación |
|---|---|---|---|
| Tema claro | Sí | `app/theme/app_theme.dart` | `AppTheme.light()` — ThemeData completo |
| Tema oscuro | Sí | `app/theme/app_theme.dart` | `AppTheme.dark()` — ThemeData completo |
| ColorScheme | Sí | `app/theme/app_colors.dart` | `AppColors.lightColorScheme` y `darkColorScheme` |
| Tipografía primaria | Sí | Manrope (700-800) | En `assets/fonts/Manrope-Regular.ttf` |
| Tipografía secundaria | Sí | Inter (400-800) | En `assets/fonts/Inter-Regular.ttf` |
| Tokens visuales | Sí | `app/theme/theme_extensions.dart` | `AppThemeTokens` con radii y spacing |
| Radii | Sí | `app/theme/app_radii.dart` | `AppRadii` class |
| Cambio de tema animado | Sí | `app/theme/app_theme_notifier.dart` | Transición con cortina |
| Logo SVG | Sí | `assets/branding/lajuana.svg` | Se usa en AppTopBar |
| Logo PNG | Sí | `assets/branding/lajuana.png` | No se usa en código |
| Splash logo | Sí | `assets/branding/splash_logo.png` | Para native splash |
| App icon SVG/PNG | Sí | `assets/branding/app_icon.svg` y `.png` | |
| Iconos | Sí | Material Icons vía `Icons.*` | Sin iconos personalizados |
| Configuración icons | Sí | `flutter_launcher_icons.yaml` | |
| Configuración splash | Sí | `flutter_native_splash.yaml` | |
| Consistencia visual | Alta | — | Sistema de diseño coherente |

**El diseño visual está notablemente trabajado y puede soportar pantallas administrativas densas.** Los widgets ya cubren cards, listas, métricas, badges, banners, timelines, formularios, y navegación. El sistema de tema es completo y bien estructurado.

## 8. Estado de integración con backend

| Componente | Existe | Archivo | Endpoint relacionado | Estado |
|---|---|---|---|---|
| HTTP client genérico | No | — | — | No existe un cliente HTTP central/reutilizable |
| `http` package | Sí | Usado en `auth_api_client.dart` y `catalogs_sync_api.dart` | — | Clientes independientes cada uno |
| Dio | No | — | — | No se usa |
| Auth API Client | Sí | `auth/infrastructure/remote/auth_api_client.dart` | `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`, `/auth/register`, `/auth/change-password`, `/config/emergency-contacts` | Completo |
| Auth Token management | Sí | `auth/infrastructure/token_storage.dart` | — | Con SQLite storage |
| Refresh token | Sí | `auth_api_client.dart` + `auth_repository_impl.dart` | `/auth/refresh` | Retry automático en 401 |
| Manejo de errores API | Sí | `auth_api_client.dart` → `ApiErrorDto` | — | Parse `code` + `message` del body |
| Catalogs Sync API | Sí | `catalogs/data/catalogs_sync_api.dart` | `/sync/bootstrap`, `/sync/pull`, `/sync/push` | Completo con retry auth |
| Reservations API Client | **Sí** | `reservations/infrastructure/remote/reservations_api_client.dart` | `/api/v1/reservations` + `/payment-proofs/{id}/download` | **Creado con descarga de archivos** |
| Participants API Client | **No** (se resuelve inline) | — | Los participantes se resuelven dentro del detalle de reserva en backend, no se llama a `/participants` individualmente | **No existe, no necesario** |
| Equines API Client | **No** | — | `/api/v1/equines` | **No existe** |
| Assignments API Client | **No** | — | `/api/v1/assignments` | **No existe** |
| Payment Proofs download | **Sí** (dentro de `ReservationsApiClient`) | `reservations/infrastructure/remote/reservations_api_client.dart` | `GET /payment-proofs/{id}/download` | **Streaming de archivos** |
| Logs API Client | **No** | — | `/api/v1/logs` | **No existe** |
| Saddles API Client | **No** | — | `/api/v1/saddles` | **No existe** |
| Providers API Client | **No** | — | `/api/v1/providers` | **No existe** |
| Base URL | Sí | `app/api_base_url.dart` | — | Resuelve por plataforma |
| DTOs para reservas | **Sí** | `reservations/infrastructure/remote/reservation_dtos.dart` | `ReservationListItemDto`, `ReservationDetailDto`, `ReservationParticipantDto`, `ReservationPaymentProofDto`, `EmergencyContactDto` | **Creados (v2 con nested DTOs)** |
| DTOs para equinos | **No** | — | — | **No existen** |
| DTOs para participantes | **No separado** | — | Se resuelven dentro del detalle de reserva | **No existen como API independiente** |
| Mappers para reservas | **Sí** | `reservations/infrastructure/mappers/reservation_mapper.dart` | DTO ↔ Domain ↔ ViewModel (+ mapping de participantes y proofs) | **Creados (v2)** |

**La app consume estos endpoints del backend:**
- `POST /auth/login` — login
- `POST /auth/refresh?refresh_token=...` — refresh
- `POST /auth/logout` — logout (con bearer)
- `GET /auth/me` — perfil (con bearer)
- `POST /auth/register` — registro
- `POST /auth/change-password` — cambio de contraseña
- `GET /config/emergency-contacts` — contactos de emergencia
- `GET /sync/bootstrap` — bootstrap de catálogos
- `POST /sync/pull` — pull de cambios
- `POST /sync/push` — push de cambios
- `GET /api/v1/reservations` — listado de reservas (con datos de experiencia/schedule resueltos en batch)
- `GET /api/v1/reservations/{id}` — detalle de reserva (v2: incluye `participants[]` y `payment_proofs[]`)
- `GET /api/v1/payment-proofs/{id}/download` — descarga de comprobantes por streaming (desde el visor de pagos)
- `POST /api/v1/payment-proofs/{id}/approve` — aprobar comprobante (admin, retorna detalle completo de reserva)
- `POST /api/v1/payment-proofs/{id}/reject` — rechazar comprobante con motivo obligatorio (admin)
- `POST /api/v1/payment-proofs/{id}/unverify` — deshacer verificación (admin, retorna detalle completo)
- `POST /api/v1/payment-proofs/{id}/unreject` — deshacer rechazo (admin, retorna detalle completo)
- `POST /api/v1/reservations/{id}/confirm` — confirmar reserva (admin, retorna detalle completo con form_url generado)

**No se encontró integración real con estos endpoints:** `/api/v1/participants`, `/api/v1/equines`, `/api/v1/assignments`, `/api/v1/logs`, `/api/v1/saddles`, `/api/v1/providers`, `/api/v1/policies`.

## 9. Estado de persistencia local/offline-first

| Capacidad offline | Existe | Archivo/dependencia | Estado | Observación |
|---|---|---|---|---|
| SQLite para sesión | Sí | `sqflite` + `auth_database.dart` | Completo | Tablas: `session_local`, `user_local` |
| SQLite para catálogos | Sí | `sqflite` + `catalogs_database.dart` | Completo | Tablas: `experiences_local`, `schedules_local`, `reservation_rules_local`, `emergency_contacts_local`, `sync_queue`, `id_map`, `sync_cursors` |
| SQLite para reservas | **Sí** | `reservations/infrastructure/local/reservations_database.dart` | **Cache network-first** | Tablas: `reservations_list_cache`, `reservation_detail_cache` |
| Cola de operaciones offline | Sí | `catalogs_repository.dart` → `sync_queue` | Para catálogos | Opera sobre experiences/schedules |
| Sincronización bidireccional | Sí | `catalogs_sync_api.dart` + `catalogs_repository.dart` | Solo catálogos | Usa `/sync/bootstrap`, `/sync/pull`, `/sync/push` |
| Capacidad offline-first para reservas | **Parcial** | `ReservationsRepositoryImpl` | **Cache network-first** (lectura offline, sin escritura offline) | Lee de API, guarda en SQLite, usa cache como fallback si no hay red |
| SharedPreferences | **No** | — | No está en pubspec | No se usa |
| secure_storage | **No** | — | No está en pubspec | No se usa |
| Hive/Drift | **No** | — | No están en pubspec | No se usan |

**Las reservas ya cumplen parcialmente el enfoque offline-first:** cache network-first con SQLite para listado y detalle (lectura offline). Faltan escritura offline con cola de sync, sincronización bidireccional y pull-to-refresh. El resto de módulos (dashboard, equinos, participantes, proveedores) siguen sin persistencia local ni cliente HTTP.

## 10. Manejo de estado

| Patrón/librería | Existe | Dónde se usa | Observación |
|---|---|---|---|
| `ChangeNotifier` | Sí | `AuthController`, `ShellNavigationController`, `DashboardController`, `ReservationsController`, `ReservationsListController`, `EquinesController`, `ParticipantsController`, etc. | Patrón consistente en toda la app |
| `AnimatedBuilder` | Sí | Todos los widgets que escuchan controllers | Patrón reactivo sin Provider/Riverpod |
| `setState` | Sí | Widgets locales con estado interno | `VoiceScreen`, `DevWidgetCatalogScreen`, etc. |
| Provider | No | — | No se usa |
| Riverpod | No | — | No se usa |
| Bloc/Cubit | No | — | No se usa |
| GetX | No | — | No se usa |
| InheritedWidget | Sí | `AppThemeNotifier` | Solo para toggle de tema |

**El patrón actual (`ChangeNotifier` + `AnimatedBuilder`) es simple y funcional.** Puede aguantar módulos como reservas con listado, filtros, detalle, y estados loading/error/empty. Sin embargo, para un módulo de reservas completo con cache local, cola offline, sincronización y retry, se recomendaría al menos un patrón de repositorio + controlador (que ya existe en auth y catálogos). Los controladores actuales de reservas (`ReservationsController`, `ReservationsListController`) son mínimos y solo manejan filtro y subruta.

## 11. Dependencias actuales

| Dependencia | Versión | Uso aparente | Usada en código | Observación |
|---|---|---|---|---|
| `flutter` | SDK | — | Sí | Core |
| `cupertino_icons` | ^1.0.8 | Iconos iOS | No | Instalada pero no usada |
| `flutter_svg` | ^2.0.10+1 | SVG (logo) | Sí | `AppTopBar` |
| `auto_size_text` | ^3.0.0 | Texto autoescalable | Sí | `AppSegmentedFilter` |
| `http` | ^1.2.2 | Cliente HTTP | Sí | `AuthApiClient`, `CatalogsSyncApi` |
| `sqflite` | ^2.3.3+1 | SQLite local | Sí | Auth + catálogos |
| `sqflite_common_ffi_web` | ^1.0.0 | SQLite web | Sí | Auth + catálogos |
| `path` | ^1.9.0 | Rutas de archivos | Sí | Bases de datos |
| `connectivity_plus` | ^6.0.5 | Detectar conectividad | Sí | `ConnectivityPlusService` |
| `device_info_plus` | ^11.2.0 | Info dispositivo | Sí | `api_base_url.dart` |
| `url_launcher` | ^6.3.1 | Abrir URLs/teléfono | Sí | `MoreFlowScreen` |

**Dependencias instaladas y no usadas:** `cupertino_icons`.

## 12. Estado frente al módulo de reservas

| Capacidad necesaria | Estado actual | Qué falta |
|---|---|---|---|
| Shell reutilizable | ✅ Implementado | Nada |
| Navegación a módulo reservas | ✅ Implementado | Ya hay tab `AppNavItem.reservas` |
| Widgets para cards/listas | ✅ Implementado | `ReservationRowCard`, `AppEntityRowCard`, `PaymentStatusCard` listos |
| Filtros/segmentos | ✅ Implementado | `AppSegmentedFilter` listo |
| Timeline | ✅ Implementado | `AppTimeline` listo |
| Cliente HTTP | ✅ **Implementado** | `ReservationsApiClient` creado con auth y refresh |
| Auth/token | ✅ Implementado | Reutiliza `TokenStorage` y refresh |
| DTOs/mappers | ✅ **Implementado** | `ReservationListItemDto`, `ReservationDetailDto`, mapper DTO↔Domain↔ViewModel |
| Repository pattern | ✅ **Implementado** | `ReservationsRepositoryImpl` con cache local |
| Estado de pantalla | ✅ **Implementado** | Controllers manejan estados loading/success/error/empty/offline |
| Cache local SQLite | ✅ **Implementado** | `ReservationsDatabase` con tablas `reservations_list_cache` y `reservation_detail_cache` (incluye participantes y proofs) |
| Manejo de errores API | ✅ **Implementado** | `ReservationsApiException` con parse de error del backend |
| Pull-to-refresh | ✅ Implementado | `RefreshIndicator` en `ReservationsModuleScreen` |
| Estados vacío/error/loading | ✅ Implementado | `AppCenteredLoader`, `AppStatusBanner`, banners de error/offline |
| Participantes en detalle | ✅ **Implementado (lectura)** | `ReservationParticipantsSectionController` recibe datos del detail, muestra métricas, alertas con scroll-to-highlight, cards tappables → vista full-screen |
| Comprobantes en detalle | ✅ **Implementado (lectura + streaming)** | `ReservationPaymentProofsSectionController` recibe datos del detail, muestra proofs con fecha, card tappable → visor con descarga por streaming + cache en memoria |
| Bloqueos operativos | ✅ **Implementado** | Computados en el resumen: pago no verificado, faltan participantes, forms incompletos, asignaciones pendientes |
| Tests de reservas | ✅ **Implementados** | 28 tests Flutter (DTO, mapper, controller, payment actions) + 23 tests backend (endpoints, permisos, auditoría, download) |
| Aprobación/rechazo de comprobantes | ✅ **Implementado** | Admin aprueba/rechaza desde el detalle de reserva. Confirmación explícita. Motivo obligatorio en rechazo. |
| Deshacer verificación/rechazo | ✅ **Implementado** | `verified` → `received` vía `unverify`, `rejected` → `received` vía `unreject`. Admin-only. |
| Auditoría de comprobantes | ✅ **Implementado** | `ReservationAuditLogDocument` creado en cada approve/reject/unverify/unreject |
| Pull-to-refresh en pagos | ✅ **Implementado** | Tab de pagos con `RefreshIndicator` + `ListView` |
| Visor con descarga | ✅ **Implementado** | Botón de descarga en visor de comprobantes con `file_saver.dart` (web + nativo) |
| Protección por roles en UI | ✅ **Implementado** | `AuthController` pasado al detalle; guía no ve comprobantes ni acciones |
| Confirmar reserva | ✅ **Implementado** | Admin confirma desde el detalle con revalidación de disponibilidad, descuento atómico de cupos, auditoría y formulario generado. SnackBar feedback, doble-tap bloqueado. |

**Conclusión: "Confirmar reserva completado; deuda controlada"**

El detalle de reserva ahora incluye participantes, comprobantes, acciones financieras y confirmación para admin. Cache local preserva todos los campos. Tests cubren el pipeline completo backend+frontend. La deuda principal es cancelar reserva y la cola offline para escritura.

## 13. Riesgos técnicos actuales

| Riesgo | Evidencia | Impacto | Recomendación |
|---|---|---|---|---|
| Sin cliente HTTP para reservas | ~~No existe~~ **(Resuelto)** | ✅ Ya existe `ReservationsApiClient` conectado al backend | N/A |
| Sin DTOs ni mappers para reservas | ~~No existen~~ **(Resuelto)** | ✅ Ya existe DTOs y mapper DTO↔Domain↔ViewModel | N/A |
| Sin persistencia local para reservas | ~~No hay~~ **(Resuelto)** | ✅ Ya existe `ReservationsDatabase` con cache SQLite | N/A |
| Dashboard, equinos y participantes mockeados | `EquineDemoRecord`, `ReservationPresentationFixtures` | Esos módulos no pueden operar con datos reales | Conectar a backend progresivamente (reservas ya resuelto) |
| Paquetes compartidos vacíos | `packages/mobile_ui`, `mobile_core`, `mobile_domain`, `mobile_mocks` solo tienen `.gitkeep` | No hay modelos de dominio compartidos entre frontend y backend | Poblarlos (especialmente `mobile_domain`) |
| Navegación no centralizada | `Navigator.of(context).push(...)` directo en lugar de rutas nombradas | Dificulta deep linking, testing y trazabilidad | Migrar a `go_router` o al menos usar rutas nombradas |
| Payload de detalle de reserva incrementado | GET /reservations/{id} ahora incluye arrays de participantes y proofs | Reservas con 20+ participantes podrían tener payloads >50KB | Monitorear; umbral típico ~2-10KB |
| `http` usado directamente sin interfaz | `AuthApiClient` y `CatalogsSyncApi` crean `http.Client` propio | Difícil mockear en tests, sin interceptores centralizados | Usar inyección de dependencias con interfaz |
| `cupertino_icons` instalada y no usada | `pubspec.yaml` la incluye, 0 imports en código | Dependencia muerta | Removerla |
| Router placeholder abandonado | `app/router.dart` con solo comentario | Sugiere migración a Navigator 2.0 pendiente | Decidir si migrar o limpiar |

## 14. Brechas contra arquitectura objetivo

| Principio objetivo | Estado actual | Brecha |
|---|---|---|
| **Flutter mobile-first** | ✅ Cumplido | App Flutter con diseño mobile-first |
| **Operación offline-first** | ⚠️ Parcial | Auth, catálogos y **reservas** tienen persistencia; faltan escritura offline y sync bidireccional para reservas |
| **SQLite/persistencia local** | ⚠️ Parcial | SQLite existe para auth, catálogos y **reservas**; faltan dashboard, equinos, participantes |
| **Backend FastAPI como fuente de validación** | ⚠️ Parcial | Auth y **reservas** validan contra backend; equinos, participantes, dashboard no |
| **Reserva como entidad central** | ⚠️ **Parcialmente cumplido** | Reserva tiene modelo de dominio, repositorio, API client y cache local. Faltan endpoints de escritura (confirmar, cancelar, registrar pago) |
| **Trazabilidad** | ❌ No implementado | No hay logs de operaciones ni auditoría en la app |
| **Permisos** | ⚠️ Parcial | Auth tiene roles y sesión local, pero no hay chequeo de permisos por acción |
| **Acciones críticas verificadas contra backend** | ✅ **Parcial** | Approve/reject/unverify/unreject verificados contra backend. Faltan confirmar y cancelar reserva. |

## 15. Recomendación previa al módulo de reservas

### Qué se puede reutilizar
- `AuthenticatedShell` con navegación por tabs (ya incluye tab de reservas)
- `AppBottomNav`, `AppTopBar`, `AppScaffold` (componentes de shell)
- Widgets: `AppEntityRowCard`, `AppBadge`, `AppButton`, `AppSegmentedFilter`, `AppTimeline`, `AppStatusBanner`, `AppCenteredLoader`, `AppSectionHeader`, `AppMetricCard`
- `ModuleSubrouteHeader` para subpestañas dentro del módulo
- `AuthController` y `TokenStorage` para autenticación
- `ShellNavigationController` para navegación entre módulos
- Catálogos ya tienen datos de experiencias y horarios que las reservas consumirán

### Qué se creó (cambios desde la versión anterior del doc)
1. ✅ **`ReservationsApiClient`** — cliente HTTP para endpoints de reservas con auth y refresh
2. ✅ **DTOs de reservas** — `ReservationListItemDto`, `ReservationDetailDto`
3. ✅ **Mappers** — DTO ↔ Domain ↔ ViewModel
4. ✅ **Base de datos SQLite local para reservas** — `ReservationsDatabase` con tablas `reservations_list_cache` y `reservation_detail_cache`
5. ✅ **Repositorio de reservas** — `ReservationsRepositoryImpl` con cache network-first
6. ✅ **Conexión de `ReservationsModuleScreen` al repositorio** — ya no usa fixtures
7. ✅ **Estados loading/error/empty/offline** en pantallas de reservas
8. ✅ **Pull-to-refresh** en listado de reservas
9. ✅ **`formatDate()`** en `mobile_core` — normalización de fechas a formato "20 de mayo de 2026"
10. ✅ **Backend enriquecido** — `GET /reservations/{id}` ahora incluye `participants[]` y `payment_proofs[]` resueltos por `$in` query
11. ✅ **DTOs nested** — `ReservationParticipantDto`, `ReservationPaymentProofDto`, `EmergencyContactDto`
12. ✅ **Modelos de dominio extendidos** — `ReservationParticipantDetail` (19 campos), `ReservationPaymentProofDetail` (9 campos)
13. ✅ **Participantes tab real** — métricas (registrados/pendientes), alertas con scroll-to-highlight, cards tappables → vista detalle full-screen
14. ✅ **Pagos tab real** — comprobantes con fecha, card tappable → visor con streaming + zoom + cache en memoria
15. ✅ **Bloqueos operativos** — computados en resumen: pago, participantes, formularios, asignaciones
16. ✅ **Cache extendida** — SQLite preserva participantes y payment_proofs en el payload del detalle
17. ✅ **Download streaming** — `ReservationsApiClient.downloadPaymentProofFile()` + en repositorio
18. ✅ **AppEntityRowCard con animación** — convertido a `StatefulWidget` con `AnimatedContainer` para transición suave del estado selected
19. ✅ **Tests de reservas** — 28 tests Flutter + 23 backend (DTO, mapper, controller, payment actions, permisos, auditoría, download)
20. ✅ **Approve/reject/unverify/unreject de comprobantes** — admin-only, con confirmación explícita, motivo obligatorio en rechazo, auditoría
21. ✅ **ReservationAuditLogDocument** — colección de auditoría para cada acción financiera
22. ✅ **file_data en PaymentProofDocument** — almacenamiento de bytes en MongoDB (sin archivos en disco)
23. ✅ **WhatsApp downloader → file_data** — descarga de media WhatsApp guarda en documento, no en storage adapter
24. ✅ **seed_proof_file_data.py** — migración de proofs sintéticos a file_data
25. ✅ **file_saver.dart** — conditional imports para descarga de archivos (web + nativo)
26. ✅ **AppConfirmDialog** — diálogo de confirmación reutilizable con estilo danger
27. ✅ **Pull-to-refresh en pagos** — RefreshIndicator + ListView en payment section
28. ✅ **AuthController en detalle** — role-based UI (admin ve acciones, guía no ve comprobantes)
29. ✅ **Decimal128 fix** — field_validator en ReservationDocument para MongoDB Decimal128
30. ✅ **Documentación** — `docs/mobile/payment-proof-actions-contract.md`
31. ✅ **Confirmar reserva (Flutter)** — API client (`confirmReservation`), repository interface + impl, controller con `ReservationActionState` (confirming/success/error + double-tap guard), botón condicional en detalle, confirmación con modal informativo, SnackBar feedback (no inline en DOM)
32. ✅ **Backend: auditoría en confirm** — `ReservationAuditLogDocument` con acción `reservation.confirmed` + `previous_status` capturado antes de la transición
33. ✅ **Backend: fix `$ne` type mismatch** — `exclude_reservation_id` convertido a `PydanticObjectId` en `list_active_reservations_for_date` para que MongoDB excluya correctamente la reserva actual del chequeo de disponibilidad
34. ✅ **Backend: fix `datetime.time` encoding** — `_save_schedule_status()` helper que usa motor collection `update_one` en producción (evita el encoder de Beanie que falla con `start_time: time`) y cae a `.save()` en tests
35. ✅ **Documentación** — `docs/mobile/reservation-confirmation-contract.md`

### Qué falta aún
1. ✅ **Confirmar reserva** — completado en este microplan
2. **Cancelar reserva** — endpoint + UI
3. **Cola de operaciones offline (sync queue)** — para escritura sin conexión
4. **Desmockear Dashboard** — conectar a backend real
5. **Desmockear Equinos** — conectar a backend real
6. **Desmockear Participantes** — conectar a backend real

### Qué no se debe tocar
- El sistema de diseño y widgets (están bien y son reutilizables)
- El shell autenticado y navegación por tabs
- El módulo auth (funciona correctamente)
- El módulo de catálogos (es el ejemplo a seguir)

### Deuda aceptable temporalmente
- Falta de tests para módulos operacionales (se pueden agregar después)
- Navegación con `Navigator.push` directo sin rutas nombradas
- Paquetes compartidos vacíos (`mobile_domain`, `mobile_ui`, `mobile_mocks`)
- Falta de escritura offline con cola de sync para reservas

## 16. Inventario final de archivos relevantes

| Archivo | Rol | Relevancia para reservas |
|---|---|---|
| `lib/main.dart` | Entry point | Alta (punto de entrada) |
| `lib/app/app.dart` | MaterialApp + DI | Alta (aquí se inyectarán dependencias) |
| `lib/app/api_base_url.dart` | Resolución de URL | Alta (necesario para API client) |
| `lib/app/navigation/app_router.dart` | Constantes de rutas | Baja (las reservas usarán push directo inicialmente) |
| `lib/app/navigation/route_names.dart` | Nombres de ruta | Media (agregar rutas de reservas) |
| `lib/app/navigation/shell_navigation_controller.dart` | Control de tabs | Alta (ya hay tab reservas) |
| `lib/app/shell/authenticated_shell.dart` | Shell principal | Alta (ya incluye `ReservationsModuleScreen`) |
| `lib/app/theme/` | Sistema de diseño | Alta (reutilizable) |
| `lib/app/widgets/` | Widgets reutilizables | Alta (usar en pantallas de reservas) |
| `lib/app/bootstrap/startup_gate.dart` | Bootstrap | Media (referencia de patrón) |
| `lib/features/auth/` | Auth completo | Alta (provee token y sesión) |
| `lib/features/auth/infrastructure/remote/auth_api_client.dart` | Cliente HTTP auth | Alta (patrón a replicar) |
| `lib/features/auth/infrastructure/local/auth_database.dart` | SQLite auth | Alta (referencia) |
| `lib/features/auth/infrastructure/token_storage.dart` | Token storage | Alta (reutilizable) |
| `lib/features/catalogs/data/catalogs_repository.dart` | Repositorio con sync offline | **Máxima** (patrón a replicar) |
| `lib/features/catalogs/data/catalogs_sync_api.dart` | API sync de catálogos | Alta (patrón a replicar) |
| `lib/features/catalogs/data/catalogs_database.dart` | SQLite catálogos | Alta (referencia para BD de reservas) |
| `lib/features/reservations/reservations_module.dart` | Factory con DI | **Máxima** (crea repo real con API client + SQLite) |
| `lib/features/reservations/domain/models/reservation_participant_detail.dart` | Modelo detalle de participante (19 campos, con alerts) | **Nuevo (v2)** |
| `lib/features/reservations/domain/models/reservation_payment_proof_detail.dart` | Modelo detalle de comprobante (9 campos) | **Nuevo (v2)** |
| `lib/features/reservations/domain/models/` | Modelos de dominio | **Máxima** (9 modelos: list item, detail, status, payment, timeline, alerts, participant_detail, proof_detail) |
| `lib/features/reservations/domain/repositories/reservations_repository.dart` | Interfaz del repositorio | **Máxima** |
| `lib/features/reservations/infrastructure/remote/reservations_api_client.dart` | API client real | **Máxima** (conecta con backend, auth, refresh) |
| `lib/features/reservations/infrastructure/remote/reservation_dtos.dart` | DTOs reales | **Máxima** (ListItemDto, DetailDto) |
| `lib/features/reservations/infrastructure/local/reservations_database.dart` | SQLite cache | **Máxima** (cache network-first) |
| `lib/features/reservations/infrastructure/local/reservations_local_data_source.dart` | Data source local | **Máxima** (lectura/escritura cache) |
| `lib/features/reservations/infrastructure/mappers/reservation_mapper.dart` | Mapper DTO↔Domain↔ViewModel | **Máxima** |
| `lib/features/reservations/infrastructure/repositories/reservations_repository_impl.dart` | Repositorio real con cache | **Máxima** (sin N+1) |
| `lib/features/reservations/presentation/screens/reservations_module_screen.dart` | Listado de reservas | **Máxima** (conectado) |
| `lib/features/reservations/presentation/screens/reservation_detail_shell_screen.dart` | Detalle de reserva | **Máxima** (conectado) |
| `lib/features/reservations/presentation/controllers/reservations_controller.dart` | Controlador de subrutas | Media |
| `lib/features/reservations/presentation/controllers/reservations_list_controller.dart` | Controlador de listado | **Alta** (filtro local, cache, estados) |
| `lib/features/reservations/presentation/controllers/reservation_detail_controller.dart` | Controlador de detalle | **Alta** (carga, cache offline) |
| `lib/features/reservations/presentation/models/reservation_view_models.dart` | ViewModels reales | **Alta** (ya no son fixtures) |
| `lib/features/reservations/presentation/widgets/reservation_row_card.dart` | Card de fila de reserva | Alta |
| `lib/features/reservations/presentation/widgets/payment_status_card.dart` | Card de estado de pago | Alta (colores sólidos del badge) |
| `lib/features/reservations/presentation/controllers/reservation_assignments_section_controller.dart` | Controlador de asignaciones | Baja (placeholder) |
| `lib/features/reservations/presentation/controllers/reservation_logs_section_controller.dart` | Controlador de bitácora | Baja (placeholder) |
| `lib/features/reservations/presentation/controllers/reservation_participants_section_controller.dart` | Controlador de participantes | **Media** (ahora poblado con datos reales: participants, totals, alerts) |
| `lib/features/reservations/presentation/controllers/reservation_payment_proofs_section_controller.dart` | Controlador de comprobantes | **Media** (ahora poblado con datos reales: proofs, paymentStatus) |
| `lib/features/dashboard/presentation/screens/dashboard_screen.dart` | Dashboard (usa fixtures) | Media (conectar a datos reales después) |
| `lib/features/equines/presentation/screens/equines_module_screen.dart` | Equinos mock | Baja (módulo aparte) |
| `lib/features/participants/presentation/screens/participants_module_screen.dart` | Participantes mock | Media (comparte datos con reservas) |
| `lib/features/providers/presentation/screens/providers_module_screen.dart` | Proveedores placeholder | Baja |
| `playground/design_system_playground.dart` | Catálogo de widgets | Baja (solo dev) |
| `pubspec.yaml` | Dependencias | Media (agregar dependencias si es necesario) |
| `assets/branding/lajuana.svg` | Logo | Baja |
| `packages/mobile_ui/` | Vacío | Media (poblarlo con UI compartida) |
| `packages/mobile_domain/` | Vacío | **Alta** (modelos de dominio compartidos) |
| `packages/mobile_core/` | `date_utils.dart` — `formatDate()` | **Media** (normalización de fechas reutilizable) |
| `packages/mobile_mocks/` | Vacío | Media (fixtures compartidos) |

## 17. Anexos

### 17.1 Widgets detectados pero no usados

| Widget | Archivo | ¿Usado en producción? |
|---|---|---|
| `AppBreadcrumb` | `app/widgets/app_breadcrumb.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppTermHelp` | `app/widgets/app_term_help.dart` | No se encontró uso real |
| `AppSelectableCard` | `app/widgets/cards/app_selectable_card.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppImageFeatureCard` | `app/widgets/cards/app_image_feature_card.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppStatsCard` | `app/widgets/cards/app_stats_card.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppExperienceCard` | `app/widgets/cards/app_experience_card.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppAssignmentCard` | `app/widgets/cards/app_assignment_card.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppCenteredBadgeCard` | `app/widgets/cards/app_centered_badge_card.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppPricingTiersTable` | `app/widgets/cards/app_pricing_tiers_table.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppLogbookTimeline` | `app/widgets/cards/app_logbook_timeline.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppTimelineMetrics` | `app/widgets/app_timeline.dart` | Solo en `DevWidgetCatalogScreen` |
| `AppVoiceFab` | `app/widgets/app_voice_fab.dart` | Solo en `DevWidgetCatalogScreen` y `VoiceScreen` |
| `ShellPageSlot` | `app/shell/widgets/shell_page_slot.dart` | No se encontró uso real |

### 17.2 Pantallas mock/prototipo

| Pantalla | Archivo | Naturaleza |
|---|---|---|
| `DevWidgetCatalogScreen` | `playground/design_system_playground.dart` | Playground dev, 767 líneas, muestra todos los widgets |
| `DashboardScreen` | `features/dashboard/presentation/screens/dashboard_screen.dart` | Datos de `ReservationPresentationFixtures` |
| `EquinesModuleScreen` | `features/equines/presentation/screens/equines_module_screen.dart` | `EquineDemoRecord` hardcodeado |
| `ParticipantsModuleScreen` | `features/participants/presentation/screens/participants_module_screen.dart` | Datos de `ReservationPresentationFixtures` |
| `ProvidersModuleScreen` | `features/providers/presentation/screens/providers_module_screen.dart` | Placeholder |
| `VoiceScreen` | `app/voice/voice_screen.dart` | UI de voz sin NLP real |

### 17.2b Pantallas conectadas a backend (nuevas desde doc anterior)

| Pantalla | Archivo | Naturaleza |
|---|---|---|
| `ReservationsModuleScreen` | `features/reservations/presentation/screens/reservations_module_screen.dart` | **Conectado a `GET /api/v1/reservations`** |
| `ReservationDetailShellScreen` | `features/reservations/presentation/screens/reservation_detail_shell_screen.dart` | **Conectado a `GET /api/v1/reservations/{id}` (v2: con participantes y proofs)** |
| `_ParticipantDetailView` | (inline en `reservation_detail_shell_screen.dart`) | **Full-screen detail view de participante** |
| `_ProofImageViewer` | (inline en `reservation_detail_shell_screen.dart`) | **Visor de comprobantes con streaming** |

### 17.3 Dependencias instaladas pero no usadas

| Dependencia | Versión | Evidencia |
|---|---|---|
| `cupertino_icons` | ^1.0.8 | 0 imports en `lib/` y `test/` |

### 17.4 Endpoints backend disponibles pero no consumidos por la app

| Endpoint | Archivo backend | Consumido por la app |
|---|---|---|---|
| `GET /reservations` | `endpoints/reservations.py` | ✅ **Sí** (listado con datos batch) |
| `GET /reservations/{id}` | `endpoints/reservations.py` | ✅ **Sí** (detalle) |
| `POST /reservations` | `endpoints/reservations.py` | ❌ No (pendiente) |
| `PATCH /reservations/{id}` | `endpoints/reservations.py` | ❌ No (pendiente) |
| `POST /reservations/{id}/confirm` | `endpoints/reservations.py` | ❌ No (pendiente) |
| `POST /reservations/{id}/transition` | `endpoints/reservations.py` | ❌ No (pendiente) |
| `POST /reservations/{id}/cancel` | `endpoints/reservations.py` | ❌ No (pendiente) |
| `POST /reservations/{id}/payment-proofs` | `endpoints/reservations.py` | ❌ No (pendiente) |
| `GET /reservations/check-availability` | `endpoints/reservations.py` | ❌ No (pendiente) |
| `GET /payment-proofs/{id}/download` | `endpoints/payment_proofs.py` | ✅ **Sí** (streaming de archivos desde Flutter) |
| `GET /participants/{id}` | `endpoints/participants.py` | ❌ No |
| `PATCH /participants/{id}` | `endpoints/participants.py` | ❌ No |
| `POST /equines` | `endpoints/equines.py` | ❌ No |
| `GET /equines` | `endpoints/equines.py` | ❌ No |
| `GET /equines/{id}` | `endpoints/equines.py` | ❌ No |
| `PATCH /equines/{id}` | `endpoints/equines.py` | ❌ No |
| `DELETE /equines/{id}` | `endpoints/equines.py` | ❌ No |
| `POST /assignments` | `endpoints/assignments.py` | ❌ No |
| `GET /assignments/{id}` | `endpoints/assignments.py` | ❌ No |
| `PATCH /assignments/{id}` | `endpoints/assignments.py` | ❌ No |
| `GET /payment-proofs/{id}` | `endpoints/payment_proofs.py` | ❌ No |
| `POST /payment-proofs/{id}/verify` | `endpoints/payment_proofs.py` | ❌ No |
| `POST /payment-proofs/{id}/approve` | `endpoints/payment_proofs.py` | ✅ **Sí** (admin) |
| `POST /payment-proofs/{id}/reject` | `endpoints/payment_proofs.py` | ✅ **Sí** (admin, con motivo) |
| `POST /payment-proofs/{id}/unverify` | `endpoints/payment_proofs.py` | ✅ **Sí** (admin, deshacer verificación) |
| `POST /payment-proofs/{id}/unreject` | `endpoints/payment_proofs.py` | ✅ **Sí** (admin, deshacer rechazo) |
| `POST /logs` | `endpoints/logs.py` | ❌ No |
| `GET /logs/{id}` | `endpoints/logs.py` | ❌ No |
| `PATCH /logs/{id}` | `endpoints/logs.py` | ❌ No |
| `POST /saddles` | `endpoints/saddles.py` | ❌ No |
| `GET /saddles` | `endpoints/saddles.py` | ❌ No |
| `GET /saddles/{id}` | `endpoints/saddles.py` | ❌ No |
| `PATCH /saddles/{id}` | `endpoints/saddles.py` | ❌ No |

---

*Documento generado el 2026-05-25. **Actualizado el 2026-05-26 (v3)** para reflejar el detalle de reserva v2: backend enriquecido con participants[] y payment_proofs[], DTOs nested, nuevos modelos de dominio, tab de participantes real con scroll-to-highlight y vista detalle, tab de pagos real con visor por streaming, bloqueos operativos en resumen, cache extendida, animación en AppEntityRowCard, y 20 tests nuevos. **Actualizado el 2026-05-26 (v4)** para reflejar acciones financieras: approve/reject/unverify/unreject de comprobantes, auditoría, file_data en MongoDB, disable de cuentas offline, botón de descarga en visor, pull-to-refresh, Decimal128 fix, y 51 tests totales. Auditoría directa del código fuente de `apps/mobile` y `apps/api`.*
