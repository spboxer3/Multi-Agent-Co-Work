#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Copy or symlink $ROOT/adapters/gemini/extension into your Gemini extensions directory, then install it with gemini extensions install <path-or-url>."
