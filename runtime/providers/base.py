from __future__ import annotations

import shutil
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from ..models import ProviderResult
from ..utils import write_text

if TYPE_CHECKING:
    from ..streaming import LiveLogger


class Provider(ABC):
    def __init__(self, name: str, config: dict, logger: "LiveLogger | None" = None):
        self.name = name
        self.config = config
        self.logger = logger

    def _resolve_command(self, cmd_name: str) -> str:
        """Resolve command name to full path (handles .CMD/.BAT on Windows)."""
        resolved = shutil.which(cmd_name)
        return resolved if resolved else cmd_name

    def _run_streaming(
        self,
        cmd: list[str],
        *,
        input_text: str,
        cwd: Path,
        stdout_path: Path,
        stderr_path: Path,
        timeout: int = 1800,
        env: dict | None = None,
    ) -> tuple[int, float, bool]:
        """Run a subprocess with real-time streaming to LiveLogger and file capture."""
        logger = self.logger
        if logger:
            logger.log(self.name, f"starting: {' '.join(cmd[:3])}...")

        start = time.time()
        timed_out = False
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env,
        )

        # Write prompt to stdin
        if input_text and proc.stdin:
            try:
                proc.stdin.write(input_text.encode("utf-8"))
            except OSError:
                pass
            finally:
                proc.stdin.close()

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def _read_stream(stream, collector: list[str], is_stderr: bool = False) -> None:
            for raw_line in stream:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\n\r")
                collector.append(line)
                if logger and is_stderr and line.strip():
                    logger.log(self.name, line)

        t_out = threading.Thread(target=_read_stream, args=(proc.stdout, stdout_lines, False), daemon=True)
        t_err = threading.Thread(target=_read_stream, args=(proc.stderr, stderr_lines, True), daemon=True)
        t_out.start()
        t_err.start()

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            proc.wait(timeout=10)

        t_out.join(timeout=5)
        t_err.join(timeout=5)

        duration = time.time() - start
        write_text(stdout_path, "\n".join(stdout_lines))
        write_text(stderr_path, "\n".join(stderr_lines))
        return proc.returncode, duration, timed_out

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
