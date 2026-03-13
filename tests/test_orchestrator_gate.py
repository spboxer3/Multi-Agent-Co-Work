from runtime.config import Config
from runtime.models import ProviderResult
from runtime.orchestrator import Orchestrator


def test_explore_gate_requires_coverage_and_entrypoint(tmp_path):
    (tmp_path / '.agents' / 'multi-agent-cowork' / 'config').mkdir(parents=True)
    (tmp_path / '.agents' / 'multi-agent-cowork' / 'schemas').mkdir(parents=True)
    (tmp_path / '.agents' / 'multi-agent-cowork' / 'schemas' / 'agent_result.schema.json').write_text('{"type": "object", "properties": {}, "required": []}', encoding='utf-8')
    (tmp_path / '.agents' / 'multi-agent-cowork' / 'config' / 'default.toml').write_text(
        '''
[dispatch]
default_profile="balanced"
[routing_profiles.balanced]
explore_providers=["claude"]
plan_provider="claude"
implement_provider="codex"
verify_providers=["shell"]
review_providers=["claude"]
[policies]
forbid_self_review=true
require_shell_verifier=true
[providers.claude]
command="claude"
[providers.codex]
command="codex"
[providers.shell]
command="sh"
''',
        encoding='utf-8'
    )
    cfg = Config.load(tmp_path)
    orch = Orchestrator(tmp_path, cfg)
    gate = orch._evaluate_gate('explore', [ProviderResult(provider='claude', role='explorer', phase='explore', status='ok', summary='x', entrypoint_status='partial', surface_coverage=0.5, decision='continue')])
    assert not gate['passed']
    assert gate['recommended_next_phase'] == 'explore'
