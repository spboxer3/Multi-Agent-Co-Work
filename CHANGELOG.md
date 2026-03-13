# Changelog

## v4.1.0
- Converted from Skill to Plugin format
- Added `.claude-plugin/plugin.json`
- Sub-commands now use plugin colon syntax (`/maw:dispatch` etc.)
- Renamed skill directories: removed `maw-` prefix
- Sub-commands are now auto-discovered by Claude Code plugin system

## v3.0.0
- rewrote main skill around expert gates and anti-patterns
- added persistent routing memory and routing commands
- added handoff packets for cross-agent communication
- added policy validation for self-review and shell verification
