# API Backend

Backend FastAPI de La Juana.

## Rol

Centraliza lógica de negocio, validaciones críticas, sincronización, integraciones y consistencia global del sistema.

## Estado

Base mínima ejecutable con:

- configuración por entorno;
- wiring centralizado por router;
- endpoint de salud versionado;
- lifecycle base para crecimiento.

## Estructura interna

- `app/api`: routers
- `app/core`: configuración, errores, utilidades transversales
- `app/domain`: entidades y reglas de dominio
- `app/repositories`: acceso a persistencia
- `app/schemas`: contratos de entrada y salida
- `app/services`: casos de uso y coordinación

## Regla

No meter toda la lógica en `main.py`. Ese archivo solo arranca la aplicación.

## Qué incluye hoy

- `FastAPI` con `lifespan` base;
- `APIRouter` principal con prefijo configurable (`/api/v1` por defecto);
- endpoint `GET /api/v1/health`;
- configuración con `pydantic-settings` desde `.env`;
- test básico de salud y tooling de calidad (`ruff`, `pytest`, `mypy`).

## Qué no incluye todavía

- modelos de negocio de reservas;
- casos de uso de cotización, pago o logística;
- repositorios y servicios funcionales.

## Setup rápido

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Ejecutar API

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload
```

## Calidad local

```bash
cd apps/api
source .venv/bin/activate
ruff check .
ruff format --check .
pytest
```

## Versionado de API

El versionado se define en configuración (`API_PREFIX` y `API_VERSION`) y se aplica en routing.
No se usa versionado en la estructura de carpetas.
