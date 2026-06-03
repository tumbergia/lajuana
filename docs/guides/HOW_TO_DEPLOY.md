# How to deploy

## CI pipeline

Dos workflows GitHub Actions:

### Quality (`quality.yml`)

Trigger: push/PR a `main` o `develop`

```
Backend:
  - Python 3.11 setup
  - pip install -e ".[dev]"
  - ruff check .
  - ruff format --check .
  - pytest

Mobile:
  - Flutter stable setup
  - dart format --output=none --set-exit-if-changed .
  - flutter analyze
  - flutter test
```

### OpenAPI check (`openapi-gen-check.yml`)

Trigger: PR que toca `app/schemas/**` o `openapi.json`

```
  - Generate OpenAPI spec from FastAPI
  - Generate Dart models
  - Check for uncommitted changes in packages/mobile_domain/lib/src/gen/
  - If dirty → fail (models desincronizados)
```

## Deploy manual

### Backend

```bash
# 1. Merge PR a develop → CI pasa
# 2. Merge develop a main
# 3. Tag version
git tag v1.x.x
git push origin v1.x.x

# 4. Deploy (depende del entorno)
# Ejemplo: docker build + push + restart
docker build -t lajuana/api:latest -f apps/api/Dockerfile .
docker push registry.example.com/lajuana/api:latest
# kubectl / docker-compose restart
```

### Mobile (Flutter)

```bash
# Android
cd apps/mobile && flutter build apk --release
# → build/app/outputs/flutter-apk/app-release.apk

# iOS
cd apps/mobile && flutter build ipa --release
# → build/ios/ipa/*.ipa
```

### Seeds (post-deploy)

```bash
cd apps/api
python -m app.cli seed -t reproducible
```

## Pre-deploy checklist

- [ ] CI quality pasa en develop
- [ ] OpenAPI gen check pasa
- [ ] Migraciones formales en `app/migrations/versions/` si hay cambios de schema
- [ ] CHANGELOG actualizado
- [ ] Breaking changes comunicados
