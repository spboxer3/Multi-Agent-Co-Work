from __future__ import annotations

import json
import os
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
        cmd = [self._resolve_command(self.config.get("command", "claude")), "-p", "Process the task from stdin.", "--output-format", "json", "--json-schema", schema_text]
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
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        start = time.time()
        proc = subprocess.run(cmd, cwd=repo_root, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=int(self.config.get("timeout_seconds", 1800)), env=env)
        duration = time.time() - start
        write_text(stdout_path, proc.stdout)
        write_text(stderr_path, proc.stderr)
        if proc.returncode != 0:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Claude invocation failed.", error=f"returncode={proc.returncode}", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["claude-returncode"], decision="re-plan", confidence=0.0)
        try:
            raw = json.loads(proc.stdout)
            payload = raw.get("structured_output") or raw
        except json.JSONDecodeError:
            payload = {"status": "failed", "summary": "Could not parse Claude JSON output.", "relevant_files": [], "proposed_changes": [], "commands": [], "risks": ["claude-parse-failure"], "notes": [], "open_questions": [], "blockers": ["claude-parse-failure"], "decision": "re-plan", "confidence": 0.0}
        return self._result_from_payload(payload, provider=self.name, role=role, phase=phase, raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), output_path=str(stdout_path), duration_seconds=duration)
