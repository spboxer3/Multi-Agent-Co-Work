# Commands

## Plugin sub-commands

After installing the plugin, these sub-commands are available using colon syntax:

### Core runtime
- `/maw:dispatch <task>` — dispatch a task to the multi-agent system
- `/maw:status <run-id>` — check status of a run
- `/maw:resume <run-id>` — resume a paused or failed run

### Routing memory
- `/maw:list-profiles` — list available routing profiles
- `/maw:show-routing` — show current routing configuration
- `/maw:assign-routing --profile balanced` — apply a named profile
- `/maw:assign-routing --phase implement=codex --phase review=claude,gemini --note "frontend default"` — set per-phase routing
- `/maw:clear-routing` — reset routing to defaults

---

## Direct CLI

The underlying Python runtime can also be invoked directly:

### Core runtime
- `python3 .agents/multi-agent-cowork/runtime/maw.py doctor`
- `python3 .agents/multi-agent-cowork/runtime/maw.py dispatch --task "<task>"`
- `python3 .agents/multi-agent-cowork/runtime/maw.py status --run-id <id>`
- `python3 .agents/multi-agent-cowork/runtime/maw.py resume --run-id <id>`
- `python3 .agents/multi-agent-cowork/runtime/maw.py report --run-id <id>`

### Routing memory
- `python3 .agents/multi-agent-cowork/runtime/maw.py routing profiles`
- `python3 .agents/multi-agent-cowork/runtime/maw.py routing show`
- `python3 .agents/multi-agent-cowork/runtime/maw.py routing set --profile balanced`
- `python3 .agents/multi-agent-cowork/runtime/maw.py routing set --phase implement=codex --phase review=claude,gemini --note "frontend default"`
- `python3 .agents/multi-agent-cowork/runtime/maw.py routing clear`

## Persistent files
- routing memory: `.multi-agent-cowork/routing-memory.json`
- known failures baseline: `.multi-agent-cowork/known-failures.json`
- run artifacts: `.multi-agent-cowork/runs/<run-id>/`
