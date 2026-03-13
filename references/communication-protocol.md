# Communication protocol

## Core rule
Agents do not communicate with each other directly. They only communicate through orchestrator-written handoff packets.

## Why
Direct peer conversation creates three recurring failures:
1. implementer starts defending intent instead of reporting facts
2. reviewer inherits the implementer’s framing and misses plan drift
3. explorer contaminates the planner with premature solution ideas

## What counts as communication state
Valid shared state:
- handoff packets under `.multi-agent-cowork/runs/<run-id>/handoffs/`
- locked plan artifacts referenced by a handoff packet
- deterministic shell outputs referenced by a handoff packet
- changed-file manifest written by orchestrator

Evidence only, not coordination state:
- provider stdout / stderr
- ad-hoc notes not cited in the handoff packet
- speculative TODOs from a provider

## Packet writing rule
Providers never write handoff packets. The orchestrator synthesizes provider outputs into a packet after evaluating the gate.

## Direct communication is forbidden
Forbidden examples:
- explorer telling implementer how to patch
- implementer sending self-justification directly to reviewer
- reviewer editing the same patch it is auditing in the same run
- verifier asking implementer to “just try one more tweak” without returning through plan

## Recovery mode
The orchestrator may expose peer raw stdout only when:
- JSON parsing failed
- packet synthesis lost critical evidence
- a human operator enabled debug mode

Even in recovery mode, the next phase still acts on the repaired packet, not on raw peer chat.
