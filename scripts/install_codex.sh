#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p .codex/skills
for skill in multi-agent-cowork maw-dispatch maw-status maw-resume maw-show-routing maw-assign-routing maw-clear-routing; do
  rm -rf ".codex/skills/$skill"
  cp -R "$ROOT/skills/$skill" ".codex/skills/$skill"
done
echo "Installed Codex skills to .codex/skills"
