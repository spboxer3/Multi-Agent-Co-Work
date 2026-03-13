# Codex adapter

Codex supports repo-local skills and explicit skill invocation with `$skill-name`. The Claude Code plugin colon syntax (`/plugin:command`) does not apply to Codex; Codex adapter wrappers must be installed separately into `.codex/skills/`.

Recommended wrappers:

- `$dispatch`
- `$status`
- `$resume`
- `$show-routing`
- `$assign-routing`
- `$clear-routing`
- `$list-profiles`

> **Note:** The old `$maw-` prefixed names (`$maw-dispatch`, `$maw-status`, etc.) are deprecated. Use the names above instead.
