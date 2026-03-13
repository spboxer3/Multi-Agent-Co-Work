# Flaky verification playbook

## First rule
A single failure is not enough to call something task-caused if the command passes on immediate rerun.

## Classification ladder
Use this order:
1. **Infrastructure** — tool crash, timeout, network, package registry, OOM, permissions
2. **Flaky** — fail once, pass on immediate rerun with no code change
3. **Pre-existing** — matches a known failure signature from baseline history or was already listed before this run
4. **Task-caused** — persists across rerun and aligns with changed files, changed symbols, or newly added tests

## Immediate rerun rule
For every failing deterministic command:
- rerun once immediately
- if it passes, classify as `flaky`
- if it fails with the same signature, continue classification

## Baseline rule
If `.multi-agent-cowork/known-failures.json` exists and the signature matches an approved known failure entry, classify as `pre-existing`.

## Unsafe shortcuts
Do not call something `pre-existing` just because the changed files look unrelated.
Do not call something `flaky` without a rerun.
Do not call something `task-caused` if the failure text indicates environment breakage.
