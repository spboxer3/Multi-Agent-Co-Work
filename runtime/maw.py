from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from shutil import which
from typing import Any

if __package__ in {None, ""}:
    THIS = Path(__file__).resolve()
    sys.path.insert(0, str(THIS.parent.parent))

from runtime.config import Config, ConfigError
from runtime.orchestrator import Orchestrator
from runtime.routing_memory import clear as clear_routing
from runtime.routing_memory import load as load_routing
from runtime.routing_memory import parse_phase_specs, save as save_routing
from runtime.utils import read_text


def repo_root_from(start: Path) -> Path:
    cur = start.resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / ".git").exists() or (candidate / ".agents" / "multi-agent-cowork").exists():
            return candidate
    return cur


def cmd_doctor(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    try:
        config = Config.load(repo_root, args.config)
        routing_memory = load_routing(repo_root, config)
        resolved = config.resolve_phase_providers(routing_memory)
    except ConfigError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    report = {
        "repo_root": str(repo_root),
        "config": str(config.path),
        "routing_memory": str(repo_root / config.routing_memory_path),
        "known_failures": str(repo_root / config.known_failures_path),
        "routing": {"memory": routing_memory, "resolved": resolved},
        "providers": {},
    }
    report_dict: dict[str, Any] = report
    for name in ["codex", "claude", "gemini"]:
        try:
            cfg = config.provider(name)
        except Exception:
            continue
        binary = cfg.get("command", name)
        report_dict["providers"][name] = {"binary": binary, "found": bool(which(binary)), "path": which(binary)}
    print(json.dumps(report_dict, indent=2))
    return 0


def _load_task(args: argparse.Namespace) -> str:
    if args.task:
        return args.task
    if args.task_file:
        return Path(args.task_file).read_text(encoding="utf-8")
    raise SystemExit("A task is required via --task or --task-file")


def _spawn_watcher(log_path: Path) -> None:
    """Spawn a new terminal window running the live watcher."""
    import subprocess as _sp
    import platform
    maw_py = str(Path(__file__).resolve())
    system = platform.system()
    if system == "Windows":
        _sp.Popen(
            ["cmd", "/c", "start", "MAW Live", sys.executable, maw_py, "watch", "--log", str(log_path)],
            creationflags=0x00000008,  # DETACHED_PROCESS
        )
    elif system == "Darwin":
        _sp.Popen(["open", "-a", "Terminal", "--args", sys.executable, maw_py, "watch", "--log", str(log_path)])
    else:
        for term in ["gnome-terminal", "xterm", "konsole"]:
            if which(term):
                if term == "gnome-terminal":
                    _sp.Popen([term, "--", sys.executable, maw_py, "watch", "--log", str(log_path)])
                else:
                    _sp.Popen([term, "-e", f"{sys.executable} {maw_py} watch --log {log_path}"])
                break


def cmd_watch(args: argparse.Namespace) -> int:
    from runtime.watcher import watch
    log_path = Path(args.log) if args.log else None
    if not log_path:
        repo_root = repo_root_from(Path.cwd())
        config = Config.load(repo_root, args.config)
        latest_path = repo_root / config.state_dir / "latest-run.txt"
        if latest_path.exists():
            run_id = latest_path.read_text(encoding="utf-8").strip()
            log_path = repo_root / config.state_dir / "runs" / run_id / "live.log"
        else:
            print("No run found. Specify --log or run a dispatch first.", file=sys.stderr)
            return 1
    watch(log_path)
    return 0


def cmd_dispatch(args: argparse.Namespace) -> int:
    import sys
    repo_root = repo_root_from(Path.cwd())
    task = _load_task(args)
    config = Config.load(repo_root, args.config)
    orchestrator = Orchestrator(repo_root, config)
    no_watch = getattr(args, "no_watch", False)
    watcher_cb = None if no_watch else _spawn_watcher
    run_dir = orchestrator.dispatch(task=task, run_id=args.run_id, phase_limit=args.phase_limit, start_phase=args.start_phase, verbose=getattr(args, "verbose", False), on_log_ready=watcher_cb)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps({"run_dir": str(run_dir), "manifest": manifest}, indent=2))
    else:
        print(str(run_dir))
        print(str(run_dir / "final-report.md"))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    config = Config.load(repo_root, args.config)
    orchestrator = Orchestrator(repo_root, config)
    print(json.dumps(orchestrator.status(args.run_id), indent=2))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    config = Config.load(repo_root, args.config)
    orchestrator = Orchestrator(repo_root, config)
    run_dir = orchestrator.resume(args.run_id)
    print(str(run_dir))
    print(str(run_dir / "final-report.md"))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    config = Config.load(repo_root, args.config)
    run_dir = Path(repo_root / config.state_dir / "runs" / args.run_id)
    print(read_text(run_dir / "final-report.md"))
    return 0


