# Arquitectura API

## Estado actual

La API está en Fase 2, con foco en `Reservation` como agregado central y módulos operativos extendidos.

Incluye:

- autenticación JWT y autorización por permisos;
- roles `admin`, `guide`, `unassigned`;
- endpoints administrativos de usuarios;
- vertical de reservas (reserva, schedule, participante, pago, reglas de confirmación);
- módulos operativos: equinos, sillas, asignaciones, bitácora, proveedores y pólizas;
- contrato uniforme de errores para frontend y pruebas.

## Reglas clave

- Las validaciones de negocio viven en `services/`.
- Los routers no contienen lógica de confirmación/negocio crítico.
- La confirmación de reserva solo se ejecuta en backend.
- Los comprobantes guardan metadatos y referencia externa (`storage_key`), no binarios en MongoDB.
- `guide` no accede a funciones administrativas/comerciales sensibles.

## Capas activas

- `api/endpoints`: interfaz HTTP y wiring de permisos.
- `schemas`: contratos públicos de entrada/salida.
- `services`: reglas, transiciones y validaciones de dominio.
- `documents`: persistencia Beanie.
- `core`: configuración, seguridad JWT, manejo de errores.
- `common`: enums, permisos, constantes y códigos de error.

## Pendientes fuera de alcance

- firma digital con validez legal final;
- política final de facturación;
- importación masiva CSV/Excel.
