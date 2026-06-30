# Quickstart — de git clone a servidor corriendo

## Prerequisitos

- Python 3.11+
- Flutter 3.29+ (channel stable)
- Dart 3.11+
- MongoDB (local o Atlas)
- JDK 17 (para Flutter Android)

## 1. Backend

```bash
# Entorno virtual
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -e ".[dev]"

# Variables de entorno (crear .env)
cat > .env <<EOF
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=lajuana
AUTH_JWT_SECRET=change-me
GEMINI_API_KEY=tu-key
EOF

# Iniciar servidor
make api-dev
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

## 2. Mobile

```bash
# Desde la raíz del repo
make mobile-pub-get
make mobile-run
# → Chrome o emulador
```

## 3. Seed data

```bash
cd apps/api
python -m app.cli seed -t reproducible   # datos base
python -m app.cli seed -t equines        # equinos
python -m app.cli seed -t experiences    # experiencias
```

## 4. Tests

```bash
make api-quality    # ruff lint + format check + pytest
make mobile-quality # dart format + flutter analyze + flutter test
```

## 5. Verification

```bash
# Health check
curl http://localhost:8000/api/v1/health
# → {"status":"ok","checks":{"mongodb":"ok"}}

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"123456"}'
```

## Problemas comunes

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: app` | Correr desde `apps/api/` o instalar con `pip install -e .` |
| MongoDB connection refused | Verificar que MongoDB esté corriendo (`mongod`) |
| Flutter `JAVA_HOME` not set | `export JAVA_HOME=/path/to/jdk17` |
| `flutter analyze` fails en Windows | Usar `make mobile-analyze` que configura JAVA_HOME |
| Seed falla con `time` object | No usar `datetime.time` — usar string ISO `"08:00:00"` |
