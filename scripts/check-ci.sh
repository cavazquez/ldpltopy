#!/usr/bin/env bash
# Ejecuta los mismos chequeos que .github/workflows/ci.yml (antes de push/PR).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> uv sync --group dev"
uv sync --group dev

echo "==> ruff check ."
uv run ruff check .

echo "==> ruff format --check ."
uv run ruff format --check .

echo "==> mypy ."
uv run mypy .

echo "==> pytest --benchmark-disable"
uv run pytest --benchmark-disable

echo "OK: mismos pasos que GitHub Actions completaron sin error."
