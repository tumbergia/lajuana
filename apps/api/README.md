# API Backend

Backend FastAPI de La Juana.

## Estado actual (Fase 2)

La API implementa:

- autenticación JWT (`access + refresh`) con registro público en rol `unassigned`;
- autorización por permisos explícitos (`Permission` + `ROLE_PERMISSIONS`);
- gestión administrativa de usuarios (`/users`, admin-only, baja lógica);
- flujo central de reservas, participantes, pagos y configuración;
- módulos operativos extendidos: equines, saddles, assignments, logs, providers y policies;
- contrato unificado de errores `ApiErrorResponse`;
- documentación OpenAPI en `/docs`.

## Estructura

- `app/api/endpoints`: routers HTTP
- `app/services`: reglas de negocio
- `app/documents`: persistencia Beanie/Mongo
- `app/schemas`: contratos request/response
- `app/core`: config, seguridad, errores y DB
- `app/common`: enums, constantes y códigos de error

## Comandos

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Calidad local:

```bash
cd apps/api
ruff check .
ruff format --check .
pytest
```
