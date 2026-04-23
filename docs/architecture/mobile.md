# Arquitectura mobile

## Objetivo actual

Construir el frontend por flujo operativo real, no por pantallas sueltas.  
La reserva es la entidad central y el shell autenticado gobierna toda la operacion.

## Shell autenticado (base obligatoria)

Toda vista principal debe correr dentro de una estructura comun:

1. `AppScaffold`
2. `AppTopBar`
3. `AppSectionHeader`
4. widget de subrutas existente (`AppBreadcrumb`) al inicio de la vista
5. banners globales de estado (conectividad, sync, sesion local)
6. contenido del modulo
7. `AppBottomNav` para navegacion primaria

## Niveles de orquestacion

### Nivel 1: app orchestration

Responsable de:

- sesion autenticada y proteccion de navegacion;
- conectividad;
- estados globales de sincronizacion;
- invalidacion/refresh de sesion;
- banners globales visibles.

### Nivel 2: module orchestration

Cada modulo principal mantiene su estado de subruta y carga local/remota:

- Dashboard operativo
- Reservas
- Equinos
- Participantes
- Mas (perfil/contactos)

Implementacion base actual:

- `features/dashboard/presentation/controllers/dashboard_controller.dart`
- `features/reservations/presentation/controllers/reservations_controller.dart`
- `features/equines/presentation/controllers/equines_controller.dart`
- `features/participants/presentation/controllers/participants_controller.dart`

### Nivel 3: view orchestration

Cada vista concreta solo maneja:

- rendering;
- eventos del usuario;
- estado efimero de UI (formularios, filtros, foco).

## Convencion de subrutas

No se redisenia ni reemplaza el widget existente.  
Se usa `AppBreadcrumb` como navegacion secundaria al inicio de cada modulo principal.

Ejemplos:

- Reservas: `Resumen / Participantes / Pagos / Asignaciones / Bitacora`
- Equinos: `Resumen / Historial / Disponibilidad / Cuidado`
- Participantes: `Resumen / Participantes / Historial`
- Dashboard: `Resumen / Pendientes / Salidas / Sync`

Para navegacion terciaria en reservas:

- `features/reservations/presentation/screens/reservation_detail_screen.dart`
- usa el mismo inicio de vista: `AppSectionHeader + AppBreadcrumb + contenido`

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

## Reglas de composicion

- local-first para pintar rapido;
- refresh remoto en segundo plano cuando aplique;
- listas largas con carga incremental;
- no mezclar reglas de negocio de feature en widgets globales;
- no mover widgets de feature al design system sin evidencia de reuso real.
