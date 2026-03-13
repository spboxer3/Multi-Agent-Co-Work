# Handoff packet specification

## Purpose
A handoff packet is the only object the next phase should rely on. It must be strong enough that the next role can work without rereading peer free-form chat.

## Required top-level fields
- `packet_id`
- `schema_version`
- `from_phase`
- `to_phase`
- `created_at`
- `route_snapshot`
- `gate`
- `evidence_summary`
- `locked_context`
- `unresolved`
- `required_actions`
- `provider_decisions`
- `intervention`

## evidence_summary
Must answer:
- what files and symbols matter
- which entrypoint / side effect path is confirmed
- how much of the relevant surface is covered
- what test surfaces were identified

## locked_context
Use phase-specific locking:
- from explore: likely file set, entrypoint, test surfaces
- from plan: locked file set, verification commands, rollback anchor
- from implement: changed-file manifest, scope-extension status
- from verify: failure classifications, rerun evidence, safe-to-review verdict

## unresolved
Keep only the items that the next phase must care about:
- blockers
- open questions
- high-severity risks

## intervention
Contains:
- `owner` — which role has authority to stop or redirect
- `reason` — short explanation
- `recommended_next_phase`
