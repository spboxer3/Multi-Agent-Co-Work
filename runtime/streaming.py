from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path


class LiveLogger:
    """Thread-safe logger that writes timestamped, provider-prefixed lines to a log file and stderr."""

    def __init__(self, path: Path, *, console: bool = False):
        self.path = path
        self._console = console
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def _ts(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def _write(self, line: str) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
            if self._console:
                import sys
                try:
                    sys.stderr.write(line + "\n")
                    sys.stderr.flush()
                except OSError:
                    pass

    def log(self, provider: str, text: str) -> None:
        for line in text.splitlines():
            self._write(f"[{self._ts()}] [{provider}] {line}")

    def phase_banner(self, phase: str, providers: list[str]) -> None:
        names = ", ".join(providers)
        self._write(f"\n[{self._ts()}] {'═' * 6} {phase.upper()} {'═' * 6} providers: [{names}]")

    def gate_result(self, phase: str, passed: bool, missing: list[str] | None = None) -> None:
        status = "PASSED" if passed else "FAILED"
        line = f"[{self._ts()}] ── gate: {phase} → {status} ──"
        if missing:
            line += f" missing: {missing}"
        self._write(line)

    def provider_done(self, provider: str, duration: float, status: str) -> None:
        self._write(f"[{self._ts()}] [{provider}] done ({duration:.1f}s, status={status})")

    def provider_summary(self, provider: str, decision: str, confidence: float, summary: str) -> None:
        self._write(f"[{self._ts()}] [{provider}] decision={decision} confidence={confidence:.2f}")
        # Wrap long summaries at ~100 chars per line for readability
        words = summary.split()
        line = ""
        for w in words:
            if len(line) + len(w) + 1 > 100:
                self._write(f"[{self._ts()}] [{provider}]   {line}")
                line = w
            else:
                line = f"{line} {w}" if line else w
        if line:
            self._write(f"[{self._ts()}] [{provider}]   {line}")

    def info(self, message: str) -> None:
        self._write(f"[{self._ts()}] {message}")
