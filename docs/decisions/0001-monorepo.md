# 0001 - Monorepo backend + frontend

## Contexto

El proyecto requiere evolución simultánea de app móvil, backend y paquetes internos reutilizables.

## Decisión

Se adopta estructura monorepo con separación entre `apps/` y `packages/`.

## Impacto

- mejor trazabilidad
- mejor coherencia entre capas
- posibilidad de compartir paquetes internos del frontend

## Riesgos

- desorden si no se fijan convenciones
- crecimiento caótico si todo se deja en `apps/mobile`
