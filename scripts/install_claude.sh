#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p .claude/skills .claude/agents
cp -R "$ROOT/adapters/claude-code/skills/." .claude/skills/
cp -R "$ROOT/adapters/claude-code/agents/." .claude/agents/
echo "Installed Claude skills and agents"
