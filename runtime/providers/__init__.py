from .base import Provider
from .claude_code import ClaudeProvider
from .codex_cli import CodexProvider
from .gemini_cli import GeminiProvider
from .shell_verifier import ShellVerifierProvider


def provider_factory(name: str, config: dict) -> Provider:
    mapping = {
        "claude": ClaudeProvider,
        "codex": CodexProvider,
        "gemini": GeminiProvider,
        "shell": ShellVerifierProvider,
    }
    if name not in mapping:
        raise ValueError(f"Unknown provider: {name}")
    return mapping[name](name, config)
