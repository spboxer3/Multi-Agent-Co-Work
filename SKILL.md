---
name: maw
description: >-
  Coordinate non-trivial coding tasks through a structured multi-role workflow:
  orchestrate, explore, implement, verify, and review. Use for bug fixes, feature
  work, refactors, dependency upgrades, and code reviews that span multiple files
  or require careful validation. Triggers on: multi-file changes, unclear root cause,
  shared abstractions, missing tests, complex debugging, patch review, code audit.
  Also triggers on: /maw, multi-agent-cowork, maw dispatch, maw status.
---

# Multi-Agent Co-Work

Split coding tasks into explicit roles to prevent **role bleed** — the #1 failure
mode where exploring, implementing, and reviewing blur together and bugs slip through.

## Two execution modes

### Subagent mode (default in Claude Code)
Orchestrator spawns Claude subagents for each role. No external CLIs needed.
Use the role contracts and reference loading guide below.

### Runtime mode (cross-CLI orchestration)
Uses `runtime/maw.py` to dispatch tasks across Claude CLI, Codex CLI, and Gemini CLI.
**LOAD** `references/communication-protocol.md` — agents communicate only through handoff packets, never directly.

**Plugin sub-commands** (available after installing as a plugin):
- `/maw:dispatch <task>` — start a runtime workflow
- `/maw:status <run-id>` — check run progress
- `/maw:resume <run-id>` — continue an interrupted run
- `/maw:show-routing` — view current routing config
- `/maw:assign-routing` — set routing profile or overrides
- `/maw:clear-routing` — reset routing to defaults
- `/maw:list-profiles` — list built-in routing profiles

**Direct CLI** (always available):
```bash
python3 runtime/maw.py doctor
python3 runtime/maw.py dispatch --task "fix the settings panel escape key bug"
python3 runtime/maw.py status --run-id <id>
python3 runtime/maw.py resume --run-id <id>
python3 runtime/maw.py report --run-id <id>
python3 runtime/maw.py routing show
python3 runtime/maw.py routing set --profile balanced
python3 runtime/maw.py routing set --phase implement=codex --phase review=claude,gemini
```

Default routing (`config/default.toml`):
| Phase | balanced | fast |
|---|---|---|
| Explore | Claude + Gemini | Claude |
| Plan | Claude | Claude |
| Implement | Codex | Codex |
| Verify | Shell + Claude | Shell |
| Review | Claude + Gemini | Claude |

## Activation heuristic

**Full workflow** — when ANY is true:
- Cannot name all affected files without searching
- Change touches code consumed by other modules
- Root cause is uncertain
- Tests are missing or flaky

**Compressed** (Explore → Implement → Verify) — when ALL are true:
- Every affected file known without searching
- Change is isolated, no downstream consumers
- Relevant tests exist and pass

## NEVER

- **NEVER let Explorer suggest fixes.** Explorer maps terrain; Implementer decides
  changes. "We should change X to Y" from Explorer = role bleed. Send back with:
  "Identify, don't prescribe."

- **NEVER skip baseline verification.** Run relevant tests BEFORE implementation.
  Without a baseline, you cannot separate "I broke this" from "already broken."
  This is the most common source of false confidence.

- **NEVER show Reviewer the plan or exploration report.** Reviewer gets diff + task
  description only. Knowing intent causes confirmation bias. Blind review catches
  2-3x more logic bugs. Runtime enforces this via `forbid_self_review` policy.

- **NEVER expand scope during Implement.** Found a related bug? Log as deferred.
  "While I'm here" is how single-file fixes become three-module refactors.

- **NEVER accept verification without commands.** "No errors" is not evidence.
  "Ran `npm test`, exit 0, 47 passed 0 failed" is evidence. Runtime enforces
  `require_shell_verifier` policy for this reason.

- **NEVER run Implement before Explore completes.** The "obvious fix" applied
  without exploration misses the 2nd and 3rd affected files every time.

- **NEVER let agents communicate directly.** In runtime mode, providers write phase
  results only. Orchestrator synthesizes into handoff packets. Raw stdout is evidence,
  not coordination state. See `references/communication-protocol.md`.

## Phase gates

Orchestrator blocks transitions when evidence is missing.
**LOAD** `references/decision-gates.md` for runtime gate evaluation details.

### Explore → Plan
- [ ] Files listed with line ranges, not just names
- [ ] Entry point symbols identified
- [ ] Data flow direction mapped (A calls B calls C)
- [ ] ≥1 risk or unknown explicitly stated
- [ ] Baseline test results captured (or "no tests" with grep evidence)

Missing call paths → send back to Explore.

