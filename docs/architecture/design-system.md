# Design System

## Objetivo

Unificar el lenguaje visual de la app y evitar duplicación de estilos y patrones.

## Base visual

- fondo oscuro dominante
- tipografía: Manrope + Inter
- tokens globales de color, radio y spacing
- componentes operativos, no decorativos

## Familias de componentes

- navegación y shell
- botones e inputs
- badges y feedback
- headers y breadcrumbs
- filtros segmentados
- timeline
- cards

## Reglas

1. No hardcodear colores ni tipografía.
2. No crear widgets gigantes con demasiadas variantes.
3. Si un componente es estable y reusable, migrarlo a `packages/mobile_ui`.
4. Si un componente depende demasiado del flujo actual, mantenerlo temporalmente en `apps/mobile`.
