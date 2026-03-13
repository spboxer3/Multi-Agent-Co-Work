---
name: status
description: Show status for a run.
disable-model-invocation: true
argument-hint: [run-id]
allowed-tools: Bash, Read, Glob, Grep
---

Run this exact command first:

```bash
python3 .agents/multi-agent-cowork/runtime/maw.py status --run-id "$ARGUMENTS"
```
