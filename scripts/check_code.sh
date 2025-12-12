#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Ruff check"
ruff check .

echo "✨ Ruff format"
ruff format .

echo "🔍 Final Ruff check"
ruff check .

echo "🧪 Pytest"
pytest -q



