from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from .base import Provider
from ..models import ProviderResult
from ..utils import ensure_dir, write_text


class ClaudeProvider(Provider):
    def invoke(self, *, role: str, phase: str, prompt: str, repo_root: Path, run_dir: Path, writable: bool, schema_path: Path) -> ProviderResult:
        provider_dir = ensure_dir(run_dir / phase / self.name)
        stdout_path = provider_dir / "stdout.json"
        stderr_path = provider_dir / "stderr.txt"
        schema_text = schema_path.read_text(encoding="utf-8")
        cmd = [self.config.get("command", "claude"), "-p", prompt, "--output-format", "json", "--json-schema", schema_text]
        model = self.config.get("model")
        if model:
            cmd += ["--model", model]
        if not writable:
            permission_mode = self.config.get("read_only_permission_mode")
            if permission_mode:
                cmd += ["--permission-mode", permission_mode]
        elif self.config.get("allow_unattended_write", False):
            cmd.append("--dangerously-skip-permissions")
        else:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Claude writable invocation blocked by config.", error="allow_unattended_write=false", blockers=["claude-write-blocked"], decision="re-plan", confidence=0.0)
        start = time.time()
        proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, timeout=int(self.config.get("timeout_seconds", 1800)))
        duration = time.time() - start
        write_text(stdout_path, proc.stdout)
        write_text(stderr_path, proc.stderr)
        if proc.returncode != 0:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Claude invocation failed.", error=f"returncode={proc.returncode}", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["claude-returncode"], decision="re-plan", confidence=0.0)
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"status": "failed", "summary": "Could not parse Claude JSON output.", "relevant_files": [], "proposed_changes": [], "commands": [], "risks": ["claude-parse-failure"], "notes": [], "open_questions": [], "blockers": ["claude-parse-failure"], "decision": "re-plan", "confidence": 0.0}
        return ProviderResult(provider=self.name, role=role, phase=phase, status=payload.get("status", "ok"), summary=payload.get("summary", ""), relevant_files=list(payload.get("relevant_files", [])), proposed_changes=list(payload.get("proposed_changes", [])), commands=list(payload.get("commands", [])), risks=list(payload.get("risks", [])), notes=list(payload.get("notes", [])), open_questions=list(payload.get("open_questions", [])), blockers=list(payload.get("blockers", [])), decision=payload.get("decision", "continue"), confidence=float(payload.get("confidence", 0.5)), raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), output_path=str(stdout_path), duration_seconds=duration)
