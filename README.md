# La Juana Monorepo

Monorepo principal del sistema de La Juana.

## Objetivo

Centralizar frontend móvil y backend en un único repositorio con reglas claras de estructura, desarrollo y evolución técnica.

Este repositorio se construye bajo estas decisiones base:

- app móvil como punto principal de operación;
- backend como fuente de verdad y coordinador de reglas críticas;
- enfoque mobile-first y offline-first;
- la reserva como entidad principal del sistema;
- trazabilidad y centralización como criterios obligatorios.

## Estructura

- `apps/mobile`: aplicación Flutter
- `apps/api`: backend FastAPI
- `packages/`: paquetes internos reutilizables del frontend
- `docs/`: decisiones, arquitectura y setup
- `tooling/`: scripts y automatización común
- `.github/workflows/`: CI futuro

## Principios de organización

1. No mezclar lógica de negocio con UI.
2. No acoplar frontend directamente a detalles de infraestructura.
3. No crear una carpeta `shared` falsa entre Python y Dart.
4. Los contratos entre frontend y backend se comparten por especificación, no por copiar modelos.
5. Toda decisión relevante debe quedar documentada en `docs/decisions`.

## Convenciones iniciales

- rama principal: `main`
- ramas de trabajo: `feat/*`, `fix/*`, `chore/*`, `docs/*`
- commits recomendados:
  - `feat: ...`
  - `fix: ...`
  - `chore: ...`
  - `docs: ...`
  - `refactor: ...`
  - `test: ...`

## Bootstrapping

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd la-juana
```

### 2. Inicializar frontend Flutter

```bash
cd apps/mobile
flutter create .
cd ../..
```

### 3. Inicializar backend Python

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install "fastapi[standard]" pytest ruff mypy
cd ../..
```

### 4. Comandos rápidos

```bash
make mobile-run
make mobile-test
make api-dev
make api-test
make api-lint
```

## Estado actual

Este repositorio arranca con estructura base y placeholders. La implementación funcional se hará sobre vertical slices centrados en la reserva y sus flujos principales.
