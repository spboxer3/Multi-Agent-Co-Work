from runtime.artifacts import create_run_layout, write_handoff
from runtime.models import ProviderResult


def test_write_handoff_has_locked_context_and_intervention(tmp_path):
    run_dir = create_run_layout(tmp_path, "run-1")
    results = [
        ProviderResult(provider="claude", role="explorer", phase="explore", status="ok", summary="found files", relevant_files=["a.py"], evidence_map=["a.py::Foo.bar::entrypoint"], entrypoint_status="confirmed", entrypoint_direction="inbound", surface_coverage=0.8, open_questions=["why"], decision="continue", confidence=0.8),
        ProviderResult(provider="gemini", role="explorer", phase="explore", status="ok", summary="found test", relevant_files=["tests/test_a.py"], evidence_map=["tests/test_a.py::test_bar::likely verification"], entrypoint_status="partial", entrypoint_direction="outbound", surface_coverage=0.6, blockers=["unknown side effect"], decision="re-explore", confidence=0.4),
    ]
    gate = {"passed": False, "missing": ["explorer requested re-explore"], "decisions": ["continue", "re-explore"], "blockers": ["unknown side effect"], "owner": "explorer", "reason": "explore evidence not yet converged", "required_actions": ["identify one likely test surface"], "recommended_next_phase": "explore"}
    routing = {"explore": ["claude", "gemini"], "plan": ["claude"]}
    path = write_handoff(run_dir, "explore", "plan", gate, results, routing)
    text = path.read_text(encoding="utf-8")
    assert '"packet_id": "explore-to-plan"' in text
    assert '"locked_context"' in text
    assert '"recommended_next_phase": "explore"' in text
    assert '"a.py::Foo.bar::entrypoint"' in text
