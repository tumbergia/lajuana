# Arquitectura API

## Estado actual

La API esta en Fase 2, con foco en `Reservation` como agregado central y modulos operativos extendidos.

Referencia completa de endpoints: `docs/architecture/api-endpoints.md`.

Incluye:

- autenticacion JWT y autorizacion por permisos;
- roles `admin`, `guide`, `unassigned`;
- endpoints administrativos de usuarios;
- vertical de reservas (reserva, schedule, participante, pago, reglas de confirmacion);
- modulos operativos: equinos, sillas, asignaciones, bitacora, proveedores y polizas;
- contrato uniforme de errores para frontend y pruebas.
- catalogo de contactos de emergencia desde configuracion (`GET /config/emergency-contacts`).

## Reglas clave

- Las validaciones de negocio viven en `services/`.
- Los routers no contienen logica de confirmacion ni negocio critico.
- La confirmacion de reserva solo se ejecuta en backend.
- Los comprobantes guardan metadatos y referencia externa (`storage_key`), no binarios en MongoDB.
- `guide` no accede a funciones administrativas ni comerciales sensibles.

## Capas activas

- `api/endpoints`: interfaz HTTP y wiring de permisos.
- `schemas`: contratos publicos de entrada/salida.
- `services`: reglas, transiciones y validaciones de dominio.
- `documents`: persistencia Beanie.
- `core`: configuracion, seguridad JWT, manejo de errores.
- `common`: enums, permisos, constantes y codigos de error.

## Contrato de errores de negocio

Desde esta fase se centraliza en una fuente unica:

- catalogo maestro de casos `400/404/409` en `apps/api/app/api/business_errors.py` (`BUSINESS_ERROR_CASES`);
- matriz endpoint -> casos aplicables en `ENDPOINT_BUSINESS_CASES`;
- consumo unificado desde OpenAPI/Swagger y pruebas de contrato.

Regla operativa: frontend y tests dependen de `error.code`, no del texto del mensaje.

## Pendientes fuera de alcance

- firma digital con validez legal final;
- politica final de facturacion;
- importacion masiva CSV/Excel.
