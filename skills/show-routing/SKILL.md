---
name: show-routing
description: Show the persistent routing memory used for agent assignment.
---

IMPORTANT: This command must run from the **project directory** (not the plugin directory)
so that it reads the correct routing config for the current project.

Run this exact command first:

```bash
cd "$PROJECT_DIR" && python "C:/Users/rolandchien/.claude/plugins/marketplaces/Multi-Agent-Co-Work/runtime/maw.py" routing show
```

Replace `$PROJECT_DIR` with the user's current working project directory.
