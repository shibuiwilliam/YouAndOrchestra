#!/usr/bin/env bash
# Pre-commit lint hook for YaO
# Runs: ruff format check + ruff lint + mypy + architecture lint + YAML validation
# Triggered: before git commit (via pre-commit framework)

set -euo pipefail

echo "=== YaO Pre-commit Lint ==="

# Format check (no auto-fix in hook)
ruff format --check src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy --strict src/yao/

# Architecture lint
python tools/architecture_lint.py

echo "=== All pre-commit checks passed ==="
