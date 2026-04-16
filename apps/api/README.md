# API Backend

Backend FastAPI de La Juana.

## Rol

Centraliza lógica de negocio, validaciones críticas, sincronización, integraciones y consistencia global del sistema.

## Estado

Base mínima con endpoint de salud y estructura de módulos inicial.

## Estructura interna

- `app/api`: routers
- `app/core`: configuración, errores, utilidades transversales
- `app/domain`: entidades y reglas de dominio
- `app/repositories`: acceso a persistencia
- `app/schemas`: contratos de entrada y salida
- `app/services`: casos de uso y coordinación

## Regla

No meter toda la lógica en `main.py`. Ese archivo solo arranca la aplicación.
