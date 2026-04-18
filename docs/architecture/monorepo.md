# Arquitectura del monorepo

## Objetivo

Centralizar frontend móvil, backend y paquetes internos en un único repositorio con fronteras claras.

## Estructura

- `apps/mobile`: aplicación Flutter
- `apps/api`: backend FastAPI
- `packages/mobile_ui`: componentes visuales estables y reutilizables
- `packages/mobile_core`: utilidades base
- `packages/mobile_domain`: contratos y modelos de dominio
- `packages/mobile_mocks`: datos fake y fixtures
- `docs/`: documentación técnica y operativa

## Reglas

1. `apps/` contiene aplicaciones ejecutables.
2. `packages/` contiene módulos internos reutilizables.
3. No compartir modelos crudos entre Python y Dart.
4. No crear paquetes nuevos sin necesidad real.
5. Toda modificación estructural relevante debe quedar documentada.
