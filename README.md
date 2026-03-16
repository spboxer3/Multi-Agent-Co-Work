# Multi-Agent Co-Work Plugin v0.2

Repository-local orchestrator for real multi-agent coding work across Codex CLI, Claude Code, Gemini CLI, and deterministic shell verification. Now available as a Claude Code **plugin**.

## Installation

### Step 1 — Add the marketplace

```bash
claude plugins marketplace add spboxer3/Multi-Agent-Co-Work
```

### Step 2 — Install the plugin

```bash
claude plugins install maw@Multi-Agent-Co-Work
```

### Step 3 — Restart Claude Code

After restart, all `/maw-*` slash commands become available.

### Step 4 (Optional) — Install Runtime CLIs

Runtime mode dispatches tasks across three different AI CLIs. Install and authenticate each one:

- **Claude CLI** — `claude` (already installed if you are using Claude Code)
- **Codex CLI** — `npm install -g @openai/codex`
- **Gemini CLI** — `npm install -g @anthropic-ai/gemini`

Verify installation:

```bash
python runtime/maw.py doctor
```

## Slash Commands

| Command | Purpose |
|---|---|
| `/maw` | Main skill — auto-triggers the structured multi-role workflow |
| `/maw-dispatch <task>` | Dispatch a task to the runtime orchestrator (Claude + Codex + Gemini) |
| `/maw-status <run-id>` | Show status of a run |
| `/maw-resume <run-id>` | Resume an interrupted run |
| `/maw-assign-routing` | Set routing profile or per-phase overrides |
| `/maw-show-routing` | Show current routing configuration |
| `/maw-clear-routing` | Reset routing to defaults |
| `/maw-list-profiles` | List built-in routing profiles |

## Quick Start

```
/maw-list-profiles
/maw-assign-routing --profile balanced
/maw-dispatch fix the settings panel escape key bug
```

Or via Python directly:

```bash
python runtime/maw.py doctor
python runtime/maw.py routing profiles
python runtime/maw.py dispatch --task "<task>"
```

## Updating

```bash
claude plugins marketplace update Multi-Agent-Co-Work
claude plugins uninstall maw@Multi-Agent-Co-Work
claude plugins install maw@Multi-Agent-Co-Work
```
