"""Live watcher — follows a run's live.log with colorized, formatted output."""
from __future__ import annotations

import sys
import time
from pathlib import Path

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"

PROVIDER_COLORS = {
    "claude": CYAN,
    "gemini": BLUE,
    "codex": MAGENTA,
    "shell": YELLOW,
}


def _colorize(line: str) -> str:
    """Apply color formatting to a log line."""
    # Phase banners
    if "═══" in line or "══════" in line:
        return f"{BOLD}{GREEN}{line}{RESET}"
    # Gate results
    if "── gate:" in line:
        if "PASSED" in line:
            return f"{BOLD}{GREEN}{line}{RESET}"
        if "FAILED" in line:
            return f"{BOLD}{RED}{line}{RESET}"
        return f"{BOLD}{YELLOW}{line}{RESET}"
    # Provider done
    if "] done (" in line:
        if "status=ok" in line:
            return f"{GREEN}{line}{RESET}"
        if "status=failed" in line:
            return f"{RED}{line}{RESET}"
        return f"{YELLOW}{line}{RESET}"
    # Provider decision/summary
    if "] decision=" in line:
        if "decision=continue" in line:
            return f"{BOLD}{GREEN}{line}{RESET}"
        if "decision=re-plan" in line or "decision=block-release" in line:
            return f"{BOLD}{RED}{line}{RESET}"
        return f"{BOLD}{YELLOW}{line}{RESET}"
    # Blockers
    if "] blockers:" in line:
        return f"{BOLD}{RED}{line}{RESET}"
    # Provider-prefixed lines
    for name, color in PROVIDER_COLORS.items():
        if f"[{name}]" in line:
            return f"{color}{line}{RESET}"
    # Timestamp-only info lines
    if line.startswith("["):
        return f"{DIM}{line}{RESET}"
    return line


def watch(log_path: Path, poll_interval: float = 0.3) -> None:
    """Tail-follow a live.log file with colored output."""
    title = f"MAW Live — {log_path.parent.name}"
    # Set terminal title on Windows and Unix
    sys.stdout.write(f"\033]0;{title}\007")
    sys.stdout.flush()

    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  MAW Live Watcher{RESET}")
    print(f"{DIM}  Watching: {log_path}{RESET}")
    print(f"{DIM}  Press Ctrl+C to stop{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}")
    print()

    pos = 0
    if log_path.exists():
        pos = log_path.stat().st_size

    # First, print existing content
    if pos > 0:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                print(_colorize(line.rstrip()))

    # Then follow new lines
    try:
        while True:
            if not log_path.exists():
                time.sleep(poll_interval)
                continue
            size = log_path.stat().st_size
            if size > pos:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(pos)
                    for line in f:
                        print(_colorize(line.rstrip()))
                    pos = f.tell()
            elif size < pos:
                # File was truncated (new run), reset
                pos = 0
                continue
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print(f"\n{DIM}Watcher stopped.{RESET}")
