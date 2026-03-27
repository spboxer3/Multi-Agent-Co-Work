---
name: dispatch
description: Dispatch a task to the multi-agent-cowork runtime orchestrator for cross-CLI execution.
---

IMPORTANT: This command must run from the **project directory** (not the plugin directory)
so that it uses the correct routing config and stores run artifacts in the project.

Run this exact command first:

```bash
cd "$PROJECT_DIR" && python "C:/Users/rolandchien/.claude/plugins/marketplaces/Multi-Agent-Co-Work/runtime/maw.py" dispatch --task "$ARGUMENTS"
```

Replace `$PROJECT_DIR` with the user's current working project directory.

Then summarize the outcome briefly and point to the run artifact it produced.
