mobile-run:
	cd apps/mobile && flutter run

mobile-test:
	cd apps/mobile && flutter test

mobile-pub-get:
	cd apps/mobile && flutter pub get

api-dev:
	cd apps/api && source .venv/bin/activate && fastapi dev app/main.py

api-test:
	cd apps/api && source .venv/bin/activate && pytest

api-lint:
	cd apps/api && source .venv/bin/activate && ruff check .

api-format:
	cd apps/api && source .venv/bin/activate && ruff format .

api-typecheck:
	cd apps/api && source .venv/bin/activate && mypy app

bootstrap:
	bash tooling/scripts/bootstrap.sh
