from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Config
from .utils import read_json, write_json, utc_now

ROLE_ALIAS = {
    "explorer": "explore",
    "planner": "plan",
    "plan": "plan",
    "implementer": "implement",
    "implement": "implement",
    "verifier": "verify",
    "verify": "verify",
    "reviewer": "review",
    "review": "review",
}

DEFAULT_MEMORY: dict[str, Any] = {
    "version": 1,
    "profile": None,
    "overrides": {},
    "updated_at": None,
    "note": "",
}


def path_for(repo_root: Path, config: Config) -> Path:
    return repo_root / config.routing_memory_path


def load(repo_root: Path, config: Config) -> dict[str, Any]:
    path = path_for(repo_root, config)
    if not path.exists():
        return dict(DEFAULT_MEMORY)
    data = read_json(path)
    merged = dict(DEFAULT_MEMORY)
    merged.update(data)
    merged["overrides"] = dict(data.get("overrides", {}))
    return merged


def save(repo_root: Path, config: Config, profile: str | None, overrides: dict[str, list[str]] | None, note: str | None = None) -> Path:
    current = load(repo_root, config)
    if profile is not None:
        current["profile"] = profile
    if overrides:
        current["overrides"].update(overrides)
    if note is not None:
        current["note"] = note
    current["updated_at"] = utc_now()
    path = path_for(repo_root, config)
    write_json(path, current)
    return path


def clear(repo_root: Path, config: Config) -> Path:
    path = path_for(repo_root, config)
    if path.exists():
        path.unlink()
    return path


def parse_phase_specs(specs: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"Invalid phase spec: {spec}")
        left, right = spec.split("=", 1)
        phase = ROLE_ALIAS.get(left.strip())
        if not phase:
            raise ValueError(f"Unknown phase or role: {left}")
        providers = [item.strip() for item in right.split(",") if item.strip()]
        if not providers:
            raise ValueError(f"No providers specified for {phase}")
        result[phase] = providers
    return result
