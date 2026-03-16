# Multi-Agent Co-Work Tutorial

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [Core Philosophy](#2-core-philosophy)
3. [Prerequisites](#3-prerequisites)
4. [Installation](#4-installation)
5. [Architecture Overview](#5-architecture-overview)
6. [The 7-Phase Workflow](#6-the-7-phase-workflow)
7. [Routing Profiles](#7-routing-profiles)
8. [Execution Modes](#8-execution-modes)
9. [Command Reference](#9-command-reference)
10. [Walk-Through: Bug Fix](#10-walk-through-bug-fix)
11. [Walk-Through: New Feature](#11-walk-through-new-feature)
12. [Decision Gates Explained](#12-decision-gates-explained)
13. [The NEVER Rules](#13-the-never-rules)
14. [Handling Edge Cases](#14-handling-edge-cases)
15. [Configuration Deep Dive](#15-configuration-deep-dive)
16. [Output Artifacts](#16-output-artifacts)
17. [Troubleshooting](#17-troubleshooting)
18. [FAQ](#18-faq)

---

## 1. What Is This?

Multi-Agent Co-Work (MAW) is a structured orchestration framework that coordinates multiple AI coding agents — Claude Code, Codex CLI, and Gemini CLI — to work together on non-trivial software engineering tasks. Instead of letting a single AI agent do everything (explore, plan, implement, test, review) in a messy, interleaved fashion, MAW forces strict role separation across distinct phases.

Think of it like a well-run software team: one person investigates the bug, another writes the fix, a different person runs the tests, and yet another reviews the code — each with clear handoff documents, not hallway conversations.

---

## 2. Core Philosophy

### The Problem: Role Bleed

The #1 failure mode in AI-assisted coding is **role bleed** — when exploration, implementation, and review blur together. An AI that is simultaneously exploring code, writing patches, and checking its own work will:
- Miss files it didn't look at carefully enough
- Rationalize its own bugs during "review"
- Skip verification because it "already knows" the fix works

### The Solution: Explicit Phases + Handoff Packets

MAW solves this by:
1. **Splitting work into 7 explicit phases**, each with a single responsibility
2. **Using handoff packets** (structured JSON documents) instead of direct agent communication
3. **Enforcing decision gates** — the orchestrator blocks phase transitions when evidence is incomplete
4. **Blind review** — the reviewer never sees the exploration report or the plan, only the diff and task description

---

## 3. Prerequisites

| Requirement | Details |
|---|---|
| Python | 3.11 or later |
| Claude Code CLI | Installed and authenticated (`claude` command available) |
| Codex CLI | (Optional) For cross-CLI implementation (`codex` command) |
| Gemini CLI | (Optional) For cross-CLI exploration/review (`gemini` command) |
| Git | Any recent version |
| Operating System | Windows, macOS, or Linux |

> **Note:** In **Subagent mode** (default for Claude Code), you only need Claude Code CLI. Codex and Gemini are only required for **Runtime mode** (cross-CLI orchestration).

---

## 4. Installation

### Method A: Plugin Installation (Recommended)

The simplest way to install is via the Claude Code plugin system:

```bash
claude plugins add multi-agent-cowork
```

After installation, all sub-commands become available as namespaced slash commands (e.g., `/maw:dispatch`, `/maw:status`). See [Section 9](#9-command-reference) for the full list.

### Method B: Manual Copy

Copy the `multi-agent-cowork` directory into your project and ensure the `.claude-plugin/plugin.json` file is present at the root of the package. This file is what Claude Code uses to discover the plugin and register its namespaced sub-commands.

```bash
cp -r /path/to/multi-agent-cowork  your-repo/.agents/multi-agent-cowork
```

> **Plugin system note:** Multi-Agent Co-Work uses the Claude Code plugin system (`.claude-plugin/plugin.json`), which enables namespaced sub-commands via the `plugin:skill` colon syntax. When installed as a plugin, each skill is exposed as `/maw:<skill-name>`.

### Step 2: Install CLI Tools

Helper scripts are provided in `scripts/`:

```bash
# Install Claude Code CLI
bash .agents/multi-agent-cowork/scripts/install_claude.sh

# Install Codex CLI (optional, for runtime mode)
bash .agents/multi-agent-cowork/scripts/install_codex.sh

# Install Gemini CLI (optional, for runtime mode)
bash .agents/multi-agent-cowork/scripts/install_gemini.sh
```

### Step 3: Verify Installation

```bash
python runtime/maw.py doctor
```

This command checks: repository root detection, config file validity, and CLI binary availability. Fix any issues it reports before proceeding.

### Step 4: (Optional) Set Up Routing

```bash
# View available routing profiles
python runtime/maw.py routing profiles

# Select a profile
python runtime/maw.py routing set --profile balanced
```

### Step 5: (Optional) Seed Known Failures

If your project has pre-existing test failures, create a baseline so the verifier doesn't flag them as new:

```bash
cp .agents/multi-agent-cowork/examples/known-failures.json \
   .multi-agent-cowork/known-failures.json
# Edit the file to list your actual known failures
```

---

## 5. Architecture Overview

> **Plugin architecture:** Multi-Agent Co-Work is packaged as a Claude Code plugin. The `.claude-plugin/plugin.json` file at the package root declares the plugin's metadata and registers its skills as namespaced sub-commands (using the `plugin:skill` colon syntax). This means that after installation, commands like `/maw:dispatch` are available directly in any Claude Code session without additional configuration.

### High-Level Flow

```
┌────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR (main agent)                   │
│   Frames task → Enforces gates → Writes handoff packets         │
└────┬──────┬──────┬──────┬──────┬──────┬──────┬────────────────┘
     │      │      │      │      │      │      │
     ▼      ▼      ▼      ▼      ▼      ▼      ▼
  INTAKE  EXPLORE  PLAN  IMPLEMENT VERIFY REVIEW REPORT
           │              │         │      │
           ▼              ▼         ▼      ▼
        Claude          Codex     Shell  Claude
        Gemini                   Claude  Gemini
```

### Key Concepts

| Concept | Description |
|---|---|
| **Orchestrator** | The central coordinator. It writes all handoff packets, evaluates decision gates, and never does implementation work itself. |
| **Provider** | An AI CLI tool (Claude, Codex, Gemini) or deterministic tool (Shell) that executes a specific phase. |
| **Handoff Packet** | A structured JSON document the orchestrator writes after each phase. It is the *only* thing the next phase is allowed to read. |
| **Decision Gate** | A checklist of conditions that must all be true before the orchestrator allows the workflow to advance to the next phase. |
| **Routing Profile** | A named configuration that maps each phase to one or more providers. |

### Communication Model

```
  ┌──────────┐         ┌──────────┐
  │ Explorer │         │  Planner │
  └────┬─────┘         └────┬─────┘
       │ result.json        │ result.json
       ▼                    ▼
  ┌─────────────────────────────────┐
  │          ORCHESTRATOR           │
  │  synthesizes → handoff packet   │
  └──────────────┬──────────────────┘
                 │ handoff packet
                 ▼
          ┌──────────────┐
          │ Implementer  │
          └──────────────┘
```

Agents **never** talk to each other directly. The Explorer does not tell the Implementer what to fix. The Reviewer never sees what the Explorer found. All communication flows through the orchestrator via handoff packets.

---

## 6. The 7-Phase Workflow

### Phase 1: INTAKE

The orchestrator frames the task. This is where you define:
- **Goal**: What should be true after the task is done?
- **Success criteria**: How do we know it worked?
- **Constraints**: What must NOT break?

The orchestrator writes `intake.json` and `manifest.json` into the run directory.

---

### Phase 2: EXPLORE

**Who:** Claude + Gemini (balanced profile), or Claude only (fast profile)
**Access:** Read-only. No code changes allowed.
**Purpose:** Map the terrain — find all relevant files, entry points, call flows, and risks.

The Explorer must produce:
```
Files: [path:line_range — role in the problem]
Entry points: [symbol names]
Call flow: A → B → C
Constraints: [what must not break]
Risks: [unknowns, fragile areas]
Questions: [what couldn't be determined]
```

**Critical rule:** The Explorer identifies problems but **never suggests fixes**. Saying "we should change X to Y" is role bleed. The correct output is "X is the entry point that handles escape key events" — facts, not prescriptions.

---

### Phase 3: PLAN

**Who:** Claude
**Purpose:** Create a locked implementation plan from the Explorer's evidence.

The Planner must:
1. **Lock the file set** — name every file that will be modified
2. **Scan consumers** — who imports or calls the changed code?
3. **Define verification commands** — concrete shell commands, not "run tests"
4. **Name a rollback anchor** — a git commit or stash to revert to if things go wrong

> Example of a good verification command: `pytest tests/test_modal.py -k "test_escape_nested" -v`
> Example of a bad one: "run the relevant tests"

---

### Phase 4: IMPLEMENT

**Who:** Codex (by default)
**Access:** Write-enabled, but bounded by the locked plan.
**Purpose:** Apply the edits defined in the plan — nothing more, nothing less.

Key rules:
- Only modify files listed in the locked plan
- If an unlisted file must change, emit `scope_extension_needed=true` and return to Plan
- Log any discovered-but-not-addressed issues as "deferred items"
- For changes touching >2 files, use `isolation: "worktree"` to work on an isolated copy

If the plan doesn't work in practice, **STOP and return to Plan**. Do not improvise.

---

### Phase 5: VERIFY

**Who:** Shell (deterministic) + Claude (analysis)
**Purpose:** Prove the implementation works with actual command output.

This phase runs **twice**:
1. **Baseline run** — before implementation, to capture pre-existing failures
2. **Validation run** — after implementation, to check if anything new broke

The verifier classifies every failure into one of four categories:

| Classification | Meaning |
|---|---|
| `task-caused` | This failure was introduced by our changes |
| `pre-existing` | This failure existed before our changes (in baseline) |
| `flaky` | This failure appears inconsistently (rerun confirms) |
| `infrastructure` | Network, Docker, CI issue — not code-related |

A failing command is rerun once before being classified as `flaky`.

---

### Phase 6: REVIEW

**Who:** Claude + Gemini (balanced profile)
**Access:** Read-only. **BLIND** — receives ONLY the diff + task description.
**Purpose:** Independent code review without confirmation bias.

The Reviewer **never sees**:
- The exploration report
- The implementation plan
- What the orchestrator expected to happen

This is intentional. Knowing intent causes confirmation bias. A blind reviewer catches 2-3x more logic bugs because they evaluate what the code *actually does*, not what it *was supposed to do*.

Output contract:
```
Correctness: [issues or "none found after reviewing N files, M hunks"]
Regression risk: [specific scenarios]
Edge cases: [uncovered]
Missing tests: [what should exist]
Verdict: [approve / request changes / block]
```

---

### Phase 7: REPORT

The orchestrator compiles all evidence into `final-report.md`:
- What changed and why
- What was verified and how
- What risks remain
- What was deferred for future work

The run is marked as `COMPLETED`, `PARTIAL`, or `FAILED`.

---

## 7. Routing Profiles

A routing profile determines which AI provider handles each phase. Three built-in profiles are available:

| Phase | balanced | fast | recovery |
|---|---|---|---|
| Explore | Claude + Gemini | Claude | Claude + Gemini |
| Plan | Claude | Claude | Claude |
| Implement | Codex | Codex | Codex |
| Verify | Shell + Claude | Shell | Shell + Claude + Gemini |
| Review | Claude + Gemini | Claude | Claude + Gemini |

- **balanced** — Best overall quality. Multiple perspectives for exploration and review. Recommended for most tasks.
- **fast** — Single provider per phase. Fastest execution but less redundancy. Good for well-understood, isolated changes.
- **recovery** — Maximum redundancy. Adds Gemini to verification. Use after a failed run or when dealing with flaky tests.

You can also create custom phase assignments:

```bash
# Use balanced profile but override the implement phase to use Claude
python3 runtime/maw.py routing set \
  --profile balanced \
  --phase implement=claude \
  --note "frontend task, Claude handles JSX better"
```

---

## 8. Execution Modes

### Mode 1: Subagent Mode (Claude Code Default)

In this mode, the orchestrator (your main Claude Code session) spawns Claude subagents for each role. No external CLIs needed. This is the simplest way to get started.

**How it works:**
1. You describe the task to Claude Code
2. Claude Code acts as the orchestrator, following the SKILL.md workflow
3. For Explore: spawns a subagent with `subagent_type: "Explore"`, thoroughness `"very thorough"`
4. For Implement: spawns a subagent with `isolation: "worktree"` when touching >2 files
5. For Verify: runs shell commands directly
6. For Review: spawns a read-only subagent with only the diff

**Triggering:**
- Just describe a task that matches the activation criteria, or
- Use the `/maw` slash command explicitly

### Mode 2: Runtime Mode (Cross-CLI)

In this mode, the Python runtime (`maw.py`) orchestrates across Claude CLI, Codex CLI, and Gemini CLI. Each provider runs as a separate process.

**Triggering:**
- Via plugin sub-commands: `/maw:dispatch <task>`, `/maw:status`, `/maw:resume`
- Via direct Python CLI: `python3 runtime/maw.py dispatch --task "your task"`

**How it works:**
1. You dispatch a task (via plugin sub-command or direct CLI)
2. The runtime creates a run directory with all artifacts
3. Each phase invokes the configured provider(s) via their CLIs
4. Results are captured as JSON, gates are evaluated, handoff packets are written
5. The run continues until completion, failure, or a gate block

**When to use Runtime mode:**
- You want different AIs for different phases (e.g., Codex for implementation, Gemini for additional review perspective)
- You need full audit trails with structured artifacts
- You're setting up CI/CD integration for automated code review

---

## 9. Command Reference

### Core Commands

```bash
# Check installation and configuration
python3 runtime/maw.py doctor

# Start a full workflow
python3 runtime/maw.py dispatch --task "fix the login timeout bug"

# Start but stop after a specific phase
python3 runtime/maw.py dispatch --task "..." --phase-limit implement

# Start from a specific phase (skip earlier phases)
python3 runtime/maw.py dispatch --task "..." --start-phase plan

# Check run status
python3 runtime/maw.py status --run-id <id>

# Resume an interrupted run
python3 runtime/maw.py resume --run-id <id>

# View the final report
python3 runtime/maw.py report --run-id <id>
```

### Routing Commands

```bash
# List available profiles
python3 runtime/maw.py routing profiles

# Show current routing configuration
python3 runtime/maw.py routing show

# Set a profile
python3 runtime/maw.py routing set --profile balanced

# Override specific phases
python3 runtime/maw.py routing set \
  --phase implement=codex \
  --phase review=claude,gemini \
  --note "frontend default"

# Reset routing to defaults
python3 runtime/maw.py routing clear
```

### Slash Commands (Inside CLI Sessions)

| CLI | Dispatch | Status | Resume |
|---|---|---|---|
| Claude Code | `/maw:dispatch <task>` | `/maw:status` | `/maw:resume` |
| Codex | `$dispatch <task>` | `$status` | `$resume` |
| Gemini | `/dispatch <task>` | `/status` | `/resume` |

### Additional Claude Code Plugin Sub-Commands

| Sub-Command | Description |
|---|---|
| `/maw:show-routing` | Show the current routing configuration |
| `/maw:assign-routing` | Assign a routing profile or override specific phases |
| `/maw:clear-routing` | Reset routing to defaults |
| `/maw:list-profiles` | List all available routing profiles |

---

## 10. Walk-Through: Bug Fix

Let's walk through a complete bug fix using MAW. The bug: pressing Escape inside a nested modal closes the parent settings panel.

### Step 1: Dispatch

```bash
python3 runtime/maw.py dispatch \
  --task "Fix: pressing Escape inside a nested modal closes the parent settings panel. \
          Expected: only the nested modal should close."
```

### Step 2: INTAKE

The orchestrator writes:
- **Goal:** Keep the parent settings panel open when Escape is handled by the nested modal
- **Success criteria:** Nested modal closes without collapsing the parent overlay
- **Constraints:** Do not regress global keyboard shortcuts

### Step 3: EXPLORE

Claude and Gemini search independently for:
- Modal keydown handlers → finds `src/components/Modal/useKeyHandler.ts:42-67`
- Escape key propagation → finds `event.stopPropagation()` is missing in nested case
- Overlay dismissal logic → finds `src/components/Overlay/Overlay.tsx:128`
- Tests around nested dialogs → finds `tests/modal.test.tsx` (no nested case)

**Gate check:** entry point confirmed, surface_coverage=0.85, risks identified. **PASS.**

### Step 4: PLAN

Claude creates a locked plan:
- **Files:** `useKeyHandler.ts`, `Overlay.tsx`, `modal.test.tsx`
- **Consumer scan:** `SettingsPanel.tsx` imports `Overlay` — must not break
- **Verification:** `npx jest tests/modal.test.tsx --verbose`
- **Rollback:** current HEAD commit `a3f2b1c`

### Step 5: IMPLEMENT

Codex applies the planned edits:
1. Add `event.stopPropagation()` in nested modal's escape handler
2. Add guard in Overlay to check if escape was already handled
3. Add new test case for nested escape behavior

### Step 6: VERIFY

```
Command: npx jest tests/modal.test.tsx --verbose
Exit code: 0
Output: Tests: 7 passed, 0 failed
New failures: none
Assessment: PASS
```

### Step 7: REVIEW + REPORT

Reviewer (blind — only sees diff + task):
- Correctness: event propagation logic looks correct
- Regression risk: global shortcuts could be affected if stopPropagation is too aggressive
- Verdict: **approve** (stopPropagation is scoped to nested modals only)

Final report compiled. Run marked as **COMPLETED**.

---

## 11. Walk-Through: New Feature

Adding bulk archive support to the notifications center.

```bash
python3 runtime/maw.py dispatch \
  --task "Add bulk archive support to the notifications center. \
          Users should be able to select multiple notifications and archive them at once. \
          Must handle partial failures and optimistic UI updates."
```

### Phase Summary

| Phase | What happens |
|---|---|
| **Explore** | Maps notification list state management, archive mutation flow, optimistic update helpers, API client/backend contract, existing single-archive tests |
| **Plan** | Locks: selection state module, bulk archive action, API client extension, optimistic state handling, new tests |
| **Implement** | Codex applies all changes. >5 files → split into two deliverables |
| **Verify** | Targeted tests for reducer state, component tests for selection, integration checks |
| **Review** | Checks: partial failure handling, stale selection after refresh, accessibility of bulk action controls |

---

## 12. Decision Gates Explained

Decision gates are the quality enforcement mechanism. The orchestrator will NOT advance to the next phase if any condition is unmet. Here's every gate in detail:

### Explore → Plan

| # | Condition | Why |
|---|---|---|
| 1 | At least one provider returned `status=ok` | Ensures exploration actually completed |
| 2 | `entrypoint_status=confirmed` | Can't plan without knowing where the problem starts |
| 3 | `surface_coverage >= 0.70` | Must examine at least 70% of relevant code surface |
| 4 | Concrete file or symbol list exists | Vague "somewhere in the modal code" is not actionable |
| 5 | At least one test surface identified | Need to know what to verify against |
| 6 | No `re-explore` requested | Provider flagged insufficient coverage |

**If the gate fails:** → Send back to Explore with the specific gap identified.

### Plan → Implement

| # | Condition |
|---|---|
| 1 | File set is locked (or open with explicit reason) |
| 2 | Consumer scan completed for each shared abstraction |
| 3 | Verification commands are concrete shell commands |
| 4 | Rollback anchor named |
| 5 | No `re-plan` requested |

### Implement → Verify

| # | Condition |
|---|---|
| 1 | Implementer returned `status=ok` |
| 2 | `scope_extension_needed=false` |
| 3 | Diff matches locked plan |

### Verify → Review

| # | Condition |
|---|---|
| 1 | Every failure is classified (`task-caused` / `pre-existing` / `flaky` / `infrastructure`) |
| 2 | Failing commands rerun before `flaky` classification |
| 3 | Shell verification present |
| 4 | No `rollback` requested |

### Review → Report

| # | Condition |
|---|---|
| 1 | Reviewer is not the implementer provider |
| 2 | No unapproved plan drift |
| 3 | High-risk branches have tests, waivers, or release blocks |
| 4 | No `block-release` requested |

---

## 13. The NEVER Rules

These rules exist because each one addresses a specific, observed failure pattern. Breaking any of them will degrade output quality.

| # | Rule | Why |
|---|---|---|
| 1 | **NEVER let Explorer suggest fixes** | Explorer maps terrain; Implementer decides changes. "We should change X to Y" from Explorer = role bleed. |
| 2 | **NEVER skip baseline verification** | Without a baseline, you can't tell "I broke this" from "already broken." Most common source of false confidence. |
| 3 | **NEVER show Reviewer the plan** | Knowing intent causes confirmation bias. Blind review catches 2-3x more bugs. |
| 4 | **NEVER expand scope during Implement** | "While I'm here" turns single-file fixes into three-module refactors. |
| 5 | **NEVER accept verification without commands** | "No errors" is not evidence. "Ran `npm test`, exit 0, 47 passed" is evidence. |
| 6 | **NEVER run Implement before Explore** | The "obvious fix" without exploration misses the 2nd and 3rd affected files every time. |
| 7 | **NEVER let agents communicate directly** | Direct chat leads to: implementer defending intent, reviewer inheriting framing, explorer contaminating planner. |

---

## 14. Handling Edge Cases

### When a Phase Gets Stuck

| Phase | Signal | Action |
|---|---|---|
| Explore | Can't find entry point after 3 searches | Widen: search error strings, config refs, test files |
| Plan | Unsure which approach | Produce 2 candidates, list trade-offs, pick the more reversible one |
| Implement | Plan doesn't work in practice | **STOP.** Return to Plan with new evidence. Do not improvise. |
| Verify | Unclear if failure is new or old | Diff failure output against baseline character-by-character |
| Review | Critical issue found | Return to Plan. Do not patch during Review. |

### Scope Extension

When the Implementer discovers it needs to modify a file not in the locked plan:

1. **DO NOT** silently edit the extra file
2. **DO NOT** hide it in notes or call it a "risk"
3. **DO** emit `scope_extension_needed=true` with `requested_files` and `decision="request-scope-extension"`
4. The workflow returns to Plan, where the Planner either approves the extension and relocks, or rejects it and requires a different strategy

### Scope Creep Signals

Pause and re-scope when any of these occur:
- Implementer edits a file not in the plan
- Diff is >3x planned size
- Understanding a 4th+ module becomes necessary
- Verifier finds failures in unrelated areas

**Response:** Log deferred items, constrain current scope, continue.

---

## 15. Configuration Deep Dive

The main configuration file is `config/default.toml`. Here's every section explained:

### [run] — Runtime Settings

```toml
[run]
state_dir = ".multi-agent-cowork"          # Where run artifacts are stored
routing_memory = ".multi-agent-cowork/routing-memory.json"  # Persistent routing config
known_failures = ".multi-agent-cowork/known-failures.json"  # Pre-existing failure baseline
max_parallel = 3                            # Max concurrent providers per phase
fail_fast = false                           # Stop run on first gate failure?
```

### [policies] — Enforcement Rules

```toml
[policies]
forbid_self_review = true     # Implementer and reviewer MUST be different providers
require_shell_verifier = true  # Shell must be in verify providers (production)
```

### [verification] — Test Commands

```toml
[verification]
commands = [
  "python3 -m compileall runtime tests",   # Syntax check
  "pytest -q"                               # Run tests
]
stop_on_failure = false       # Continue running remaining commands after failure?
rerun_failures_once = true    # Rerun failed commands once before classifying?
```

### [providers.*] — Provider Settings

```toml
[providers.codex]
command = "codex"                    # CLI binary name
model = "gpt-5.2-codex"            # Model to use
full_auto = true                     # Run without human confirmation
sandbox_read_only = "read-only"     # Permission mode for read-only phases
sandbox_write = "workspace-write"   # Permission mode for write phases
timeout_seconds = 2400              # Max execution time

[providers.claude]
command = "claude"
model = "sonnet"
read_only_permission_mode = "acceptEdits"
allow_unattended_write = false       # Require confirmation for writes
timeout_seconds = 2400

[providers.gemini]
command = "gemini"
read_only_only = true                # Never allow writes
extra_args = []                      # Additional CLI arguments
timeout_seconds = 2400

[providers.shell]
command = "sh"
timeout_seconds = 1800
```

---

## 16. Output Artifacts

Every run creates a structured directory under `.multi-agent-cowork/runs/<run-id>/`. Here's what each file is:

```
.multi-agent-cowork/runs/abc123/
│
├── manifest.json              # Run metadata: status, phases, gates, timing
├── intake.json                # Task framing: goal, success criteria, constraints
├── routing.json               # Routing snapshot for this run
│
├── explore/                   # Explorer outputs
│   ├── claude/result.json     #   Claude's exploration result
│   └── gemini/result.json     #   Gemini's exploration result
│
├── plan/
│   └── claude/result.json     # Locked implementation plan
│
├── implement/
│   └── codex/result.json      # Implementation result + deviations
│
├── verify/
│   ├── shell/
│   │   ├── cmd-1.stdout.txt          # First command output
│   │   ├── cmd-1.rerun.stdout.txt    # Rerun output (if failure)
│   │   └── result.json               # Classification of all results
│   └── claude/result.json            # Analysis of verification
│
├── review/
│   ├── claude/result.json     # Claude's blind review
│   └── gemini/result.json     # Gemini's blind review
│
├── handoffs/                  # Orchestrator-written transition documents
│   ├── explore-to-plan.json
│   ├── plan-to-implement.json
│   ├── implement-to-verify.json
│   └── verify-to-review.json
│
├── explore-summary.md         # Human-readable phase summaries
├── plan-summary.md
├── implement-summary.md
├── verify-summary.md
├── review-summary.md
│
└── final-report.md            # End-to-end report: changes, evidence, risks
```

---

## 17. Troubleshooting

### "doctor" reports missing CLI

If `maw.py doctor` says a CLI is not found, but you only plan to use Subagent mode, this is fine. You only need all three CLIs for Runtime mode.

### Gate blocked at Explore → Plan

Most common cause: `surface_coverage < 0.70`. This means the explorer didn't examine enough of the relevant codebase. The orchestrator will send it back to Explore with guidance to widen the search — check error strings, config references, or test files.

### Implementer requests scope extension

This is normal and expected behavior. The workflow returns to Plan, where the Planner approves or rejects the extension. No manual intervention needed.

### Verification failures classified as "task-caused"

This means the implementation introduced a regression. The workflow will:
1. Classify the failure
2. Potentially request rollback
3. Return to Plan with evidence of what went wrong

Check the verification output in `verify/shell/cmd-*.stdout.txt` for details.

### Run interrupted

Use `resume` to continue from where it left off:

```bash
python3 runtime/maw.py resume --run-id <id>
```

The manifest tracks which phase was reached, so the run picks up exactly where it stopped.

---

## 18. FAQ

### Q: When should I use MAW vs. just asking Claude directly?

Use MAW when **any** of these are true:
- You can't name all affected files without searching
- The change touches code consumed by other modules
- Root cause is uncertain
- Tests are missing or flaky

Use Claude directly when **all** of these are true:
- Every affected file is known
- The change is isolated with no downstream consumers
- Relevant tests exist and pass

---

### Q: Can I skip phases?

Yes, using the "compressed" workflow: **Explore → Implement → Verify**. This is appropriate when all affected files are known, the change is isolated, and relevant tests exist. Use `--start-phase` and `--phase-limit` to control which phases run.

---

### Q: What if I only have Claude Code, not Codex or Gemini?

Use Subagent mode (the default). Claude Code spawns subagents for each role. You get the same structured workflow and role separation, just all powered by Claude models. The key benefit — role separation and blind review — works just as well.

---

### Q: How long does a full workflow take?

It depends on the task complexity and codebase size. Each phase invokes AI providers which have their own processing times. The `timeout_seconds` setting in the config (default: 2400s per provider) prevents any single phase from hanging indefinitely.

---

### Q: Can I customize which provider handles which phase?

Yes. Use the routing commands:

```bash
# Set a base profile
python3 runtime/maw.py routing set --profile balanced

# Override specific phases
python3 runtime/maw.py routing set --phase implement=claude --phase review=gemini

# Add a note for context
python3 runtime/maw.py routing set --phase implement=claude --note "Claude handles TypeScript better"
```

Routing is persistent across runs until you clear it.

---

### Q: What are handoff packets and why do they matter?

Handoff packets are structured JSON documents that the orchestrator writes after each phase completes. They contain:
- Evidence from the completed phase
- Locked context for the next phase
- Gate evaluation results
- Unresolved risks and required actions

They matter because they are the **only** thing the next phase reads. This prevents agents from inheriting each other's biases, assumptions, or framings. The orchestrator controls the narrative, not the individual agents.

---

### Q: How do I view past runs?

```bash
# List run directories
ls .multi-agent-cowork/runs/

# View a specific run's status
python3 runtime/maw.py status --run-id <id>

# Read the final report
python3 runtime/maw.py report --run-id <id>

# Or read the report file directly
cat .multi-agent-cowork/runs/<id>/final-report.md
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                  MULTI-AGENT CO-WORK                         │
│                    Quick Reference                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PHASES:  Intake → Explore → Plan → Implement                │
│                    → Verify → Review → Report                │
│                                                              │
│  PROFILES:  balanced (default) | fast | recovery             │
│                                                              │
│  COMMANDS:                                                   │
│    doctor              Check setup                           │
│    dispatch --task ""   Start workflow                        │
│    status --run-id      Check progress                       │
│    resume --run-id      Continue interrupted                 │
│    report --run-id      View final report                    │
│    routing show         Current routing                      │
│    routing set          Change routing                       │
│                                                              │
│  NEVER:                                                      │
│    ✗ Explorer suggests fixes                                 │
│    ✗ Skip baseline verification                              │
│    ✗ Show Reviewer the plan                                  │
│    ✗ Expand scope in Implement                               │
│    ✗ Accept "no errors" as verification                      │
│    ✗ Implement before Explore                                │
│    ✗ Let agents talk directly                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

*This tutorial covers Multi-Agent Co-Work v4 (Claude Code plugin). For version history, see CHANGELOG.md.*
