from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .base import Provider
from ..models import ProviderResult
from ..utils import ensure_dir, write_text


class CodexProvider(Provider):
    def invoke(self, *, role: str, phase: str, prompt: str, repo_root: Path, run_dir: Path, writable: bool, schema_path: Path) -> ProviderResult:
        provider_dir = ensure_dir(run_dir / phase / self.name)
        stdout_path = provider_dir / "stdout.jsonl"
        stderr_path = provider_dir / "stderr.txt"
        output_path = provider_dir / "final.json"
        write_text(provider_dir / "prompt.txt", prompt)
        codex_bin = self._resolve_command(self.config.get("command", "codex"))
        cmd = [codex_bin, "exec", "--json", "--output-schema", str(schema_path), "-o", str(output_path)]
        model = self.config.get("model")
        if model:
            cmd += ["--model", model]
        if self.config.get("no_sandbox", False):
            cmd.append("--dangerously-bypass-approvals-and-sandbox")
        elif writable:
            if self.config.get("full_auto", True):
                cmd.append("--full-auto")
            cmd += ["--sandbox", self.config.get("sandbox_write", "workspace-write")]
        else:
            cmd += ["--sandbox", self.config.get("sandbox_read_only", "read-only")]
        cmd.extend(self.config.get("extra_args", []))
        cmd.append("-")
        streaming = self.config.get("streaming", False) and self.logger is not None
        start = time.time()
        if streaming:
            timeout_seconds = int(self.config.get("timeout_seconds", 2400))
            proc_rc, duration, timed_out = self._run_streaming(cmd, input_text=prompt, cwd=repo_root, stdout_path=stdout_path, stderr_path=stderr_path, timeout=timeout_seconds)
        else:
            import subprocess
            timeout_seconds = int(self.config.get("timeout_seconds", 2400))
            try:
                proc = subprocess.run(cmd, cwd=repo_root, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds)
                duration = time.time() - start
                proc_rc = proc.returncode
                write_text(stdout_path, proc.stdout)
                write_text(stderr_path, proc.stderr)
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                duration = time.time() - start
                timed_out = True
                proc_rc = -1
                write_text(stdout_path, exc.output or "")
                write_text(stderr_path, exc.stderr or "")
        if timed_out:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Codex invocation timed out.", error=f"timeout after {timeout_seconds}s", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["codex-timeout"], decision="re-plan", confidence=0.0)
        if proc_rc != 0:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Codex invocation failed.", error=f"returncode={proc_rc}", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration)
        payload = None
        if output_path.exists():
            try:
                payload = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = None
        if payload is None:
            raw_stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
            payload = self._parse_jsonl_final(raw_stdout)
        return self._result_from_payload(payload, provider=self.name, role=role, phase=phase, raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), output_path=str(output_path) if output_path.exists() else None, duration_seconds=duration)

    def _parse_jsonl_final(self, text: str) -> dict[str, Any]:
        last_message = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = obj.get("item") or {}
            if obj.get("type") == "item.completed" and item.get("type") == "agent_message":
                msg_text = item.get("text")
                if isinstance(msg_text, str):
                    last_message = msg_text
        if last_message:
            payload = self._extract_json_object(last_message)
            if payload is not None:
                return payload
        return {"status": "failed", "summary": "Could not parse Codex final output.", "relevant_files": [], "proposed_changes": [], "commands": [], "risks": ["codex-parse-failure"], "notes": [], "open_questions": [], "blockers": ["codex-parse-failure"], "decision": "re-plan", "confidence": 0.0}

    def _extract_json_object(self, text: str) -> dict[str, Any] | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    return None
            return None
