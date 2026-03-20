from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .base import Provider
from ..models import ProviderResult
from ..utils import ensure_dir, write_text


class GeminiProvider(Provider):
    def invoke(self, *, role: str, phase: str, prompt: str, repo_root: Path, run_dir: Path, writable: bool, schema_path: Path) -> ProviderResult:
        if writable and self.config.get("read_only_only", True):
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Gemini writable invocation blocked by config.", error="read_only_only=true", blockers=["gemini-write-blocked"], decision="re-plan", confidence=0.0)
        provider_dir = ensure_dir(run_dir / phase / self.name)
        stdout_path = provider_dir / "stdout.json"
        stderr_path = provider_dir / "stderr.txt"
        write_text(provider_dir / "prompt.txt", prompt)
        gemini_bin = self._resolve_command(self.config.get("command", "gemini"))
        timeout_seconds = int(self.config.get("timeout_seconds", 1800))
        cmd = [gemini_bin, "-p", "Process the task from stdin.", "--output-format", "json"]
        cmd.extend(self.config.get("extra_args", []))
        streaming = self.config.get("streaming", False) and self.logger is not None
        start = time.time()
        if streaming:
            proc_rc, duration, timed_out = self._run_streaming(cmd, input_text=prompt, cwd=repo_root, stdout_path=stdout_path, stderr_path=stderr_path, timeout=timeout_seconds)
        else:
            import subprocess
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
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Gemini invocation timed out.", error=f"timeout after {timeout_seconds}s", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["gemini-timeout"], decision="re-plan", confidence=0.0)
        if proc_rc != 0:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Gemini invocation failed.", error=f"returncode={proc_rc}", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["gemini-returncode"], decision="re-plan", confidence=0.0)
        raw_stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else ""
        wrapper = self._parse_wrapper(raw_stdout)
        response_text = wrapper.get("response", "")
        payload = self._extract_json_object(response_text)
        if payload is None:
            payload = {"status": "failed", "summary": "Could not parse Gemini response JSON.", "relevant_files": [], "proposed_changes": [], "commands": [], "risks": ["gemini-parse-failure"], "notes": [response_text[:2000]], "open_questions": [], "blockers": ["gemini-parse-failure"], "decision": "re-plan", "confidence": 0.0}
        return self._result_from_payload(payload, provider=self.name, role=role, phase=phase, raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), output_path=str(stdout_path), duration_seconds=duration)

    def _parse_wrapper(self, text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
        return {"response": text}

    def _extract_json_object(self, text: str) -> dict[str, Any] | None:
        text = text.strip()
        if text.startswith("```"):
            lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
            text = "\n".join(lines).strip()
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
