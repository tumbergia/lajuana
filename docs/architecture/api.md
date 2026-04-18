# Arquitectura API

## Estado actual

El backend está en fase base ejecutable.
Hoy centraliza:

- bootstrap de FastAPI;
- configuración por entorno;
- routing principal versionado;
- endpoint de salud.

## Capas previstas

- `api/`: routers
- `core/`: configuración, errores y utilidades transversales
- `domain/`: reglas y entidades
- `repositories/`: persistencia
- `schemas/`: contratos de entrada y salida
- `services/`: casos de uso

## Regla

No concentrar lógica real en `main.py`. Ese archivo solo debe arrancar la aplicación y registrar el wiring principal.

## Versionado

El versionado de API se resuelve en rutas (`/api/v1/...`) usando configuración.
No se versiona por carpetas (no `api/v1/` en filesystem).

## Alcance de esta fase

- sí: base técnica limpia, validable y documentada;
- no: lógica de dominio de reservas y verticales funcionales.

## Próximo paso recomendado

Implementar la primera vertical funcional de reservas con:
- schemas
- service
- repository
- endpoint
