from __future__ import annotations

import json
import os
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
        write_text(provider_dir / "prompt.txt", prompt)
        schema_text = schema_path.read_text(encoding="utf-8")
        claude_bin = self._resolve_command(self.config.get("command", "claude"))
        cmd = [claude_bin, "-p", "Process the task from stdin.", "--output-format", "json", "--json-schema", schema_text]
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
        streaming = self.config.get("streaming", False) and self.logger is not None
        start = time.time()
        if streaming:
            timeout_seconds = int(self.config.get("timeout_seconds", 1800))
            proc_rc, duration, timed_out = self._run_streaming(cmd, input_text=prompt, cwd=repo_root, stdout_path=stdout_path, stderr_path=stderr_path, timeout=timeout_seconds, env=env)
        else:
            import subprocess
            timeout_seconds = int(self.config.get("timeout_seconds", 1800))
            try:
                proc = subprocess.run(cmd, cwd=repo_root, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds, env=env)
                duration = time.time() - start
                proc_rc = proc.returncode
                write_text(stdout_path, proc.stdout)
                write_text(stderr_path, proc.stderr)
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                duration = time.time() - start
                timed_out = True
                proc_rc = -1
                write_text(stdout_path, str(exc.output or ""))
                write_text(stderr_path, str(exc.stderr or ""))
        if timed_out:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Claude invocation timed out.", error=f"timeout after {timeout_seconds}s", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["claude-timeout"], decision="re-plan", confidence=0.0)
        if proc_rc != 0:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Claude invocation failed.", error=f"returncode={proc_rc}", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["claude-returncode"], decision="re-plan", confidence=0.0)
        raw_stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
        try:
            raw = json.loads(raw_stdout)
            payload = raw.get("structured_output") or raw
        except json.JSONDecodeError:
            payload = {"status": "failed", "summary": "Could not parse Claude JSON output.", "relevant_files": [], "proposed_changes": [], "commands": [], "risks": ["claude-parse-failure"], "notes": [], "open_questions": [], "blockers": ["claude-parse-failure"], "decision": "re-plan", "confidence": 0.0}
        return self._result_from_payload(payload, provider=self.name, role=role, phase=phase, raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), output_path=str(stdout_path), duration_seconds=duration)