def cmd_routing_profiles(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    config = Config.load(repo_root, args.config)
    print(json.dumps({"default_profile": config.default_profile, "profiles": config.routing_profiles}, indent=2))
    return 0


def cmd_routing_show(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    config = Config.load(repo_root, args.config)
    memory = load_routing(repo_root, config)
    resolved = config.resolve_phase_providers(memory)
    print(json.dumps({"path": str(repo_root / config.routing_memory_path), "memory": memory, "resolved": resolved}, indent=2))
    return 0


def cmd_routing_set(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    config = Config.load(repo_root, args.config)
    overrides = parse_phase_specs(args.phase or [])
    path = save_routing(repo_root, config, profile=args.profile, overrides=overrides, note=args.note)
    memory = load_routing(repo_root, config)
    resolved = config.resolve_phase_providers(memory)
    print(json.dumps({"path": str(path), "memory": memory, "resolved": resolved}, indent=2))
    return 0


def cmd_routing_clear(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    config = Config.load(repo_root, args.config)
    path = clear_routing(repo_root, config)
    print(json.dumps({"cleared": str(path), "exists": path.exists()}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maw")
    parser.add_argument("--config", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor")
    doctor.set_defaults(func=cmd_doctor)
    dispatch = sub.add_parser("dispatch")
    dispatch.add_argument("--task")
    dispatch.add_argument("--task-file")
    dispatch.add_argument("--run-id")
    dispatch.add_argument("--start-phase", choices=["explore", "plan", "implement", "verify", "review"])
    dispatch.add_argument("--phase-limit", choices=["explore", "plan", "implement", "verify", "review"])
    dispatch.add_argument("--json", action="store_true")
    dispatch.add_argument("--verbose", action="store_true", help="Stream live progress to stderr")
    dispatch.add_argument("--no-watch", action="store_true", help="Do not open a live watcher window")
    dispatch.set_defaults(func=cmd_dispatch)
    status = sub.add_parser("status")
    status.add_argument("--run-id", required=True)
    status.set_defaults(func=cmd_status)
    resume = sub.add_parser("resume")
    resume.add_argument("--run-id", required=True)
    resume.set_defaults(func=cmd_resume)
    watch = sub.add_parser("watch", help="Live watcher for agent communication")
    watch.add_argument("--log", help="Path to live.log (defaults to latest run)")
    watch.set_defaults(func=cmd_watch)
    report = sub.add_parser("report")
    report.add_argument("--run-id", required=True)
    report.set_defaults(func=cmd_report)
    routing = sub.add_parser("routing")
    routing_sub = routing.add_subparsers(dest="routing_command", required=True)
    routing_profiles = routing_sub.add_parser("profiles")
    routing_profiles.set_defaults(func=cmd_routing_profiles)
    routing_show = routing_sub.add_parser("show")
    routing_show.set_defaults(func=cmd_routing_show)
    routing_set = routing_sub.add_parser("set")
    routing_set.add_argument("--profile")
    routing_set.add_argument("--phase", action="append")
    routing_set.add_argument("--note")
    routing_set.set_defaults(func=cmd_routing_set)
    routing_clear = routing_sub.add_parser("clear")
    routing_clear.set_defaults(func=cmd_routing_clear)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
