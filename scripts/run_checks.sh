#!/usr/bin/env bash
set -euo pipefail

# Run common validation commands with best-effort detection.
# The script is intentionally conservative and should be adapted per repo.
# Usage:
#   ./scripts/run_checks.sh [PATH]

ROOT="${1:-.}"

if [ ! -d "$ROOT" ]; then
  echo "Path not found: $ROOT" >&2
  exit 1
fi

cd "$ROOT"

run() {
  echo
  echo "> $*"
  "$@"
}

echo "=== Running Python static analysis and security checks ==="

# 1. Flake8 Style Check
if command -v flake8 >/dev/null 2>&1; then
  run flake8 runtime tests
else
  echo "flake8 not found, skipping style check."
fi

# 2. Mypy Type Check
if command -v mypy >/dev/null 2>&1; then
  run mypy runtime tests
else
  echo "mypy not found, skipping type check."
fi

# 3. Bandit Security Scan
if command -v bandit >/dev/null 2>&1; then
  run bandit -r runtime -s B602,B603,B404,B112
else
  echo "bandit not found, skipping security scan."
fi

# 4. Pytest with Coverage
if command -v pytest >/dev/null 2>&1; then
  run pytest --cov=runtime --cov-fail-under=40 tests/
else
  echo "pytest not found, skipping tests."
fi

# 5. Safety Dependency Check
if command -v safety >/dev/null 2>&1; then
  run safety check
else
  echo "safety not found, skipping dependency check."
fi

echo
echo "=== All checks completed! ==="
