---
name: dispatch
description: Dispatch the repository-local orchestrator.
disable-model-invocation: true
argument-hint: [task]
allowed-tools: Bash, Read, Glob, Grep
---

Run this exact command first:

```bash
python3 .agents/multi-agent-cowork/runtime/maw.py dispatch --task "$ARGUMENTS"
```
