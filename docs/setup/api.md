# Setup API

## Entorno Python

```bash
cd apps/api
python -m venv .venv
```

Activa el entorno virtual:

- Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

- Linux/macOS:

```bash
source .venv/bin/activate
```

## Instalación

```bash
pip install -U pip
pip install -e ".[dev]"
```

## Ejecutar API

Desde la raíz del repo:

```bash
make api-dev
```

O desde apps/api:

```bash
uvicorn app.main:app --reload
```

## Validación de calidad

```bash
cd apps/api
source .venv/bin/activate
ruff check .
ruff format --check .
pytest
```

## Endpoint base

```bash
GET /api/v1/health
```
