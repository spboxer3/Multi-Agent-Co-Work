---
name: assign-routing
description: Persist a new routing profile or per-phase provider override for future runs.
---

IMPORTANT: This command must run from the **project directory** (not the plugin directory)
so that the routing config is saved where `dispatch` will read it.

Run this exact command first:

```bash
cd "$PROJECT_DIR" && python "C:/Users/rolandchien/.claude/plugins/marketplaces/Multi-Agent-Co-Work/runtime/maw.py" routing set $ARGUMENTS
```

Replace `$PROJECT_DIR` with the user's current working project directory (use `git rev-parse --show-toplevel` or the primary working directory from context).
