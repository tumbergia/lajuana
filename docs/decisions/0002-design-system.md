# ADR-0002: Design system propio

**Fecha:** 2026-04-22  
**Estado:** ✅ Aceptado  

## Contexto

Necesitábamos consistencia visual sin depender de librerías externas (Material You, Shadcn, etc.). El producto tiene branding propio (La Juana) con colores, tipografía (Manrope + Inter) y personalidad visual específica.

## Decisión

Design system propio implementado en `packages/mobile_ui/` con:
- Tokens de color, tipografía, radios (`AppColors`, `AppTextTheme`, `AppRadii`)
- Widgets base reusables (`AppButton`, `AppCard`, `AppTextField`, etc.)
- `AppTheme.light()`/`dark()` factory methods
- `ThemeExtension` para propiedades custom

## Consecuencias

- Consistencia visual en toda la app
- Sin dependencia externa de design system
- Migración progresiva: widgets estables se mueven de `lib/app/widgets/` a `packages/mobile_ui/`
- ADR-0004 documenta la estrategia de extracción
