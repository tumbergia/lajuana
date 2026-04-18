# 0004 - Migración gradual a mobile_ui

## Contexto

Ya existen varios componentes visuales suficientemente estables para salir de `apps/mobile`.

## Decisión

Migrar gradualmente componentes maduros a `packages/mobile_ui`.

## Criterio

Un componente se mueve cuando:
- es reusable;
- no depende de lógica de negocio;
- su API ya está razonablemente estable.

## Riesgos

- mover demasiado pronto componentes aún inestables
- crear acoplamientos prematuros con shell o features
