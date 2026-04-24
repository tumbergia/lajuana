# Arquitectura mobile

## Objetivo actual

Construir el frontend por flujo operativo real, no por pantallas sueltas.  
La reserva es la entidad central y el shell autenticado gobierna toda la operacion.

## Entrada de la app (topologia)

`main.dart` → `LaJuanaApp` → `StartupGate` (`app/bootstrap/startup_gate.dart`) → flujo no autenticado o `AuthenticatedShell` (`app/shell/authenticated_shell.dart`).  
No hay `HomePage` como centro operativo: cada tab monta su feature bajo demanda (Navigator anidado por tab visitado).

Autenticacion vive en `features/auth/`. Los banners globales de sesion/conectividad/sync se pintan en `ShellStatusRegion` bajo el `AppTopBar` del shell, no en cada modulo.

## Shell autenticado (base obligatoria)

Dentro del area autenticada, el shell aporta:

1. `AppTopBar` global (una sola barra superior en rutas internas; el detalle de reserva no duplica top bar).
2. `ShellStatusRegion` (banners transversales).
3. Slot de contenido: `Navigator` por tab primario, creado en el primer acceso y conservado con `Offstage` + `TickerMode`.
4. `AppBottomNav` para navegacion primaria.

Cada modulo bajo el shell usa donde aplique:

- `AppSectionHeader`
- `AppBreadcrumb` al inicio
- contenido de la subruta activa

Los modulos no repiten los banners globales ya mostrados por el shell.

## Niveles de orquestacion

### Nivel 1: app orchestration

Responsable de:

- sesion autenticada y proteccion de navegacion;
- conectividad;
- estados globales de sincronizacion;
- invalidacion/refresh de sesion;
- banners globales visibles (`ShellStatusRegion`).

### Nivel 2: module orchestration

Cada modulo principal mantiene su estado de subruta y carga local/remota:

- Dashboard operativo (`features/dashboard/presentation/screens/dashboard_screen.dart`)
- Reservas (`features/reservations/presentation/screens/reservations_module_screen.dart`)
- Equinos (`features/equines/presentation/screens/equines_module_screen.dart`)
- Participantes (`features/participants/presentation/screens/participants_module_screen.dart`)
- Mas / configuracion (`features/configuration/presentation/screens/more_flow_screen.dart`)
- Catalogos operativos (`features/catalogs/`) con persistencia local, cola offline y sync/push.

Implementacion base de controladores:

- `features/dashboard/presentation/controllers/dashboard_controller.dart`
- `features/reservations/presentation/controllers/reservations_controller.dart` (subrutas del modulo)
- `features/reservations/presentation/controllers/reservations_list_controller.dart` (lista / filtros / paginacion incremental)
- `features/equines/presentation/controllers/equines_controller.dart`
- `features/participants/presentation/controllers/participants_controller.dart`

### Nivel 3: view orchestration

Cada vista concreta solo maneja:

- rendering;
- eventos del usuario;
- estado efimero de UI (formularios, filtros, foco).

## Convencion de subrutas

No se redisenia ni reemplaza el widget existente.  
Se usa `AppBreadcrumb` como navegacion secundaria al inicio de cada modulo principal (o cabecera compuesta via `ModuleSubrouteHeader` en `features/shared`).

Ejemplos:

- Reservas: `Resumen / Participantes / Pagos / Asignaciones / Bitacora`
- Equinos: `Resumen / Historial / Disponibilidad / Cuidado`
- Participantes: `Resumen / Participantes / Historial`
- Dashboard: `Resumen / Pendientes / Salidas / Sync`

Para navegacion terciaria en reservas:

- `features/reservations/presentation/screens/reservation_detail_shell_screen.dart`
- mismo patron: `AppSectionHeader + AppBreadcrumb + contenido` (sin segundo `AppTopBar`)

## Convencion de estados globales visibles

Se muestran como componentes transversales reutilizables:

- sin conexion;
- conexion inestable;
- cambios pendientes de sync;
- sesion local con restricciones;
- sesion que requiere validacion remota.

## Prioridad de construccion

1. shell autenticado + convencion de subrutas + estado global visible;
2. dashboard operativo;
3. reservas (resumen y subrutas internas);
4. participantes, pagos, asignaciones y bitacora en flujo de reserva;
5. equinos;
6. proveedores y configuracion operativa;
7. endurecimiento de estados vacios/error/conflictos y optimizacion.

## Catalogos offline-first

- Escrituras de experiencias, fechas operativas y reglas de reserva via `sync/push`.
- Lectura y reconciliacion via `sync/bootstrap` + `sync/pull`.
- Cola local persistente con estados `pending`, `conflict`, `rejected`, `synced`.
- Acceso principal desde `Mas > Catalogos` y acceso rapido a fechas operativas desde Reservas.

## Reglas de composicion

- local-first para pintar rapido;
- refresh remoto en segundo plano cuando aplique;
- rutas no deben bloquear UI esperando red si ya existe data local;
- separar estados de vista: `isInitialLoading`, `isRefreshing`, `isSyncing`, `hasLocalData`;
- evitar metodos ambiguos tipo `load()` en controladores/repositorios de catalogos;
- preferir nombres explicitos: `loadLocalThenRefresh`, `refresh*FromServer`, `syncNow`;
- listas largas con carga incremental (`ListView.builder`, `loadMore` donde aplique);
- no mezclar reglas de negocio de feature en widgets globales;
- no mover widgets de feature al design system sin evidencia de reuso real;
- tabs del shell: inicializacion perezosa; no montar todos los modulos al arranque.
