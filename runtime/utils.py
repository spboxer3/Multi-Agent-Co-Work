from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def atomic_write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    import sys
    if sys.platform == "win32":
        path.write_text(content, encoding="utf-8")
    else:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)


def write_text(path: Path, content: str) -> None:
    atomic_write_text(path, content)


def write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_slug(text: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    text = text.lower().replace(" ", "-")
    out = []
    for ch in text:
        out.append(ch if ch in allowed else "-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "run"


def new_run_id(task: str) -> str:
    return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{safe_slug(task)[:24]}"
