# ADR-0004: Extracción mobile UI a packages

**Fecha:** 2026-06-02  
**Estado:** ⏳ Postergado  

## Contexto

Widgets reusables estaban mezclados con lógica de negocio en `lib/app/widgets/`. Para mantener la separación de capas (regla #3), necesitamos extraerlos a `packages/mobile_ui/`.

## Decisión

Extracción progresiva Googlereada por criterios:

1. **Widget estable** — sin cambios funcionales en las últimas 2 semanas
2. **Sin dependencias business** — no importa modelos de dominio ni repositorios
3. **API probada** — al menos 3 usos en diferentes features

Estado actual: `mobile_ui` poblado con 40 archivos (29 widgets, 6 theme, 4 voice).  
`mobile_domain` poblado con 23+ archivos (modelos + repos generados desde OpenAPI).  
`mobile_mocks` poblado con 2 archivos (fakes).

## Consecuencias

- Extracción completa queda para otro proyecto
- Packages actuales son funcionales y se usan en producción
- Nuevos widgets se crean directamente en `packages/mobile_ui/`
- Los ~21 widgets legacy en `lib/app/widgets/` se migran cuando toca modificarlos
