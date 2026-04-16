#!/usr/bin/env bash
set -e

echo "==> Bootstrapping La Juana monorepo"

if [ -d "apps/mobile" ]; then
  echo "Mobile folder exists"
else
  mkdir -p apps/mobile
fi

if [ -f "apps/mobile/pubspec.yaml" ]; then
  echo "Flutter app already initialized"
else
  echo "Initializing Flutter app..."
  (cd apps/mobile && flutter create .)
fi

if [ ! -d "apps/api/.venv" ]; then
  echo "Creating Python venv..."
  (cd apps/api && python -m venv .venv)
fi

echo "Installing backend dependencies..."
(
  cd apps/api
  source .venv/bin/activate
  pip install -U pip
  pip install "fastapi[standard]" pytest ruff mypy
)

echo "Done"
