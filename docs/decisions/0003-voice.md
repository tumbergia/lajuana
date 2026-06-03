# ADR-0003: Navegación por voz

**Fecha:** 2026-04-22  
**Estado:** 🟡 Prototipo  

## Contexto

Operaciones ecuestres requieren manos libres. Guías necesitan interactuar sin soltar riendas.

## Decisión

Módulo de voz prototipo en `packages/mobile_ui/lib/src/voice/`. Integración vía `AppVoiceFab` en pantallas operativas. Reconocimiento local (no cloud) para latencia cero.

## Consecuencias

- Prototipo funcional pero no productivo
- Voice FAB presente en UI pero oculto en release build
- Pendiente: definición de comandos, testing en ruido ambiente, integración con flow de asignaciones
