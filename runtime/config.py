from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    pass


def _deep_get(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


class Config:
    def __init__(self, path: Path, data: dict[str, Any], repo_root: Path):
        self.path = path
        self.data = data
        self.repo_root = repo_root

    @classmethod
    def load(cls, repo_root: Path, explicit: str | None = None) -> "Config":
        candidates = []
        if explicit:
            candidates.append(Path(explicit))
        candidates.extend([
            repo_root / ".multi-agent-cowork.toml",
            repo_root / ".agents" / "multi-agent-cowork" / "config" / "default.toml",
            Path(__file__).resolve().parent.parent / "config" / "default.toml",
        ])
        for candidate in candidates:
            if candidate.exists():
                with candidate.open("rb") as fh:
                    return cls(candidate, tomllib.load(fh), repo_root)
        raise ConfigError("No configuration file found.")

    @property
    def package_root(self) -> Path:
        repo_candidate = self.repo_root / ".agents" / "multi-agent-cowork"
        if repo_candidate.exists():
            return repo_candidate
        return self.path.parent.parent if self.path.parent.name == "config" else Path(__file__).resolve().parent.parent

    @property
    def state_dir(self) -> str:
        return _deep_get(self.data, "run", "state_dir", default=".multi-agent-cowork")

    @property
    def routing_memory_path(self) -> str:
        return _deep_get(self.data, "run", "routing_memory", default=".multi-agent-cowork/routing-memory.json")

    @property
    def known_failures_path(self) -> str:
        return _deep_get(self.data, "run", "known_failures", default=".multi-agent-cowork/known-failures.json")

    @property
    def max_parallel(self) -> int:
        return int(_deep_get(self.data, "run", "max_parallel", default=3))

    @property
    def fail_fast(self) -> bool:
        return bool(_deep_get(self.data, "run", "fail_fast", default=False))

    @property
    def default_profile(self) -> str:
        return str(_deep_get(self.data, "dispatch", "default_profile", default="balanced"))

    @property
    def verification_commands(self) -> list[str]:
        return list(_deep_get(self.data, "verification", "commands", default=[]))

    @property
    def stop_on_verify_failure(self) -> bool:
        return bool(_deep_get(self.data, "verification", "stop_on_failure", default=False))

    @property
    def rerun_failures_once(self) -> bool:
        return bool(_deep_get(self.data, "verification", "rerun_failures_once", default=True))

    @property
    def forbid_self_review(self) -> bool:
        return bool(_deep_get(self.data, "policies", "forbid_self_review", default=True))

    @property
    def require_shell_verifier(self) -> bool:
        return bool(_deep_get(self.data, "policies", "require_shell_verifier", default=True))

    @property
    def routing_profiles(self) -> dict[str, dict[str, Any]]:
        return dict(self.data.get("routing_profiles", {}))

    def routing_profile(self, name: str | None = None) -> dict[str, Any]:
        use = name or self.default_profile
        profiles = self.routing_profiles
        if use not in profiles:
            raise ConfigError(f"Unknown routing profile: {use}")
        return dict(profiles[use])

    def provider(self, name: str) -> dict[str, Any]:
        providers = self.data.get("providers", {})
        if name not in providers:
            raise ConfigError(f"Missing provider config for {name}")
        return dict(providers[name])

    def resolve_phase_providers(self, routing_memory: dict[str, Any] | None = None) -> dict[str, list[str]]:
        routing_memory = routing_memory or {}
        profile_name = routing_memory.get("profile") or self.default_profile
        profile = self.routing_profile(profile_name)
        resolved = {
            "explore": list(profile.get("explore_providers", [])),
            "plan": [profile["plan_provider"]] if profile.get("plan_provider") else [],
            "implement": [profile["implement_provider"]] if profile.get("implement_provider") else [],
            "verify": list(profile.get("verify_providers", [])),
            "review": list(profile.get("review_providers", [])),
        }
        overrides = routing_memory.get("overrides", {})
        for phase, providers in overrides.items():
            if phase in resolved:
                resolved[phase] = list(providers)
        self.validate_routing(resolved)
        return resolved

    def validate_routing(self, resolved: dict[str, list[str]]) -> None:
        implement = set(resolved.get("implement", []))
        review = set(resolved.get("review", []))
        if self.forbid_self_review and implement & review:
            raise ConfigError(f"Self-review forbidden by policy: implement={sorted(implement)} review={sorted(review)}")
        if self.require_shell_verifier and "shell" not in resolved.get("verify", []):
            raise ConfigError("Production policy requires `shell` in verify providers.")
