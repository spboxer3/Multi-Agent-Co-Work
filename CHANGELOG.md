# Changelog

## v0.3.0
- feat: consolidate sub-skill SKILL.md files into root SKILL.md for cleaner plugin structure
- feat: add coordination invariants, phase load rules, and handoff packet contract to SKILL.md
- feat: add intervention gates with per-role decision rules (re-explore, re-plan, rollback, block-release)
- feat: rename `resume` skill to `mawresume` to match plugin namespace convention
- fix: update `/maw:mawresume` command reference in SKILL.md
- docs: update README slash commands to use `maw:` colon syntax instead of `maw-` dash syntax
- docs: bump version to v0.3.0

## v0.2.0
- fix: resolve .CMD/.BAT executables on Windows via `shutil.which()` in `base.py`
- fix: pass long prompts via stdin instead of command-line args to avoid Windows 8191-char limit (Claude, Gemini, Codex)
- fix: clear `CLAUDECODE` env var to prevent nested session errors when spawning Claude CLI
- fix: set `encoding="utf-8"` on all `subprocess.run` calls to avoid cp950 decode errors on CJK Windows
- fix: use direct file write instead of `os.replace()` on Windows to avoid file-locking PermissionError
- fix: extract `structured_output` from Claude CLI JSON wrapper for correct field mapping
- fix: add `_result_from_payload()` helper in `base.py` to map all ProviderResult fields (entrypoint_status, surface_coverage, evidence_map, etc.)
- fix: use `path.is_file()` instead of `path.exists()` in `read_text()` to prevent PermissionError on directories

## v0.1.0
- Initial release
