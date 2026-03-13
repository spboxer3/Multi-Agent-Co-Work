Use `.agents/multi-agent-cowork/skills/multi-agent-cowork` whenever a task needs real role separation across exploration, planning, implementation, verification, and review.

Key repository policy:
- implementer and reviewer must not be the same provider
- production verification must include shell
- scope extension must return to plan
- agents communicate only through orchestrator handoff packets
