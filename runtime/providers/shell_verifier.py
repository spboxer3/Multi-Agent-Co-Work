from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from .base import Provider
from ..models import ProviderResult
from ..utils import ensure_dir, write_text


class ShellVerifierProvider(Provider):
    def invoke(self, *, role: str, phase: str, prompt: str, repo_root: Path, run_dir: Path, writable: bool, schema_path: Path) -> ProviderResult:
        provider_dir = ensure_dir(run_dir / phase / self.name)
        commands = list(self.config.get("commands", []))
        if not commands:
            return ProviderResult(provider=self.name, role=role, phase=phase, status="ok", summary="No verification commands configured.", decision="continue", confidence=0.2)
        summaries = []
        risks = []
        notes = []
        blockers = []
        classifications = []
        rerun_enabled = bool(self.config.get("rerun_failures_once", True))
        known_failures = self._load_known_failures(Path(self.config.get("known_failures_path", "")))
        start = time.time()
        failing = False
        for idx, command in enumerate(commands, start=1):
            proc = subprocess.run(command, cwd=repo_root, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=int(self.config.get("timeout_seconds", 1800)))
            write_text(provider_dir / f"cmd-{idx}.stdout.txt", proc.stdout)
            write_text(provider_dir / f"cmd-{idx}.stderr.txt", proc.stderr)
            outcome = "ok" if proc.returncode == 0 else f"failed({proc.returncode})"
            summaries.append(f"{command}: {outcome}")
            notes.append(f"{command}: {outcome}")
            if proc.returncode != 0:
                failing = True
                classification, extra_notes = self._classify_failure(command, proc.stdout + "\n" + proc.stderr, repo_root, rerun_enabled, known_failures, provider_dir, idx)
                classifications.append(f"{command}: {classification}")
                notes.extend(extra_notes)
                if classification == "task-caused":
                    risks.append(f"task-caused failure: {command}")
                    blockers.append(f"task-caused failure: {command}")
                elif classification == "pre-existing":
                    risks.append(f"pre-existing failure: {command}")
                elif classification == "flaky":
                    risks.append(f"flaky verification: {command}")
                elif classification == "infrastructure":
                    risks.append(f"infrastructure failure: {command}")
                if self.config.get("stop_on_failure", False) and classification == "task-caused":
                    break
        duration = time.time() - start
        status = "ok" if not failing or not blockers else "failed"
        decision = "continue" if status == "ok" else "rollback"
        return ProviderResult(provider=self.name, role=role, phase=phase, status=status, summary="; ".join(summaries), verification_commands=commands, commands=commands, failure_classification=classifications, risks=risks, notes=notes, blockers=blockers, decision=decision, confidence=0.9 if status == "ok" else 0.2, duration_seconds=duration)

    def _classify_failure(self, command: str, text: str, repo_root: Path, rerun_enabled: bool, known_failures: list[dict], provider_dir: Path, idx: int) -> tuple[str, list[str]]:
        notes: list[str] = []
        lower = text.lower()
        infrastructure_markers = ["permission denied", "network", "timed out", "timeout", "oom", "out of memory", "certificate", "registry", "dns"]
        if any(marker in lower for marker in infrastructure_markers):
            return "infrastructure", notes
        if rerun_enabled:
            rerun = subprocess.run(command, cwd=repo_root, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=int(self.config.get("timeout_seconds", 1800)))
            write_text(provider_dir / f"cmd-{idx}.rerun.stdout.txt", rerun.stdout)
            write_text(provider_dir / f"cmd-{idx}.rerun.stderr.txt", rerun.stderr)
            if rerun.returncode == 0:
                notes.append(f"rerun passed for {command}")
                return "flaky", notes
            notes.append(f"rerun failed for {command} with code {rerun.returncode}")
            text = text + "\n" + rerun.stdout + "\n" + rerun.stderr
            lower = text.lower()
        for item in known_failures:
            if command == item.get("command") or item.get("match_text", "").lower() in lower:
                notes.append(f"matched known failure id={item.get('id', 'unknown')}")
                return "pre-existing", notes
        return "task-caused", notes

    def _load_known_failures(self, path: Path) -> list[dict]:
        if not path or not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        return []
