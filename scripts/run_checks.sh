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

if [ -f package.json ]; then
  if command -v jq >/dev/null 2>&1; then
    HAS_LINT=$(jq -r '.scripts.lint // empty' package.json)
    HAS_TEST=$(jq -r '.scripts.test // empty' package.json)
    HAS_TYPECHECK=$(jq -r '.scripts.typecheck // empty' package.json)
    HAS_BUILD=$(jq -r '.scripts.build // empty' package.json)
  else
    HAS_LINT=""
    HAS_TEST=""
    HAS_TYPECHECK=""
    HAS_BUILD=""
  fi

  PKG=""
  if command -v pnpm >/dev/null 2>&1; then
    PKG="pnpm"
  elif command -v npm >/dev/null 2>&1; then
    PKG="npm"
  elif command -v yarn >/dev/null 2>&1; then
    PKG="yarn"
  fi

  if [ -n "$PKG" ]; then
    [ -n "$HAS_TEST" ] && run $PKG test || true
    [ -n "$HAS_LINT" ] && run $PKG run lint || true
    [ -n "$HAS_TYPECHECK" ] && run $PKG run typecheck || true
    [ -n "$HAS_BUILD" ] && run $PKG run build || true
  else
    echo "No Node package manager found"
  fi
else
  echo "No package.json found; adapt this script for your stack"
fi
