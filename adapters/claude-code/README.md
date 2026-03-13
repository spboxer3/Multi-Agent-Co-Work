# Claude Code adapter

Claude Code discovers skills automatically via the plugin system. Commands use the colon syntax `/plugin-name:command` and are available without any manual registration.

All multi-agent-cowork commands are auto-discovered and invoked as:

- `/maw:dispatch`
- `/maw:status`
- `/maw:resume`
- `/maw:show-routing`
- `/maw:assign-routing`
- `/maw:clear-routing`
- `/maw:list-profiles`

Markdown files in `.claude/commands/` continue to work as custom slash commands alongside the plugin colon syntax.
