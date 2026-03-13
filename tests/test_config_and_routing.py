from pathlib import Path

from runtime.config import Config
from runtime.routing_memory import save, load, clear, parse_phase_specs


def _write_cfg(repo: Path):
    (repo / '.agents' / 'multi-agent-cowork' / 'config').mkdir(parents=True)
    (repo / '.agents' / 'multi-agent-cowork' / 'config' / 'default.toml').write_text(
        '''
[run]
state_dir = ".multi-agent-cowork"
routing_memory = ".multi-agent-cowork/routing-memory.json"
known_failures = ".multi-agent-cowork/known-failures.json"

[dispatch]
default_profile = "balanced"

[routing_profiles.balanced]
explore_providers=["claude","gemini"]
plan_provider="claude"
implement_provider="codex"
verify_providers=["shell","claude"]
review_providers=["claude","gemini"]

[routing_profiles.recovery]
explore_providers=["claude","gemini"]
plan_provider="claude"
implement_provider="codex"
verify_providers=["shell","claude","gemini"]
review_providers=["claude","gemini"]

[policies]
forbid_self_review = true
require_shell_verifier = true

[providers.claude]
command="claude"
[providers.gemini]
command="gemini"
[providers.codex]
command="codex"
[providers.shell]
command="sh"
''',
        encoding='utf-8'
    )


def test_load_default_and_resolve(tmp_path: Path):
    repo = tmp_path
    _write_cfg(repo)
    cfg = Config.load(repo)
    resolved = cfg.resolve_phase_providers({})
    assert resolved["implement"] == ["codex"]
    assert "shell" in resolved["verify"]
    assert "recovery" in cfg.routing_profiles


def test_routing_memory_roundtrip(tmp_path: Path):
    repo = tmp_path
    _write_cfg(repo)
    cfg = Config.load(repo)
    path = save(repo, cfg, profile="balanced", overrides={"review": ["claude", "gemini"]}, note="x")
    assert path.exists()
    memory = load(repo, cfg)
    assert memory["profile"] == "balanced"
    assert memory["overrides"]["review"] == ["claude", "gemini"]
    clear(repo, cfg)
    assert not path.exists()


def test_parse_phase_specs():
    parsed = parse_phase_specs(["implement=codex", "review=claude,gemini", "planner=claude"])
    assert parsed["implement"] == ["codex"]
    assert parsed["review"] == ["claude", "gemini"]
    assert parsed["plan"] == ["claude"]


def test_self_review_policy_blocks_same_provider(tmp_path: Path):
    repo = tmp_path
    _write_cfg(repo)
    cfg = Config.load(repo)
    try:
        cfg.resolve_phase_providers({"overrides": {"review": ["codex"]}})
    except Exception as exc:
        assert "Self-review forbidden" in str(exc)
    else:
        raise AssertionError("Expected self-review validation to fail")
