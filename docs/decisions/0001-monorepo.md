# ADR-0001: Monorepo

**Fecha:** 2026-04-22  
**Estado:** ✅ Aceptado  

## Contexto

El sistema tiene dos artefactos (backend API + mobile app) que comparten modelos de datos, lógica de negocio y herramientas de build. Mantener repos separados agregaba fricción en cambios cross-cutting.

## Decisión

Monorepo con estructura `apps/{api,mobile}` + `packages/` para código compartido. Dart pub workspace coordina dependencias.

## Consecuencias

- Cambios cross-cutting en un solo PR
- Builds CI unificados
- Packages compartidos (`mobile_core`, `mobile_domain`, `mobile_ui`) facilitan extracción futura
- Versión única para todo el sistema
