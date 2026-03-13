from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from .artifacts import create_run_layout, write_provider_result, write_final_report, write_handoff
from .config import Config
from .models import PhaseName, ProviderResult, RunManifest, RunStatus
from .prompting import build_prompt
from .providers import provider_factory
from .routing_memory import load as load_routing_memory
from .state_machine import StateMachine, NEXT_PHASE, RECOMMENDED_NEXT
from .utils import ensure_dir, new_run_id, utc_now, write_json, write_text, read_json


class Orchestrator:
    def __init__(self, repo_root: Path, config: Config):
        self.repo_root = repo_root
        self.config = config
        self.state_root = ensure_dir(repo_root / config.state_dir)
        self.package_root = config.package_root
        self.schema_path = self.package_root / "schemas" / "agent_result.schema.json"
        self.schema = json.loads(self.schema_path.read_text(encoding="utf-8"))

    def dispatch(self, task: str, run_id: str | None = None, phase_limit: str | None = None, start_phase: str | None = None) -> Path:
        routing_memory = load_routing_memory(self.repo_root, self.config)
        routing = self.config.resolve_phase_providers(routing_memory)
        run_id = run_id or new_run_id(task)
        run_dir = create_run_layout(self.state_root, run_id)
        manifest_path = run_dir / "manifest.json"
        if manifest_path.exists():
            prior = read_json(manifest_path)
            manifest = RunManifest(**prior)
            manifest.status = RunStatus.RUNNING.value
        else:
            manifest = RunManifest(run_id=run_id, task=task, repo_root=str(self.repo_root), state_dir=str(self.state_root), routing={"memory": routing_memory, "resolved": routing}, started_at=utc_now(), status=RunStatus.RUNNING.value)
        machine = StateMachine(current=PhaseName.INTAKE.value if not start_phase else start_phase)
        self._save_manifest(run_dir, manifest)
        write_text(self.state_root / "latest-run.txt", run_id + "\n")
        write_json(run_dir / "routing.json", manifest.routing)
        manifest.artifacts["routing"] = str(run_dir / "routing.json")
        write_json(run_dir / "intake.json", {"task": task, "created_at": utc_now()})
        manifest.artifacts["intake"] = str(run_dir / "intake.json")
        self._save_manifest(run_dir, manifest)

        phases = ["explore", "plan", "implement", "verify", "review"]
        if start_phase and start_phase in phases:
            phases = phases[phases.index(start_phase):]
        if phase_limit and phase_limit in phases:
            phases = phases[: phases.index(phase_limit) + 1]

        overall_failures: list[ProviderResult] = []
        stopped_early = False
        for phase in phases:
            machine.advance(phase)
            manifest.current_phase = phase
            manifest.next_phase = NEXT_PHASE.get(phase)
            self._save_manifest(run_dir, manifest)
            results = self._run_phase(run_dir, task, phase, routing)
            manifest.phases[phase] = {"providers": [r.to_dict() for r in results], "completed_at": utc_now()}
            summary_path = run_dir / f"{phase}-summary.md"
            write_text(summary_path, self._phase_summary(results))
            manifest.artifacts[f"{phase}-summary"] = str(summary_path)
            gate = self._evaluate_gate(phase, results)
            manifest.gates[phase] = gate
            if phase in NEXT_PHASE:
                handoff_path = write_handoff(run_dir, phase, NEXT_PHASE[phase], gate, results, routing)
                manifest.artifacts[f"handoff:{phase}:{NEXT_PHASE[phase]}"] = str(handoff_path)
            self._save_manifest(run_dir, manifest)
            phase_failures = [r for r in results if r.status == "failed"]
            if phase_failures:
                overall_failures.extend(phase_failures)
            if not gate["passed"]:
                manifest.next_phase = gate.get("recommended_next_phase")
                stopped_early = True
                self._save_manifest(run_dir, manifest)
                break
            if phase_failures and self.config.fail_fast:
                stopped_early = True
                break

        manifest.current_phase = PhaseName.REPORT.value
        report_text = self._final_report(manifest)
        report_path = write_final_report(run_dir, report_text)
        manifest.report_path = str(report_path)
        manifest.artifacts["final-report"] = str(report_path)
        manifest.ended_at = utc_now()
        total_provider_runs = sum(len(v.get("providers", [])) for v in manifest.phases.values())
        if stopped_early and (overall_failures or manifest.next_phase):
            manifest.status = RunStatus.PARTIAL.value if manifest.next_phase else RunStatus.FAILED.value
        elif overall_failures and len(overall_failures) == total_provider_runs:
            manifest.status = RunStatus.FAILED.value
        elif overall_failures:
            manifest.status = RunStatus.PARTIAL.value
        else:
            manifest.status = RunStatus.COMPLETED.value
        self._save_manifest(run_dir, manifest)
        return run_dir

    def resume(self, run_id: str) -> Path:
        run_dir = self.state_root / "runs" / run_id
        manifest = read_json(run_dir / "manifest.json")
        status = manifest.get("status")
        if status == RunStatus.COMPLETED.value:
            return run_dir
        task = manifest["task"]
        start_phase = manifest.get("next_phase")
        if not start_phase:
            completed_phases = set(manifest.get("phases", {}).keys())
            phases = ["explore", "plan", "implement", "verify", "review"]
            remaining = [p for p in phases if p not in completed_phases]
            if not remaining:
                return run_dir
            start_phase = remaining[0]
        return self.dispatch(task=task, run_id=run_id, start_phase=start_phase)

    def status(self, run_id: str) -> dict:
        run_dir = self.state_root / "runs" / run_id
        return read_json(run_dir / "manifest.json")

    def _run_phase(self, run_dir: Path, task: str, phase: str, routing: dict[str, list[str]]) -> list[ProviderResult]:
        providers = routing.get(phase, [])
        results: list[ProviderResult] = []
        parallel = phase in {"explore", "review", "verify"} and len(providers) > 1
        if parallel:
            with ThreadPoolExecutor(max_workers=min(len(providers), self.config.max_parallel)) as pool:
                future_map = {pool.submit(self._invoke_provider, provider, phase, task, run_dir): provider for provider in providers}
                for fut in as_completed(future_map):
                    result = fut.result()
                    write_provider_result(run_dir, result)
                    results.append(result)
        else:
            for provider in providers:
                result = self._invoke_provider(provider, phase, task, run_dir)
                write_provider_result(run_dir, result)
                results.append(result)
        return results

    def _invoke_provider(self, provider_name: str, phase: str, task: str, run_dir: Path) -> ProviderResult:
        cfg = self.config.provider(provider_name)
        if provider_name == "shell":
            cfg["commands"] = self.config.verification_commands
            cfg["stop_on_failure"] = self.config.stop_on_verify_failure
            cfg["rerun_failures_once"] = self.config.rerun_failures_once
            cfg["known_failures_path"] = str(self.repo_root / self.config.known_failures_path)
        writable = phase == PhaseName.IMPLEMENT.value
        prompt = build_prompt(provider=provider_name, role=self._role_for_phase(phase, provider_name), phase=phase, task=task, repo_root=self.repo_root, run_dir=run_dir, package_root=self.package_root, writable=writable, schema=self.schema)
        provider = provider_factory(provider_name, cfg)
        return provider.invoke(role=self._role_for_phase(phase, provider_name), phase=phase, prompt=prompt, repo_root=self.repo_root, run_dir=run_dir, writable=writable, schema_path=self.schema_path)

    def _role_for_phase(self, phase: str, provider_name: str) -> str:
        mapping = {"explore": "explorer", "plan": "planner", "implement": "implementer", "verify": "verifier", "review": "reviewer"}
        if provider_name == "shell":
            return "verifier"
        return mapping[phase]

    def _evaluate_gate(self, phase: str, results: list[ProviderResult]) -> dict:
        ok = [r for r in results if r.status == "ok"]
        blockers = sorted({x for r in results for x in r.blockers})
        decisions = [r.decision for r in results]
        failure_classifications = sorted({x for r in results for x in r.failure_classification})
        coverage = max((r.surface_coverage for r in results), default=0.0)
        entrypoint_confirmed = any(r.entrypoint_status == "confirmed" for r in results)
        file_set_good = any(r.file_set_mode in {"locked", "open-with-reason"} for r in results)
        verification_commands = sorted({x for r in results for x in (r.verification_commands or r.commands)})
        missing: list[str] = []
        required_actions: list[str] = []
        owner = phase
        reason = "phase passed"
        recommended_next_phase = NEXT_PHASE.get(phase)

        if phase == "explore":
            owner = "explorer"
            if not ok:
                missing.append("no successful explorer result")
            if not entrypoint_confirmed:
                missing.append("entrypoint not confirmed")
            if coverage < 0.70:
                missing.append("surface coverage below 0.70")
            if any("unknown-surface" in b for b in blockers):
                missing.append("unknown surface remains")
            if "re-explore" in decisions:
                missing.append("explorer requested re-explore")
            required_actions = ["narrow search to direct call path and named consumers", "identify one likely test surface"] if missing else []
            if missing:
                reason = "explore evidence not yet converged"
                recommended_next_phase = RECOMMENDED_NEXT.get("re-explore")
        elif phase == "plan":
            owner = "planner"
            if not ok:
                missing.append("no successful planner result")
            if not file_set_good:
                missing.append("file set not locked")
            if not verification_commands:
                missing.append("verification commands missing")
            if not any(r.rollback_anchor for r in results):
                missing.append("rollback anchor missing")
            if "re-plan" in decisions:
                missing.append("planner requested re-plan")
            required_actions = ["lock the file set or explain why it stays open", "name deterministic verification commands", "name rollback anchor"] if missing else []
            if missing:
                reason = "plan is not yet safe to implement"
                recommended_next_phase = RECOMMENDED_NEXT.get("re-plan")
        elif phase == "implement":
            owner = "implementer"
            if not ok:
                missing.append("no successful implementer result")
            if any(r.scope_extension_needed for r in results):
                missing.append("scope extension requested")
            if "request-scope-extension" in decisions:
                missing.append("implementer requested scope extension")
            required_actions = ["return to planner with requested files and reason"] if missing else []
            if missing:
                reason = "implementation exceeded or challenged the locked plan"
                recommended_next_phase = RECOMMENDED_NEXT.get("request-scope-extension")
        elif phase == "verify":
            owner = "verifier"
            if not results:
                missing.append("no verifier result")
            if self.config.require_shell_verifier and not any(r.provider == "shell" for r in results):
                missing.append("shell verifier missing")
            if any(r.status == "failed" and not r.failure_classification for r in results):
                missing.append("unclassified verification failure")
            if "rollback" in decisions:
                missing.append("verifier requested rollback")
            required_actions = ["rerun failing deterministic commands once", "classify every failing command", "return to implement if failure is task-caused"] if missing else []
            if missing:
                reason = "verification evidence is incomplete or unsafe"
                recommended_next_phase = RECOMMENDED_NEXT.get("rollback") if "rollback" in decisions else PhaseName.VERIFY.value
        elif phase == "review":
            owner = "reviewer"
            if not ok:
                missing.append("no successful reviewer result")
            if "block-release" in decisions:
                missing.append("reviewer blocked release")
            if blockers:
                missing.append("blocking issues present")
            required_actions = ["resolve plan drift or high-risk untested branches before release"] if missing else []
            if missing:
                reason = "review found release-blocking issues"
                recommended_next_phase = RECOMMENDED_NEXT.get("block-release")
        if blockers and phase != "review":
            missing.append("blocking issues present")
        return {
            "passed": not missing,
            "missing": sorted(set(missing)),
            "decisions": decisions,
            "blockers": blockers,
            "failure_classification": failure_classifications,
            "owner": owner,
            "reason": reason,
            "required_actions": required_actions,
            "recommended_next_phase": recommended_next_phase,
        }

    def _phase_summary(self, results: Iterable[ProviderResult]) -> str:
        lines: list[str] = []
        for r in results:
            lines.append(f"## {r.provider}\nstatus: {r.status}\ndecision: {r.decision}\nsummary: {r.summary}\n")
            if r.entrypoint_status != "unknown":
                lines.append(f"entrypoint_status: {r.entrypoint_status}")
            if r.surface_coverage:
                lines.append(f"surface_coverage: {r.surface_coverage}")
            if r.file_set_mode != "unknown":
                lines.append(f"file_set_mode: {r.file_set_mode}")
            if r.relevant_files:
                lines.append("relevant_files:\n" + "\n".join(f"- {x}" for x in r.relevant_files))
            if r.evidence_map:
                lines.append("evidence_map:\n" + "\n".join(f"- {x}" for x in r.evidence_map))
            if r.proposed_changes:
                lines.append("proposed_changes:\n" + "\n".join(f"- {x}" for x in r.proposed_changes))
            if r.failure_classification:
                lines.append("failure_classification:\n" + "\n".join(f"- {x}" for x in r.failure_classification))
            if r.risks:
                lines.append("risks:\n" + "\n".join(f"- {x}" for x in r.risks))
            if r.blockers:
                lines.append("blockers:\n" + "\n".join(f"- {x}" for x in r.blockers))
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def _final_report(self, manifest: RunManifest) -> str:
        lines = [
            f"# Multi-Agent Co-Work Report: {manifest.run_id}",
            "",
            f"Task: {manifest.task}",
            f"Status: {manifest.status}",
            f"Repository: {manifest.repo_root}",
            f"Routing profile: {manifest.routing.get('memory', {}).get('profile') or self.config.default_profile}",
            f"Recommended next phase: {manifest.next_phase}",
            "",
        ]
        for phase, payload in manifest.phases.items():
            lines.append(f"## {phase}")
            gate = manifest.gates.get(phase)
            if gate:
                lines.append(f"- gate passed: {gate['passed']}")
                lines.append(f"- intervention owner: {gate.get('owner')}")
                lines.append(f"- gate reason: {gate.get('reason')}")
                lines.append(f"- recommended next phase: {gate.get('recommended_next_phase')}")
                if gate.get("required_actions"):
                    lines.append("- required actions:")
                    lines.extend([f"  - {x}" for x in gate["required_actions"]])
                if gate.get("missing"):
                    lines.append("- gate missing:")
                    lines.extend([f"  - {x}" for x in gate["missing"]])
            for provider_payload in payload.get("providers", []):
                lines.append(f"### {provider_payload['provider']}")
                lines.append(f"- status: {provider_payload['status']}")
                lines.append(f"- decision: {provider_payload.get('decision')}")
                lines.append(f"- confidence: {provider_payload.get('confidence')}")
                lines.append(f"- summary: {provider_payload['summary']}")
                if provider_payload.get("entrypoint_status") and provider_payload.get("entrypoint_status") != "unknown":
                    lines.append(f"- entrypoint status: {provider_payload['entrypoint_status']}")
                if provider_payload.get("surface_coverage"):
                    lines.append(f"- surface coverage: {provider_payload['surface_coverage']}")
                if provider_payload.get("file_set_mode") and provider_payload.get("file_set_mode") != "unknown":
                    lines.append(f"- file set mode: {provider_payload['file_set_mode']}")
                if provider_payload.get("relevant_files"):
                    lines.append("- relevant files:")
                    lines.extend([f"  - {x}" for x in provider_payload["relevant_files"]])
                if provider_payload.get("evidence_map"):
                    lines.append("- evidence map:")
                    lines.extend([f"  - {x}" for x in provider_payload["evidence_map"]])
                if provider_payload.get("proposed_changes"):
                    lines.append("- proposed changes:")
                    lines.extend([f"  - {x}" for x in provider_payload["proposed_changes"]])
                if provider_payload.get("failure_classification"):
                    lines.append("- failure classification:")
                    lines.extend([f"  - {x}" for x in provider_payload["failure_classification"]])
                if provider_payload.get("risks"):
                    lines.append("- risks:")
                    lines.extend([f"  - {x}" for x in provider_payload["risks"]])
                if provider_payload.get("blockers"):
                    lines.append("- blockers:")
                    lines.extend([f"  - {x}" for x in provider_payload["blockers"]])
                if provider_payload.get("error"):
                    lines.append(f"- error: {provider_payload['error']}")
                lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _save_manifest(self, run_dir: Path, manifest: RunManifest) -> None:
        write_json(run_dir / "manifest.json", manifest.to_dict())
