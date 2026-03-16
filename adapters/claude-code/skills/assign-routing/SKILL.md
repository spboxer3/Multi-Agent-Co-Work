---
name: maw-assign-routing
description: Persist new routing choices.
disable-model-invocation: true
argument-hint: [--profile ... | --phase ...]
allowed-tools: Bash, Read, Glob, Grep
---

Run this exact command first:

```bash
python runtime/maw.py routing set $ARGUMENTS
```