### Plan → Implement
- [ ] Each edit names file + function + nature of change
- [ ] Consumer files listed (who imports/calls the changed code)
- [ ] Validation = concrete commands, not "run tests"
- [ ] >5 files? → split into smaller deliverables

### Implement → Verify
- [ ] All planned edits applied (or deviation documented with evidence)
- [ ] No unplanned edits in diff
- [ ] Deferred items logged

### Verify → Review
- [ ] Commands with actual output, not paraphrased
- [ ] New failures separated from baseline failures
- [ ] Blocking vs non-blocking classification

## Role contracts

### Orchestrator (main agent)
Frames task. Selects workflow. Enforces gates. Compiles report.
**LOAD** `prompts/orchestrator.md` for decision framework.

### Explorer (subagent, read-only)
Spawn: `subagent_type: "Explore"`, thoroughness: `"very thorough"`.
Input: raw task description only. **Do NOT include** your hypotheses.
**MANDATORY LOAD**: `prompts/explorer.md` as system context.

Output contract:
```
Files: [path:line_range — role in the problem]
Entry points: [symbol names]
Call flow: A → B → C
Constraints: [what must not break]
Risks: [unknowns, fragile areas]
Questions: [what couldn't be determined]
```

### Implementer (subagent, write-enabled)
Spawn with `isolation: "worktree"` when changes touch >2 files.
Input: exploration report + approved plan.
**MANDATORY LOAD**: `prompts/implementer.md` as system context.

Output contract:
```
Edits: [file:function — what changed, why]
Deferred: [found but not addressed]
Deviations: [from plan, with evidence]
```

### Verifier (subagent)
Spawn TWICE: baseline (before impl) and validation (after impl).
Input (baseline): test commands from Plan.
Input (validation): same commands + baseline output for diff.
**MANDATORY LOAD**: `prompts/verifier.md` as system context.
**LOAD** `scripts/run_checks.sh` — adapt for the repo's stack.

Output contract:
```
Command: [exact command]
Exit code: [number]
Key output: [relevant lines]
New failures: [not in baseline]
Assessment: [pass / fail / inconclusive + reason]
```

### Reviewer (subagent, read-only, BLIND)
Input: diff + task description ONLY. No exploration report. No plan.
**MANDATORY LOAD**: `prompts/reviewer.md` as system context.

Output contract:
```
Correctness: [issues or "none found after reviewing N files, M hunks"]
Regression risk: [specific scenarios]
Edge cases: [uncovered]
Missing tests: [what should exist]
Verdict: [approve / request changes / block]
```

## Execution sequence

```
1. INTAKE  — frame task brief
2. EXPLORE + BASELINE VERIFY  — run in parallel
   [gate: explore evidence + baseline captured]
3. PLAN   — orchestrator writes plan
   [gate: plan covers all explore findings]
4. IMPLEMENT — worktree if >2 files
   [gate: diff matches plan]
5. VERIFY  — compare against baseline
   [gate: no new failures, or failures classified]
6. REVIEW  — blind, diff-only
   [gate: no blocking issues]
7. REPORT  — compile all evidence
```

## Scope creep signals

Pause and re-scope when:
- Implementer edits a file not in the plan
- Diff is >3x planned size
- Understanding a 4th+ module becomes necessary
- Verifier finds failures in unrelated areas

Response: log deferred items, constrain current scope, continue.

## When a phase is stuck

| Phase | Signal | Action |
|---|---|---|
| Explore | Can't find entry point after 3 searches | Widen: search error strings, config refs, test files that exercise the feature |
| Plan | Unsure which approach | Produce 2 candidates, list trade-offs, pick the more reversible one |
| Implement | Plan doesn't work in practice | STOP. Return to Plan with new evidence. Do not improvise. |
| Verify | Unclear if failure is new or old | Diff failure output against baseline character-by-character |
| Review | Critical issue found | Return to Plan. Do not patch during Review. |

## Reference loading guide

| Phase | LOAD | Do NOT load |
|---|---|---|
| Explore | `prompts/explorer.md`, `scripts/collect_context.sh` | implementer, verifier, reviewer prompts |
| Plan | `templates/implementation-plan.md`, `templates/task-brief.md` | — |
| Implement | `prompts/implementer.md` | explorer, reviewer prompts |
| Verify (×2) | `prompts/verifier.md`, `scripts/run_checks.sh` | — |
| Review | `prompts/reviewer.md`, `templates/review-report.md` | exploration report, implementation plan |
| Report | `scripts/summarize_diff.sh`, `templates/verification-report.md` | — |
| Runtime mode | `references/communication-protocol.md`, `references/decision-gates.md` | — |
