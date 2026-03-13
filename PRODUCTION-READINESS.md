# Production readiness

## Required
- install and authenticate `codex`, `claude`, and `gemini`
- install the plugin via `claude plugins add multi-agent-cowork` or copy the package so that `.claude-plugin/plugin.json` is discoverable. After installation, plugin sub-commands (`/maw:dispatch`, `/maw:status`, `/maw:resume`, etc.) are available automatically.
- verify `python3 .agents/multi-agent-cowork/runtime/maw.py doctor`
- set routing memory if your team wants a non-default profile
- maintain `.multi-agent-cowork/known-failures.json` for stable pre-existing failure classification

## Recommended
- keep shell verification deterministic and fast
- keep review providers different from implement provider
- treat human override as an explicit policy exception and record it in the next handoff packet
