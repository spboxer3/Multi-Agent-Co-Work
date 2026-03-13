from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ProviderResult


class Provider(ABC):
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    @abstractmethod
    def invoke(self, *, role: str, phase: str, prompt: str, repo_root: Path, run_dir: Path, writable: bool, schema_path: Path) -> ProviderResult:
        raise NotImplementedError
