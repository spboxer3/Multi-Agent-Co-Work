from pathlib import Path
from runtime.config import Config


def test_load_default_from_repo(tmp_path: Path):
    repo = tmp_path
    (repo / '.agents' / 'multi-agent-cowork' / 'config').mkdir(parents=True)
    (repo / '.agents' / 'multi-agent-cowork' / 'config' / 'default.toml').write_text(
        """[run]
state_dir = ".multi-agent-cowork"
[dispatch]
explore_providers=["claude"]
[providers.claude]
command="claude"
""",
        encoding='utf-8'
    )
    cfg = Config.load(repo)
    assert cfg.state_dir == '.multi-agent-cowork'
