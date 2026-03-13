# Install

## Option A — Plugin install (recommended)

Install directly from a marketplace or git repo:

```
claude plugins add multi-agent-cowork
```

Or from a git URL:

```
claude plugins add https://github.com/<owner>/multi-agent-cowork.git
```

After installation, plugin sub-commands become available automatically:

- `/maw:dispatch <task>` — start a runtime workflow
- `/maw:status <run-id>` — check run status
- `/maw:resume <run-id>` — continue interrupted run
- `/maw:assign-routing` — set routing profile or overrides
- `/maw:show-routing` — view current routing config
- `/maw:clear-routing` — reset routing to defaults
- `/maw:list-profiles` — list built-in routing profiles

## Option B — Manual copy

1. Copy this package to `.claude/plugins/multi-agent-cowork` in your repository (or user config directory).
2. Claude Code will auto-discover the plugin via `.claude-plugin/plugin.json`.

## Post-install

1. Install and authenticate `codex`, `claude`, and `gemini` on the target machine.
2. Verify with:
   - `python3 .agents/multi-agent-cowork/runtime/maw.py doctor`
3. Optionally seed routing memory:
   - `/maw:list-profiles`
   - `/maw:assign-routing --profile balanced`
4. Optionally seed known failures baseline:
   - copy `examples/known-failures.json` to `.multi-agent-cowork/known-failures.json`
