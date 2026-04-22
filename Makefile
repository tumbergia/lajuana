MOBILE_JAVA_HOME ?= /c/Program Files/Java/jdk-17

mobile-run:
	cd apps/mobile && JAVA_HOME="$(MOBILE_JAVA_HOME)" PATH="$$JAVA_HOME/bin:$$PATH" DART_VM_OPTIONS=--old_gen_heap_size=2048 flutter run

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

API_PY := $(shell if [ -x apps/api/.venv/Scripts/python.exe ]; then echo .venv/Scripts/python.exe; else echo .venv/bin/python; fi)

api-dev:
	cd apps/api && $(API_PY) -m uvicorn app.main:app --reload

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
