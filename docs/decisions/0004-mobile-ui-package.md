# 0004 - Migración gradual a mobile_ui

**Status:** postponed (2026-06-02)

## Contexto

Ya existen varios componentes visuales suficientemente estables para salir de `apps/mobile`.

Sin embargo, la migración masiva de imports (`../../` → `package:mobile`) y la extracción a packages requiere un trabajo de infraestructura que se ha pospuesto para no bloquear entregas funcionales.

## Decisión

Migrar gradualmente componentes maduros a `packages/mobile_ui`.

## Criterio de extracción

Un componente se extrae de `apps/mobile` a `packages/mobile_ui/**` SOLO cuando cumple TODOS estos criterios:

1. **Multi-feature**: el widget se usa en ≥2 features distintos (no solo en un screen).
2. **Sin dependencia de dominio**: el widget no importa modelos de dominio, repositorios ni controladores.
3. **API estable**: la interfaz del widget no ha cambiado en ≥2 semanas de desarrollo activo.

Hasta que los criterios se cumplan, el widget permanece inline en `apps/mobile`.

## Prerrequisitos

- W3.9 (migración a `package:mobile/` imports) debe completarse primero para que los imports dentro de `apps/mobile` referencien a `package:mobile_ui/...` sin path relativos rotos.
- El workspace ya declara `mobile_ui`, `mobile_domain`, `mobile_mocks` como dependencias, aunque los packages están vacíos.

## Riesgos

- mover demasiado pronto componentes aún inestables
- crear acoplamientos prematuros con shell o features
- romper imports existentes si la extracción no se coordina con W3.9
