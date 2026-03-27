---
name: clear-routing
description: Clear the persistent routing memory and fall back to config defaults.
---

IMPORTANT: This command must run from the **project directory** (not the plugin directory)
so that it clears the correct routing config for the current project.

Run this exact command first:

```bash
cd "$PROJECT_DIR" && python "C:/Users/rolandchien/.claude/plugins/marketplaces/Multi-Agent-Co-Work/runtime/maw.py" routing clear
```

Replace `$PROJECT_DIR` with the user's current working project directory.
