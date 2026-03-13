# Decision gates

## Explore -> Plan
Pass only if all are true:
- at least one provider returned `status=ok`
- `entrypoint_status=confirmed`
- `surface_coverage >= 0.70`
- a concrete file or symbol list exists
- at least one likely test surface exists
- no provider requested `re-explore`
- no blocker contains `unknown-surface`

If search is too wide, narrow in this order:
1. files on the observed call path
2. direct consumers of the touched symbol
3. test files targeting the same subsystem
4. only then adjacent abstractions

## Plan -> Implement
Pass only if all are true:
- the changed-file set is locked, or open with an explicit reason
- consumer scan has been done for each shared abstraction in the plan
- verification commands are deterministic shell commands
- rollback anchor is named
- missing tests are either added or written down as an explicit risk
- no provider requested `re-plan`

## Implement -> Verify
Pass only if all are true:
- implementer returned `status=ok`
- `scope_extension_needed=false`
- no provider requested `request-scope-extension`
- the summary explains how the patch matches the locked plan

If the implementer discovers the plan is wrong, do not patch around it. Return to plan.

## Verify -> Review
Pass only if all are true:
- every failed command is classified as `task-caused`, `pre-existing`, `flaky`, or `infrastructure`
- a failing command was rerun at least once before calling it `flaky`
- shell verification exists in production mode
- no provider requested `rollback`

## Review -> Report
Pass only if all are true:
- reviewer is not the implementer provider
- no unapproved plan drift exists
- every high-risk branch has either a test, a waiver, or a release block
- no provider requested `block-release`
