MOBILE_JAVA_HOME ?= /c/Program Files/Java/jdk-17

# Base URL del API (opcional). Debe ser URL completa con esquema, p. ej. http://192.168.1.10:8000/api/v1
# Vacío = heurística: emulador → 10.0.2.2; Android físico → 127.0.0.1 (requiere adb reverse o ver abajo).
# Wi‑Fi físico: MOBILE_API_BASE_URL=http://<IP-de-tu-PC>:8000/api/v1 make mobile-profile (API con --host 0.0.0.0).
MOBILE_API_BASE_URL ?=
MOBILE_DART_DEFINES := $(if $(strip $(MOBILE_API_BASE_URL)),--dart-define=API_BASE_URL=$(MOBILE_API_BASE_URL),)

mobile-run:
	cd apps/mobile && JAVA_HOME="$(MOBILE_JAVA_HOME)" PATH="$$JAVA_HOME/bin:$$PATH" DART_VM_OPTIONS=--old_gen_heap_size=2048 flutter run $(MOBILE_DART_DEFINES)

mobile-profile:
	cd apps/mobile && JAVA_HOME="$(MOBILE_JAVA_HOME)" PATH="$$JAVA_HOME/bin:$$PATH" DART_VM_OPTIONS=--old_gen_heap_size=2048 flutter run --profile $(MOBILE_DART_DEFINES)

mobile-test:
	cd apps/mobile && JAVA_HOME="$(MOBILE_JAVA_HOME)" PATH="$$JAVA_HOME/bin:$$PATH" DART_VM_OPTIONS=--old_gen_heap_size=2048 flutter test

mobile-pub-get:
	cd apps/mobile && JAVA_HOME="$(MOBILE_JAVA_HOME)" PATH="$$JAVA_HOME/bin:$$PATH" DART_VM_OPTIONS=--old_gen_heap_size=2048 flutter pub get

mobile-format-check:
	dart format --output=none --set-exit-if-changed apps/mobile/lib apps/mobile/test packages

mobile-analyze:
	cd apps/mobile && JAVA_HOME="$(MOBILE_JAVA_HOME)" PATH="$$JAVA_HOME/bin:$$PATH" DART_VM_OPTIONS=--old_gen_heap_size=2048 flutter analyze

mobile-packages-analyze:
	cd packages/mobile_core && flutter analyze
	cd packages/mobile_domain && flutter analyze
	cd packages/mobile_mocks && flutter analyze
	cd packages/mobile_ui && flutter analyze

mobile-quality:
	$(MAKE) mobile-format-check
	$(MAKE) mobile-analyze
	$(MAKE) mobile-packages-analyze
	$(MAKE) mobile-test

ifeq ($(OS),Windows_NT)
API_PY := .venv/Scripts/python.exe
else
API_PY := .venv/bin/python
endif

api-dev:
	cd apps/api && $(API_PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

api-test:
	cd apps/api && $(API_PY) -m pytest

api-lint:
	cd apps/api && $(API_PY) -m ruff check .

api-format:
	cd apps/api && $(API_PY) -m ruff format .

api-format-check:
	cd apps/api && $(API_PY) -m ruff format --check .

api-typecheck:
	cd apps/api && $(API_PY) -m mypy app

api-mcp:
	cd apps/api && $(API_PY) -m app.mcp_server.server

api-ask-example:
	curl -X POST http://localhost:8000/api/v1/ask \
		-H "Content-Type: application/json" \
		-d '{"message":"Hola, quiero reservar recorrido de medio día para 4 personas el 20 de junio de 2026","channel":"test","from_phone":"+573001112233"}'

api-agentic-reset:
	bash tooling/scripts/reset_agentic_layer.sh

api-quality:
	$(MAKE) api-lint
	$(MAKE) api-format-check
	$(MAKE) api-test

api-install:
	cd apps/api && $(API_PY) -m pip install -e ".[dev]"

api-uninstall:
	cd apps/api && $(API_PY) -m pip uninstall -e ".[dev]"

bootstrap:
	bash tooling/scripts/bootstrap.sh
