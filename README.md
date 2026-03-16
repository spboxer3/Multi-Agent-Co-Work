# Multi-Agent Co-Work Plugin v0.1

Repository-local orchestrator for real multi-agent coding work across Codex CLI, Claude Code, Gemini CLI, and deterministic shell verification. Now available as a Claude Code **plugin**.

## Installation

```bash
# From the plugin registry
claude plugins add multi-agent-cowork

# Or install locally from a cloned repo
claude plugins add ./path/to/multi-agent-cowork
```

## Sub-commands

The plugin exposes slash commands directly inside Claude Code:

| Command | Purpose |
|---|---|
| `/maw:dispatch <task>` | Dispatch a task to the runtime orchestrator |
| `/maw:status <run-id>` | Show status of a run |
| `/maw:resume <run-id>` | Resume an interrupted run |
| `/maw:assign-routing` | Set routing profile or per-phase overrides |
| `/maw:show-routing` | Show current routing configuration |
| `/maw:clear-routing` | Reset routing to defaults |
| `/maw:list-profiles` | List built-in routing profiles |

## Fast path

Via plugin sub-commands:
```
/maw:list-profiles
/maw:assign-routing --profile balanced
/maw:dispatch fix the settings panel escape key bug
```

Via python directly:
```bash
python runtime/maw.py doctor
python runtime/maw.py routing profiles
python runtime/maw.py dispatch --task "<task>"
```
