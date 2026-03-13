#!/usr/bin/env bash
set -euo pipefail

# Summarize changed files and rough churn for review/report phases.
# Usage:
#   ./scripts/summarize_diff.sh [BASE_REF]
# Example:
#   ./scripts/summarize_diff.sh HEAD~1

BASE="${1:-HEAD}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository" >&2
  exit 1
fi

echo "== changed files =="
git diff --name-only "$BASE"...HEAD || true

echo
echo "== diff stat =="
git diff --stat "$BASE"...HEAD || true

echo
echo "== staged diff stat =="
git diff --cached --stat || true
