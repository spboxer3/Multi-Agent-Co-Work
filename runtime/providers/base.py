from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ProviderResult


class Provider(ABC):
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def _resolve_command(self, cmd_name: str) -> str:
        """Resolve command name to full path (handles .CMD/.BAT on Windows)."""
        resolved = shutil.which(cmd_name)
        return resolved if resolved else cmd_name

    @staticmethod
    def _result_from_payload(payload: dict, *, provider: str, role: str, phase: str, raw_stdout_path: str | None = None, raw_stderr_path: str | None = None, output_path: str | None = None, duration_seconds: float | None = None) -> "ProviderResult":
        """Build a ProviderResult from an agent JSON payload, mapping all known fields."""
        from ..models import ProviderResult
        return ProviderResult(
            provider=provider, role=role, phase=phase,
            status=payload.get("status", "ok"),
            summary=payload.get("summary", ""),
            relevant_files=list(payload.get("relevant_files", [])),
            evidence_map=list(payload.get("evidence_map", [])),
            entrypoint_status=payload.get("entrypoint_status", "unknown"),
            entrypoint_direction=payload.get("entrypoint_direction", ""),
            surface_coverage=float(payload.get("surface_coverage", 0.0)),
            proposed_changes=list(payload.get("proposed_changes", [])),
            requested_files=list(payload.get("requested_files", [])),
            file_set_mode=payload.get("file_set_mode", "unknown"),
            verification_commands=list(payload.get("verification_commands", [])),
            failure_classification=list(payload.get("failure_classification", [])),
            scope_extension_needed=bool(payload.get("scope_extension_needed", False)),
            scope_extension_reason=payload.get("scope_extension_reason", ""),
            rollback_anchor=payload.get("rollback_anchor", ""),
            commands=list(payload.get("commands", [])),
            risks=list(payload.get("risks", [])),
            notes=list(payload.get("notes", [])),
            open_questions=list(payload.get("open_questions", [])),
            blockers=list(payload.get("blockers", [])),
            decision=payload.get("decision", "continue"),
            confidence=float(payload.get("confidence", 0.5)),
            raw_stdout_path=raw_stdout_path,
            raw_stderr_path=raw_stderr_path,
            output_path=output_path,
            duration_seconds=duration_seconds,
        )

    @abstractmethod
    def invoke(self, *, role: str, phase: str, prompt: str, repo_root: Path, run_dir: Path, writable: bool, schema_path: Path) -> ProviderResult:
        raise NotImplementedError
