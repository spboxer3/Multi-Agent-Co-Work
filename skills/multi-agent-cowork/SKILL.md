---
name: multi-agent-cowork
description: Run real multi-agent coding work across Codex CLI, Claude Code, Gemini CLI, and shell verification when you need hard role separation, structured handoffs, routing memory, and intervention gates.
---

# Multi-Agent Co-Work

Use this skill only for tasks where role contamination is more dangerous than latency: cross-file bug fixes, migrations, risky refactors, patch review, release-blocking incidents, or any request that explicitly asks for multiple agents.

This is not a generic software-process reminder. It is a coordination contract for real cross-CLI execution.

## Activation test

Activate this skill when **two or more** of the following are true:
- implementation and review must be performed by different providers
- the blast radius is unclear after the first search pass
- verification depends on deterministic commands, not model judgment alone
- the task crosses module boundaries, shared abstractions, or migrations
- the user wants durable role assignment such as `codex implements, claude reviews`

Do **not** activate it for one-file edits, pure explanation work, or low-risk content tweaks.

## Default production routing

Default profile: `balanced`
- explore: `claude`, `gemini`
- plan: `claude`
- implement: `codex`
- verify: `shell`, `claude`
- review: `claude`, `gemini`

Persistent routing memory lives at `.multi-agent-cowork/routing-memory.json`.

Change it with:
- `python runtime/maw.py routing profiles`
- `python runtime/maw.py routing show`
- `python runtime/maw.py routing set --profile balanced`
- `python runtime/maw.py routing set --phase implement=codex --phase review=claude,gemini`
- `python runtime/maw.py routing clear`

## Coordination invariants

1. **No peer-to-peer chat.** Agents never coordinate by conversational back-and-forth.
2. **Only the orchestrator writes handoff packets.** Provider stdout is evidence, not shared state.
3. **Every phase consumes a locked packet.** If a phase needs more than the packet allows, it must request intervention.
4. **Implementer cannot self-approve scope growth.** Scope change must go back through plan.
5. **Reviewer cannot review the provider that implemented.** If routing says otherwise, treat it as a policy error.
6. **Production verify requires shell.** LLM-only verify is insufficient.

## NEVER

NEVER leave explore with `surface_coverage < 0.70` unless the planner explicitly marks why a narrower search is sufficient.
Reason: premature convergence creates false confidence and misses shared consumers.

NEVER let the implementer repair a bad plan by “just touching one extra file”.
Reason: unapproved file-set expansion hides the true blast radius. Use `scope_extension_needed=true` and return to plan.

NEVER let verify classify a failure as task-caused on first observation if the command passes on immediate rerun.
Reason: that is a flaky candidate until proven persistent.

NEVER let review consume raw implementer narrative outside the orchestrator packet.
Reason: self-justification pollutes the audit surface and hides plan drift.

NEVER unblock release when verify has only `infrastructure` classification and no deterministic rerun plan.
Reason: lack of evidence is not evidence of safety.

NEVER allow reviewer and implementer to share provider identity in the same run.
Reason: confirmation bias beats good intentions.

## Who intervenes, and when

- **Explorer** may stop the run with `decision="re-explore"` when the entrypoint is unknown, evidence conflicts, or search breadth exploded without a dominant causal path.
- **Planner** may stop the run with `decision="re-plan"` when the file set is still ambiguous, consumers were not checked, or verification commands are non-deterministic.
- **Implementer** may request `decision="request-scope-extension"` when the locked plan is invalidated by a hidden consumer, shared abstraction, or missing prerequisite.
- **Verifier** may issue `decision="rollback"` when task-caused failures persist after rerun or when deterministic verification contradicts the claimed patch intent.
- **Reviewer** may issue `decision="block-release"` when the patch violates the locked plan, hides unapproved scope growth, or leaves a high-risk branch untested.

## Phase load rules

### Explore
Load exactly:
- `prompts/explorer.md`
- `templates/exploration-report.md`
- `references/explore-convergence.md`
- `references/handoff-packet-spec.md`
- `references/communication-protocol.md`

Do not load:
- `prompts/implementer.md`
- `prompts/reviewer.md`

Exit only when all are true:
- `entrypoint_status = confirmed`
- `surface_coverage >= 0.70`
- at least one consumer or side effect path is named
- at least one likely test surface is named
- no blocker remains labeled `unknown-surface`

### Plan
Load exactly:
- `prompts/planner.md`
- `templates/implementation-plan.md`
- `references/decision-gates.md`
- `references/scope-extension-protocol.md`
- latest `explore -> plan` handoff packet

Exit only when all are true:
- `file_set_mode = locked` or `open-with-reason`
- verification commands are concrete shell commands
- consumer scan was performed for touched abstractions
- rollback anchor is named

### Implement
Load exactly:
- `prompts/implementer.md`
- `references/scope-extension-protocol.md`
- locked `plan -> implement` handoff packet

If the patch needs extra files, do **not** continue. Emit:
- `scope_extension_needed=true`
- `scope_extension_reason`
- `requested_files`
- `decision="request-scope-extension"`

### Verify
Load exactly:
- `prompts/verifier.md`
- `templates/verification-report.md`
- `references/flaky-verification-playbook.md`
- `implement -> verify` handoff packet
- shell verifier output when configured

Exit only when all failures are classified as one of:
- `task-caused`
- `pre-existing`
- `flaky`
- `infrastructure`

If classification is missing, verify is incomplete.

### Review
Load exactly:
- `prompts/reviewer.md`
- `templates/review-report.md`
- `references/intervention-matrix.md`
- `verify -> review` handoff packet
- changed-file manifest and verification evidence

Do not load:
- raw implementer defense text outside the packet

Block release when any of the following is true:
- plan drift without approved scope extension
- high-risk branch lacks test or explicit waiver
- verifier requested rollback
- reviewer is the same provider as implementer

## Handoff packet contract

All phase-to-phase communication must use orchestrator-written packets in:

```text
.multi-agent-cowork/runs/<run-id>/handoffs/
```

Every packet must contain:
- `packet_id`, `schema_version`, `from_phase`, `to_phase`
- `route_snapshot`
- `gate`
- `evidence_summary`
- `locked_context`
- `unresolved`
- `required_actions`
- `provider_decisions`
- `intervention`

The next phase may read the packet and orchestrator-selected locked artifacts only.

## Dispatch and slash wrappers

Primary runtime:

```bash
python runtime/maw.py dispatch --task "<task>"
```

Plugin sub-commands (Claude Code, after installing as plugin):
- `/maw:dispatch <task>`
- `/maw:status <run-id>`
- `/maw:resume <run-id>`
- `/maw:assign-routing --profile balanced`
- `/maw:clear-routing`
- `/maw:show-routing`
- `/maw:list-profiles`
