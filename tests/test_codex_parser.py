import json

from runtime.providers.codex_cli import CodexProvider


def test_parse_jsonl_final_message():
    p = CodexProvider("codex", {})
    message = json.dumps({
        "status": "ok",
        "summary": "done",
        "relevant_files": [],
        "proposed_changes": [],
        "commands": [],
        "risks": [],
        "notes": [],
        "open_questions": [],
        "blockers": [],
        "decision": "continue",
        "confidence": 0.7,
    })
    text = "\n".join([
        json.dumps({"type": "thread.started"}),
        json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": message}}),
    ])
    payload = p._parse_jsonl_final(text)
    assert payload["summary"] == "done"
    assert payload["decision"] == "continue"
