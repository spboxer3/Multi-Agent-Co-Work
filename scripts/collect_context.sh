#!/usr/bin/env bash
set -euo pipefail

# Collect a lightweight snapshot of repository context for exploration.
# Usage:
#   ./scripts/collect_context.sh [PATH]
# Example:
#   ./scripts/collect_context.sh .

ROOT="${1:-.}"

if [ ! -d "$ROOT" ]; then
  echo "Path not found: $ROOT" >&2
  exit 1
fi

cd "$ROOT"

echo "== repo root =="
pwd

echo
printf '== git status ==\n'
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git status --short || true
else
  echo "git not available or not a git repository"
fi

echo
printf '== top-level files ==\n'
find . -maxdepth 2 \( -path './.git' -o -path './node_modules' -o -path './dist' -o -path './build' -o -path './coverage' \) -prune -o -maxdepth 2 -type f | sort | sed 's#^./##' | head -200

echo
printf '== package / build files ==\n'
find . -maxdepth 3 \( -name 'package.json' -o -name 'pnpm-workspace.yaml' -o -name 'turbo.json' -o -name 'tsconfig.json' -o -name 'vite.config.*' -o -name 'vitest.config.*' -o -name 'jest.config.*' -o -name 'eslint.config.*' -o -name '.eslintrc*' -o -name 'pyproject.toml' -o -name 'go.mod' -o -name 'Cargo.toml' \) | sort | sed 's#^./##'

echo
printf '== likely test files ==\n'
find . \( -path './node_modules' -o -path './.git' -o -path './dist' -o -path './build' -o -path './coverage' \) -prune -o -type f \( -name '*test*' -o -name '*spec*' \) | sort | sed 's#^./##' | head -200
