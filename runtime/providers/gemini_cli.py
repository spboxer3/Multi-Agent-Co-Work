from __future__ import annotations

import json
import subprocess
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
        cmd = [self.config.get("command", "gemini"), "-p", prompt, "--output-format", "json"]
        cmd.extend(self.config.get("extra_args", []))
        start = time.time()
        proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, timeout=int(self.config.get("timeout_seconds", 1800)))
        duration = time.time() - start
        write_text(stdout_path, proc.stdout)
        write_text(stderr_path, proc.stderr)
        if proc.returncode != 0:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Gemini invocation failed.", error=f"returncode={proc.returncode}", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration, blockers=["gemini-returncode"], decision="re-plan", confidence=0.0)
        wrapper = self._parse_wrapper(proc.stdout)
        response_text = wrapper.get("response", "")
        payload = self._extract_json_object(response_text)
        if payload is None:
            payload = {"status": "failed", "summary": "Could not parse Gemini response JSON.", "relevant_files": [], "proposed_changes": [], "commands": [], "risks": ["gemini-parse-failure"], "notes": [response_text[:2000]], "open_questions": [], "blockers": ["gemini-parse-failure"], "decision": "re-plan", "confidence": 0.0}
        return ProviderResult(provider=self.name, role=role, phase=phase, status=payload.get("status", "ok"), summary=payload.get("summary", ""), relevant_files=list(payload.get("relevant_files", [])), proposed_changes=list(payload.get("proposed_changes", [])), commands=list(payload.get("commands", [])), risks=list(payload.get("risks", [])), notes=list(payload.get("notes", [])), open_questions=list(payload.get("open_questions", [])), blockers=list(payload.get("blockers", [])), decision=payload.get("decision", "continue"), confidence=float(payload.get("confidence", 0.5)), raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), output_path=str(stdout_path), duration_seconds=duration)

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
