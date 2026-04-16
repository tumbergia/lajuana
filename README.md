# La Juana

[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white)](https://flutter.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.x-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.x-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)

## Objetivo

La Juana es una plataforma de digitalización operativa para la gestión integral de experiencias turísticas. Centraliza el flujo comercial y operativo completo: desde el primer contacto con el cliente hasta la ejecución del tour, pasando por cotización, pago, confirmación, logística, asignación de guías y bitácora de operación.

La reserva es la entidad principal del sistema. Toda acción relevante gira alrededor de ella.

El sistema opera bajo un enfoque **mobile-first** y **offline-first**, con la app móvil como nodo operativo principal y el backend como fuente de verdad para validaciones críticas y sincronización.

## Estructura

```
la-juana/
├── apps/
│   ├── mobile/        # Aplicación Flutter (nodo operativo principal)
│   └── api/           # Backend FastAPI + MongoDB
├── packages/
│   ├── mobile_core/   # Utilidades base del frontend
│   ├── mobile_domain/ # Modelos y contratos de dominio Flutter
│   ├── mobile_mocks/  # Fixtures y fakes para desarrollo
│   └── mobile_ui/     # Design system y componentes reutilizables
├── docs/              # Arquitectura, decisiones y setup
└── tooling/           # Scripts y automatización
```

## Cómo iniciar

### Requisitos previos

- Flutter 3.x
- Python 3.11+
- MongoDB 7.x (local o Atlas)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tumbergia/lajuana.git
cd lajuana
```

### 2. Inicializar la app Flutter

```bash
cd apps/mobile
flutter create .
cd ../..
```

### 3. Inicializar el backend Python

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install "fastapi[standard]" beanie pydantic pytest ruff mypy
cd ../..
```

### 4. Comandos disponibles

```bash
make api-dev        # Levanta el backend en modo desarrollo
make api-test       # Corre los tests del backend
make api-lint       # Linting con ruff
make mobile-run     # Corre la app Flutter
make mobile-test    # Tests del frontend
make bootstrap      # Inicializa todo el entorno desde cero
```
