from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class PhaseName(str, Enum):
    INTAKE = "intake"
    EXPLORE = "explore"
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    REVIEW = "review"
    REPORT = "report"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class ProviderResult:
    provider: str
    role: str
    phase: str
    status: str
    summary: str
    relevant_files: list[str] = field(default_factory=list)
    evidence_map: list[str] = field(default_factory=list)
    entrypoint_status: str = "unknown"
    entrypoint_direction: str = ""
    surface_coverage: float = 0.0
    proposed_changes: list[str] = field(default_factory=list)
    requested_files: list[str] = field(default_factory=list)
    file_set_mode: str = "unknown"
    verification_commands: list[str] = field(default_factory=list)
    failure_classification: list[str] = field(default_factory=list)
    scope_extension_needed: bool = False
    scope_extension_reason: str = ""
    rollback_anchor: str = ""
    commands: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    decision: str = "continue"
    confidence: float = 0.5
    raw_stdout_path: str | None = None
    raw_stderr_path: str | None = None
    output_path: str | None = None
    error: str | None = None
    duration_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunManifest:
    run_id: str
    task: str
    repo_root: str
    state_dir: str
    routing: dict[str, Any] = field(default_factory=dict)
    status: str = RunStatus.PENDING.value
    current_phase: str = PhaseName.INTAKE.value
    next_phase: str | None = None
    phases: dict[str, dict[str, Any]] = field(default_factory=dict)
    gates: dict[str, dict[str, Any]] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)
    started_at: str | None = None
    ended_at: str | None = None
    report_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
