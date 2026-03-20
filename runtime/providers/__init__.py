from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Type

from .base import Provider
from .claude_code import ClaudeProvider
from .codex_cli import CodexProvider
from .gemini_cli import GeminiProvider
from .shell_verifier import ShellVerifierProvider

if TYPE_CHECKING:
    from ..streaming import LiveLogger


def provider_factory(name: str, config: dict, logger: "LiveLogger | None" = None) -> Provider:
    mapping: Dict[str, Type[Provider]] = {
        "claude": ClaudeProvider,
        "codex": CodexProvider,
        "gemini": GeminiProvider,
        "shell": ShellVerifierProvider,
    }
    if name not in mapping:
        raise ValueError(f"Unknown provider: {name}")
    return mapping[name](name, config, logger=logger)
