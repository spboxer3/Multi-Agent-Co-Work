from __future__ import annotations

import json
import subprocess
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
        cmd = [self.config.get("command", "codex"), "exec", "--json", "--output-schema", str(schema_path), "-o", str(output_path)]
        model = self.config.get("model")
        if model:
            cmd += ["--model", model]
        if writable:
            if self.config.get("full_auto", True):
                cmd.append("--full-auto")
            cmd += ["--sandbox", self.config.get("sandbox_write", "workspace-write")]
        else:
            cmd += ["--sandbox", self.config.get("sandbox_read_only", "read-only")]
        start = time.time()
        proc = subprocess.run(cmd + [prompt], cwd=repo_root, capture_output=True, text=True, timeout=int(self.config.get("timeout_seconds", 2400)))
        duration = time.time() - start
        write_text(stdout_path, proc.stdout)
        write_text(stderr_path, proc.stderr)
        if proc.returncode != 0:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="failed", summary="Codex invocation failed.", error=f"returncode={proc.returncode}", raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), duration_seconds=duration)
        payload = None
        if output_path.exists():
            try:
                payload = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = None
        if payload is None:
            payload = self._parse_jsonl_final(proc.stdout)
        return ProviderResult(provider=self.name, role=role, phase=phase, status=payload.get("status", "ok"), summary=payload.get("summary", ""), relevant_files=list(payload.get("relevant_files", [])), proposed_changes=list(payload.get("proposed_changes", [])), commands=list(payload.get("commands", [])), risks=list(payload.get("risks", [])), notes=list(payload.get("notes", [])), open_questions=list(payload.get("open_questions", [])), blockers=list(payload.get("blockers", [])), decision=payload.get("decision", "continue"), confidence=float(payload.get("confidence", 0.5)), raw_stdout_path=str(stdout_path), raw_stderr_path=str(stderr_path), output_path=str(output_path) if output_path.exists() else None, duration_seconds=duration)

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
