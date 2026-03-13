import json
from pathlib import Path

from runtime.providers.shell_verifier import ShellVerifierProvider


def test_shell_verifier_classifies_known_failure(tmp_path: Path):
    provider = ShellVerifierProvider("shell", {
        "commands": ["python -c 'import sys; sys.exit(1)'"] ,
        "timeout_seconds": 10,
        "rerun_failures_once": False,
        "known_failures_path": str(tmp_path / "known.json"),
    })
    (tmp_path / "known.json").write_text(json.dumps([{"id": "x", "command": "python -c 'import sys; sys.exit(1)'"}]), encoding="utf-8")
    result = provider.invoke(role="verifier", phase="verify", prompt="", repo_root=tmp_path, run_dir=tmp_path, writable=False, schema_path=tmp_path / "none.json")
    assert any("pre-existing" in x for x in result.failure_classification)
