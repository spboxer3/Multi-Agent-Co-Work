# Intervention matrix

| Phase | Who may stop progress | Trigger | Required decision | Recommended next phase |
| --- | --- | --- | --- | --- |
| explore | explorer | entrypoint unknown, evidence conflict, search too wide | `re-explore` | `explore` |
| plan | planner | file set ambiguous, consumer scan missing, weak verification | `re-plan` | `plan` or `explore` |
| implement | implementer | locked plan invalidated, extra file required | `request-scope-extension` | `plan` |
| verify | verifier | persistent task-caused failure | `rollback` | `implement` |
| review | reviewer | unsafe patch, plan drift, untested critical branch | `block-release` | `implement` or human review |

## Human override
A human may override any gate, but the override reason must be written into the next handoff packet.
