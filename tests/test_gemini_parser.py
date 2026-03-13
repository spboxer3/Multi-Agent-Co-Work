from runtime.providers.gemini_cli import GeminiProvider


def test_extract_json_object_from_fenced_block():
    p = GeminiProvider("gemini", {})
    payload = p._extract_json_object("""```json
{"status":"ok","summary":"x","relevant_files":[],"proposed_changes":[],"commands":[],"risks":[],"notes":[],"open_questions":[],"blockers":[],"decision":"continue","confidence":0.5}
```""")
    assert payload["status"] == "ok"
    assert payload["decision"] == "continue"
