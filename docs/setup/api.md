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
pip install "fastapi[standard]" beanie pydantic pytest ruff mypy
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
