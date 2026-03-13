from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import ProviderResult
from .utils import ensure_dir, write_json, write_text, read_text, utc_now

SCHEMA_VERSION = "1.1"


def create_run_layout(state_dir: Path, run_id: str) -> Path:
    run_dir = ensure_dir(state_dir / "runs" / run_id)
    for name in ["explore", "plan", "implement", "verify", "review", "handoffs"]:
        ensure_dir(run_dir / name)
    return run_dir


def write_provider_result(run_dir: Path, result: ProviderResult) -> Path:
    base = ensure_dir(run_dir / result.phase / result.provider)
    result_path = base / "result.json"
    write_json(result_path, result.to_dict())
    return result_path


def write_final_report(run_dir: Path, content: str) -> Path:
    path = run_dir / "final-report.md"
    write_text(path, content)
    return path


def context_snippet(paths: Iterable[Path], max_chars: int = 24000) -> str:
    blocks: list[str] = []
    remaining = max_chars
    for path in paths:
        text = read_text(path)
        if not text:
            continue
        chunk = text[:remaining]
        if not chunk:
            break
        blocks.append(f"## {path.name}\n{chunk}\n")
        remaining -= len(chunk)
        if remaining <= 0:
            break
    return "\n".join(blocks)


def _union(results: list[ProviderResult], attr: str) -> list[str]:
    items = []
    seen = set()
    for result in results:
        for value in getattr(result, attr):
            if value not in seen:
                seen.add(value)
                items.append(value)
    return items


def write_handoff(run_dir: Path, from_phase: str, to_phase: str, gate: dict, results: list[ProviderResult], routing: dict) -> Path:
    packet = {
        "packet_id": f"{from_phase}-to-{to_phase}",
        "schema_version": SCHEMA_VERSION,
        "from_phase": from_phase,
        "to_phase": to_phase,
        "created_at": utc_now(),
        "route_snapshot": routing,
        "gate": gate,
        "evidence_summary": {
            "relevant_files": _union(results, "relevant_files"),
            "evidence_map": _union(results, "evidence_map"),
            "entrypoint_status": max((r.entrypoint_status for r in results), key=lambda x: {"unknown": 0, "partial": 1, "confirmed": 2}.get(x, 0), default="unknown"),
            "entrypoint_directions": [r.entrypoint_direction for r in results if r.entrypoint_direction],
            "surface_coverage": max((r.surface_coverage for r in results), default=0.0),
            "test_surfaces": [x for x in _union(results, "relevant_files") if "test" in x.lower()],
        },
        "locked_context": {
            "proposed_changes": _union(results, "proposed_changes"),
            "requested_files": _union(results, "requested_files"),
            "file_set_mode": next((r.file_set_mode for r in results if r.file_set_mode != "unknown"), "unknown"),
            "verification_commands": _union(results, "verification_commands") or _union(results, "commands"),
            "rollback_anchor": next((r.rollback_anchor for r in results if r.rollback_anchor), ""),
            "scope_extension_needed": any(r.scope_extension_needed for r in results),
            "scope_extension_reasons": [r.scope_extension_reason for r in results if r.scope_extension_reason],
        },
        "unresolved": {
            "risks": _union(results, "risks"),
            "open_questions": _union(results, "open_questions"),
            "blockers": _union(results, "blockers"),
            "failure_classification": _union(results, "failure_classification"),
        },
        "required_actions": gate.get("required_actions", []),
        "provider_decisions": [
            {
                "provider": r.provider,
                "decision": r.decision,
                "confidence": r.confidence,
                "status": r.status,
                "summary": r.summary,
            }
            for r in results
        ],
        "intervention": {
            "owner": gate.get("owner"),
            "reason": gate.get("reason"),
            "recommended_next_phase": gate.get("recommended_next_phase", to_phase),
        },
    }
    path = run_dir / "handoffs" / f"{from_phase}-to-{to_phase}.json"
    write_json(path, packet)
    return path
