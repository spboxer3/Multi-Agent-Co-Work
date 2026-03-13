# Self review

This version fixes the main structural weakness from v3: it no longer relies on generic phase prose as the primary value.

What is materially different:
- gates now consume expert-only fields such as `entrypoint_status`, `surface_coverage`, `file_set_mode`, `scope_extension_needed`, and `failure_classification`
- handoff packets now carry a locked context, unresolved items, required actions, and explicit intervention ownership
- verify now has a flaky-test playbook and optional known-failures baseline
- routing memory now exposes profile listing in addition to show/set/clear

v4.1 plugin conversion:
- package now uses `.claude-plugin/plugin.json` for plugin discovery, replacing the previous manual copy-into-place workflow
- sub-skills renamed from the `maw-*` prefix to clean names (e.g., `dispatch`, `verify`, `review`, `routing-memory`), so the colon syntax enables proper namespaced sub-commands (`/maw:dispatch` instead of `/maw-dispatch`)
- this aligns with the Claude CLI plugin contract and makes the skill set discoverable without extra configuration

Remaining limitations:
- live provider invocation still depends on the target machine having authenticated `codex`, `claude`, and `gemini` CLIs installed
- pre-existing failure classification is strongest when `.multi-agent-cowork/known-failures.json` is maintained
