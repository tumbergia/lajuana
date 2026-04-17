# Arquitectura API

## Estado actual

El backend está en fase base. Hoy expone endpoint de salud y estructura modular lista para evolucionar.

## Capas previstas

- `api/`: routers
- `core/`: configuración, errores y utilidades transversales
- `domain/`: reglas y entidades
- `repositories/`: persistencia
- `schemas/`: contratos de entrada y salida
- `services/`: casos de uso

## Regla

No concentrar lógica real en `main.py`. Ese archivo solo debe arrancar la aplicación y registrar el wiring principal.

## Próximo paso recomendado

Implementar la primera vertical funcional de reservas con:
- schemas
- service
- repository
- endpoint
