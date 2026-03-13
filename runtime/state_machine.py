from __future__ import annotations

from dataclasses import dataclass

from .models import PhaseName

ALLOWED_TRANSITIONS = {
    PhaseName.INTAKE.value: [PhaseName.EXPLORE.value],
    PhaseName.EXPLORE.value: [PhaseName.PLAN.value, PhaseName.EXPLORE.value],
    PhaseName.PLAN.value: [PhaseName.IMPLEMENT.value, PhaseName.PLAN.value, PhaseName.EXPLORE.value],
    PhaseName.IMPLEMENT.value: [PhaseName.VERIFY.value, PhaseName.PLAN.value],
    PhaseName.VERIFY.value: [PhaseName.REVIEW.value, PhaseName.IMPLEMENT.value, PhaseName.VERIFY.value],
    PhaseName.REVIEW.value: [PhaseName.REPORT.value, PhaseName.IMPLEMENT.value, PhaseName.REVIEW.value],
    PhaseName.REPORT.value: [],
}

NEXT_PHASE = {
    PhaseName.EXPLORE.value: PhaseName.PLAN.value,
    PhaseName.PLAN.value: PhaseName.IMPLEMENT.value,
    PhaseName.IMPLEMENT.value: PhaseName.VERIFY.value,
    PhaseName.VERIFY.value: PhaseName.REVIEW.value,
    PhaseName.REVIEW.value: PhaseName.REPORT.value,
}

RECOMMENDED_NEXT = {
    "re-explore": PhaseName.EXPLORE.value,
    "re-plan": PhaseName.PLAN.value,
    "request-scope-extension": PhaseName.PLAN.value,
    "rollback": PhaseName.IMPLEMENT.value,
    "block-release": PhaseName.IMPLEMENT.value,
}


@dataclass
class StateMachine:
    current: str = PhaseName.INTAKE.value

    def advance(self, nxt: str) -> None:
        allowed = ALLOWED_TRANSITIONS.get(self.current, [])
        if nxt not in allowed:
            raise ValueError(f"Invalid transition: {self.current} -> {nxt}")
        self.current = nxt
