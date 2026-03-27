import subprocess

from runtime.providers.claude_code import ClaudeProvider
from runtime.providers.codex_cli import CodexProvider
from runtime.providers.gemini_cli import GeminiProvider


class DummyLogger:
    def log(self, *_args, **_kwargs) -> None:
        pass


def test_gemini_timeout_non_streaming(monkeypatch, tmp_path):
    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="gemini", timeout=1, output="partial", stderr="err")

    monkeypatch.setattr(subprocess, "run", _raise_timeout)
    provider = GeminiProvider("gemini", {"streaming": False, "timeout_seconds": 1, "command": "gemini"})
    result = provider.invoke(
        role="implementer",
        phase="implement",
        prompt="hello",
        repo_root=tmp_path,
        run_dir=tmp_path,
        writable=False,
        schema_path=tmp_path / "schema.json",
    )
    assert result.status == "failed"
    assert "gemini-timeout" in result.blockers
    assert result.decision == "re-plan"


def test_gemini_timeout_with_streaming_config(monkeypatch, tmp_path):
    """Gemini no longer uses _run_streaming; verify timeout still works
    even when streaming=True in config (stdin pipe mode ignores it)."""
    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="gemini", timeout=1, output="partial", stderr="err")

    monkeypatch.setattr(subprocess, "run", _raise_timeout)
    provider = GeminiProvider("gemini", {"streaming": True, "timeout_seconds": 1, "command": "gemini"})
    provider.logger = DummyLogger()
    result = provider.invoke(
        role="implementer",
        phase="implement",
        prompt="hello",
        repo_root=tmp_path,
        run_dir=tmp_path,
        writable=False,
        schema_path=tmp_path / "schema.json",
    )
    assert result.status == "failed"
    assert "gemini-timeout" in result.blockers
    assert result.decision == "re-plan"


def test_claude_and_codex_timeout_non_streaming(monkeypatch, tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text("{}", encoding="utf-8")

    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="cli", timeout=1, output="partial", stderr="err")

    monkeypatch.setattr(subprocess, "run", _raise_timeout)

    claude = ClaudeProvider("claude", {"streaming": False, "timeout_seconds": 1, "command": "claude"})
    claude_result = claude.invoke(
        role="implementer",
        phase="implement",
        prompt="hello",
        repo_root=tmp_path,
        run_dir=tmp_path,
        writable=False,
        schema_path=schema_path,
    )
    assert claude_result.status == "failed"
    assert "claude-timeout" in claude_result.blockers

    codex = CodexProvider("codex", {"streaming": False, "timeout_seconds": 1, "command": "codex"})
    codex_result = codex.invoke(
        role="implementer",
        phase="implement",
        prompt="hello",
        repo_root=tmp_path,
        run_dir=tmp_path,
        writable=False,
        schema_path=schema_path,
    )
    assert codex_result.status == "failed"
    assert "codex-timeout" in codex_result.blockers
