# Arquitectura mobile

## Estado actual

La app Flutter es la capa más avanzada del repositorio.

## Flujo de arranque

`main.dart -> bootstrap() -> LaJuanaApp`

## Componentes principales

- tema global light/dark
- shell base
- top bar y bottom nav custom
- interacción de voz contextual
- design system reusable
- playground visual para calibración

## Estado provisional

- `router.dart` aún no gobierna el flujo principal
- `DesignSystemPlayground` sigue usándose como entorno de visualización
- algunas piezas de UI estables aún viven dentro de `apps/mobile`

## Dirección correcta

1. separar playground de flujo principal;
2. mover UI estable a `packages/mobile_ui`;
3. organizar pantallas por feature;
4. introducir router real;
5. comenzar vertical funcional de reservas.
