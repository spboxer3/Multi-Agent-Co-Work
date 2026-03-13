from __future__ import annotations

import json
from pathlib import Path

from .artifacts import context_snippet
from .utils import read_text

PHASE_TEMPLATE = {
    "explore": "exploration-report.md",
    "plan": "implementation-plan.md",
    "verify": "verification-report.md",
    "review": "review-report.md",
}

ROLE_PROMPT = {
    "explorer": "explorer.md",
    "planner": "planner.md",
    "implementer": "implementer.md",
    "verifier": "verifier.md",
    "reviewer": "reviewer.md",
}

PHASE_REFERENCES = {
    "explore": ["explore-convergence.md", "handoff-packet-spec.md", "communication-protocol.md", "decision-gates.md"],
    "plan": ["decision-gates.md", "scope-extension-protocol.md", "handoff-packet-spec.md"],
    "implement": ["scope-extension-protocol.md", "handoff-packet-spec.md"],
    "verify": ["flaky-verification-playbook.md", "decision-gates.md", "handoff-packet-spec.md"],
    "review": ["intervention-matrix.md", "handoff-packet-spec.md", "communication-protocol.md", "decision-gates.md"],
}


def build_prompt(*, provider: str, role: str, phase: str, task: str, repo_root: Path, run_dir: Path, package_root: Path, writable: bool, schema: dict) -> str:
    prompt_text = read_text(package_root / "prompts" / ROLE_PROMPT.get(role, ""))
    template_text = read_text(package_root / "templates" / PHASE_TEMPLATE.get(phase, ""))
    references = "\n\n".join(
        f"## {name}\n{read_text(package_root / 'references' / name)}"
        for name in PHASE_REFERENCES.get(phase, [])
        if (package_root / 'references' / name).exists()
    )
    context_paths = [
        run_dir / "intake.json",
        run_dir / "routing.json",
        run_dir / "explore-summary.md",
        run_dir / "plan-summary.md",
        run_dir / "implement-summary.md",
        run_dir / "verify-summary.md",
        run_dir / "review-summary.md",
        run_dir / "handoffs" / "explore-to-plan.json",
        run_dir / "handoffs" / "plan-to-implement.json",
        run_dir / "handoffs" / "implement-to-verify.json",
        run_dir / "handoffs" / "verify-to-review.json",
    ]
    context = context_snippet([p for p in context_paths if p.exists()])
    write_rule = "You may edit files only if this phase is allowed to write and only within the locked plan." if writable else "Do not edit files."
    return (
        f"You are the `{role}` agent running through the `{provider}` CLI in a cross-CLI orchestrated workflow.\n\n"
        f"Task:\n{task}\n\n"
        f"Repository root:\n{repo_root}\n"
        f"Run directory:\n{run_dir}\n"
        f"Current phase:\n{phase}\n\n"
        f"Hard rules:\n"
        f"- {write_rule}\n"
        f"- You do not talk directly to peer agents.\n"
        f"- Return only JSON matching the schema.\n"
        f"- Use the handoff packet as the source of truth.\n"
        f"- If you need more scope than the packet allows, request intervention through your decision field.\n\n"
        f"Role prompt:\n{prompt_text}\n\n"
        f"References:\n{references}\n\n"
        f"Expected report shape:\n{template_text}\n\n"
        f"Previous artifacts:\n{context if context else '(none)'}\n\n"
        f"Required JSON schema:\n{json.dumps(schema, indent=2)}\n"
    )
