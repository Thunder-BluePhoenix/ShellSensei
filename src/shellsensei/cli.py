from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import sys
from getpass import getuser
from pathlib import Path

from . import __version__
from .apply import backup_profile, render_profile_block, resolve_profile_path, upsert_managed_block
from .automate import generate_wrappers
from .benchmark import run_normalize_benchmark
from .board import board_path, git_sync, load_board, post_suggestions, review_post
from .ci_profiles import load_ci_profile
from .ci_lint import lint_shell_files
from .config import default_db_path
from .history import discover_history_sources, read_history_lines, select_sources
from .hooks import hook_snippet, install_hook
from .ide import write_diagnostics_bridge, write_vscode_snippets, write_vscode_tasks
from .intent_engine import parse_intent, save_custom_profile
from .metrics import build_metrics
from .normalize import command_hash, normalize_command
from .pack import export_pack, import_pack
from .phase_status import evaluate_phase_status
from .policy import check_command_policy
from .quality_gate import run_quality_gate
from .repo_context import detect_repo_type, repo_coaching_hints
from .report import build_report_payload, render_report_json, render_report_markdown
from .risk import risk_allows
from .storage import (
    connect,
    create_session,
    feedback_summary,
    get_summary,
    get_telemetry_opt_in,
    init_db,
    insert_commands,
    log_telemetry_event,
    record_feedback,
    set_telemetry_opt_in,
    top_commands,
)
from .suggest import Suggestion, suggest_from_db
from .updater import run_self_update
from .v2_context import record_context_feedback
from .v2_ranker import rerank_suggestions


def _resolve_db_path(db_arg: str | None) -> Path:
    if db_arg:
        return Path(db_arg).expanduser().resolve()
    candidate = default_db_path()
    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        probe = sqlite3.connect(candidate)
        probe.close()
        return candidate
    except Exception:
        local = (Path.cwd() / ".shellsensei" / "shellsensei.db").resolve()
        local.parent.mkdir(parents=True, exist_ok=True)
        return local


def _write_output(text: str, output_path: str | None) -> None:
    if output_path:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote report: {path}")
        return
    print(text)


def _quote_for_alias(raw: str) -> str:
    return raw.replace("\\", "\\\\").replace('"', '\\"')


def _resolve_suggest_shell(shell: str) -> str:
    if shell != "auto":
        return shell
    return "powershell" if platform.system().lower().startswith("win") else "bash"


def _log_event(db_path: Path, event_type: str, payload: dict | None = None) -> None:
    conn = connect(db_path)
    try:
        init_db(conn)
        payload_json = json.dumps(payload) if payload else None
        log_telemetry_event(conn, event_type=event_type, payload_json=payload_json)
    finally:
        conn.close()


def _render_stats_text(db_path: Path, summary: dict[str, int], top: list[tuple[str, int]]) -> str:
    lines = [
        "ShellSensei Stats",
        "-----------------",
        f"DB Path: {db_path}",
        f"Sessions: {summary['total_sessions']}",
        f"Commands: {summary['total_commands']}",
        f"Unique normalized commands: {summary['unique_normalized']}",
        "",
        "Top commands:",
    ]
    for cmd, count in top:
        lines.append(f"  {count:>5}  {cmd}")
    return "\n".join(lines)


def _render_stats_markdown(db_path: Path, summary: dict[str, int], top: list[tuple[str, int]]) -> str:
    lines = [
        "# ShellSensei Stats",
        "",
        f"- **DB Path**: `{db_path}`",
        f"- **Sessions**: {summary['total_sessions']}",
        f"- **Commands**: {summary['total_commands']}",
        f"- **Unique normalized commands**: {summary['unique_normalized']}",
        "",
        "## Top Commands",
        "",
        "| Count | Command |",
        "|---:|---|",
    ]
    for cmd, count in top:
        safe_cmd = cmd.replace("|", "\\|")
        lines.append(f"| {count} | `{safe_cmd}` |")
    return "\n".join(lines)


def _suggestion_snippet(suggestion: Suggestion, shell: str = "bash") -> str:
    if shell == "powershell":
        return (
            f"function {suggestion.name} {{\n"
            f"  {suggestion.command}\n"
            "}"
        )
    if suggestion.kind == "alias":
        return f'alias {suggestion.name}="{_quote_for_alias(suggestion.command)}"'
    return (
        f"{suggestion.name}() {{\n"
        f"  {suggestion.command}\n"
        "}"
    )


def _render_suggest_text(suggestions: list[Suggestion], shell: str) -> str:
    lines = ["ShellSensei Suggestions", "----------------------", ""]
    for suggestion in suggestions:
        lines.extend(
            [
                f"[{suggestion.kind.upper()}] {suggestion.name}  (repeats: {suggestion.count})",
                f"Confidence: {suggestion.confidence:.2f} | Risk: {suggestion.risk_level}",
                f"Reason: {suggestion.rationale}",
                "Snippet:",
                _suggestion_snippet(suggestion, shell=shell),
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _render_suggest_markdown(suggestions: list[Suggestion], shell: str) -> str:
    code_lang = "powershell" if shell == "powershell" else "bash"
    lines = [
        "# ShellSensei Suggestions",
        "",
        f"- **Shell profile**: `{shell}`",
        "",
        "| Type | Name | Repeats | Confidence | Risk | Reason |",
        "|---|---|---:|---:|---|---|",
    ]
    for s in suggestions:
        reason = s.rationale.replace("|", "\\|")
        lines.append(f"| {s.kind} | `{s.name}` | {s.count} | {s.confidence:.2f} | {s.risk_level} | {reason} |")
    lines.append("")
    lines.append("## Snippets")
    lines.append("")
    for s in suggestions:
        lines.append(f"### `{s.name}` ({s.kind})")
        lines.append("")
        lines.append(f"```{code_lang}")
        lines.append(_suggestion_snippet(s, shell=shell))
        lines.append("```")
        lines.append("")
    return "\n".join(lines).rstrip()


def _interactive_select_suggestions(suggestions: list[Suggestion]) -> list[Suggestion]:
    print("Interactive apply mode")
    print("Type: y = include, n = skip, q = stop selection")
    print("")
    selected: list[Suggestion] = []

    for suggestion in suggestions:
        prompt = (
            f"Include {suggestion.name} ({suggestion.kind}, repeats={suggestion.count})? [y/n/q]: "
        )
        while True:
            try:
                answer = input(prompt).strip().lower()
            except EOFError:
                return selected

            if answer in {"y", "yes"}:
                selected.append(suggestion)
                break
            if answer in {"n", "no"}:
                break
            if answer in {"q", "quit"}:
                return selected
            print("Please enter y, n, or q.")

    return selected


def cmd_init(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    conn = connect(db_path)
    try:
        init_db(conn)
    finally:
        conn.close()
    print(f"Initialized ShellSensei DB at: {db_path}")
    _log_event(db_path, "init")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    conn = connect(db_path)
    try:
        init_db(conn)
        total = 0
        chosen_sources = list(select_sources(args.shell))
        if not chosen_sources:
            print(f"No history source matched shell='{args.shell}'")
            return 1

        for source in chosen_sources:
            lines = read_history_lines(source, limit=args.limit)
            if not lines:
                print(f"Skip {source.shell}: no history found at {source.path}")
                continue

            payload: list[tuple[str, str, str]] = []
            for raw in lines:
                norm = normalize_command(raw)
                if not norm:
                    continue
                payload.append((raw, norm, command_hash(norm)))

            if not payload:
                print(f"Skip {source.shell}: parsed 0 non-empty commands")
                continue

            session_id = create_session(conn, source.shell, str(source.path))
            count = insert_commands(conn, session_id, payload)
            total += count
            print(f"Ingested {count} commands from {source.shell} ({source.path})")

        print(f"Total imported commands: {total}")
        _log_event(db_path, "ingest", {"total_imported": total, "shell": args.shell})
        return 0
    finally:
        conn.close()


def cmd_stats(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' first.")
        return 1

    conn = connect(db_path)
    try:
        summary = get_summary(conn)
        top = top_commands(conn, limit=args.top)
        payload = {
            "db_path": str(db_path),
            "summary": summary,
            "top_commands": [{"command": cmd, "count": count} for cmd, count in top],
        }

        if args.format == "json":
            rendered = json.dumps(payload, indent=2)
        elif args.format == "markdown":
            rendered = _render_stats_markdown(db_path, summary, top)
        else:
            rendered = _render_stats_text(db_path, summary, top)

        _write_output(rendered, args.output)
        _log_event(db_path, "stats", {"format": args.format, "top": args.top})
        return 0
    finally:
        conn.close()


def cmd_doctor(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    print("ShellSensei Doctor")
    print("------------------")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.platform()}")
    print(f"DB Path: {db_path} ({'exists' if db_path.exists() else 'missing'})")
    print("\nHistory sources:")
    for source in discover_history_sources():
        status = "ok" if source.path.exists() else "missing"
        print(f"- {source.shell:<10} {status:<7} {source.path}")
    return 0


def cmd_suggest(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' and 'shellsensei ingest' first.")
        return 1

    project_root = Path(args.project_root).expanduser().resolve()
    suggestions = _load_filtered_suggestions(
        db_path=db_path,
        min_count=args.min_count,
        limit=args.limit,
        prefix=args.prefix,
        max_risk=args.max_risk,
        project_root=project_root,
        threshold=args.threshold,
    )

    if not suggestions:
        print("No suggestions found. Try lowering --min-count or ingest more history.")
        return 0

    target_shell = _resolve_suggest_shell(args.shell)
    filtered = suggestions

    if args.format == "json":
        rendered = json.dumps(
            {
                "shell": target_shell,
                "suggestions": [
                    {
                        "kind": s.kind,
                        "name": s.name,
                        "count": s.count,
                        "normalized": s.normalized,
                        "command": s.command,
                        "rationale": s.rationale,
                        "snippet": _suggestion_snippet(s, shell=target_shell),
                        "confidence": s.confidence,
                        "risk_level": s.risk_level,
                    }
                    for s in filtered
                ],
            },
            indent=2,
        )
    elif args.format == "markdown":
        rendered = _render_suggest_markdown(filtered, shell=target_shell)
    else:
        rendered = _render_suggest_text(filtered, shell=target_shell)

    _write_output(rendered, args.output)
    _log_event(
        db_path,
        "suggest",
        {"count": len(filtered), "format": args.format, "shell": target_shell, "max_risk": args.max_risk},
    )
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' and 'shellsensei ingest' first.")
        return 1

    target_shell = _resolve_suggest_shell(args.shell)
    profile_path = (
        Path(args.profile).expanduser().resolve()
        if args.profile
        else resolve_profile_path(target_shell)
    )

    project_root = Path(args.project_root).expanduser().resolve()
    suggestions = _load_filtered_suggestions(
        db_path=db_path,
        min_count=args.min_count,
        limit=args.limit,
        prefix=args.prefix,
        max_risk=args.max_risk,
        project_root=project_root,
        threshold=args.threshold,
    )

    if not suggestions:
        print("No suggestions found. Nothing to apply.")
        return 0

    selected: list[Suggestion]
    if args.interactive:
        selected = _interactive_select_suggestions(suggestions)
    elif args.all:
        selected = suggestions
    else:
        by_name = {s.name: s for s in suggestions}
        selected = []
        missing: list[str] = []
        for name in args.name:
            if name in by_name:
                selected.append(by_name[name])
            else:
                missing.append(name)
        if missing:
            print(f"Unknown suggestion name(s): {', '.join(missing)}")
            print("Run 'shellsensei suggest' to view available names.")
            return 1

    if not selected:
        print("No suggestions selected. Nothing to apply.")
        return 0

    block = render_profile_block(selected, shell=target_shell)
    existing = profile_path.read_text(encoding="utf-8", errors="ignore") if profile_path.exists() else ""
    updated = upsert_managed_block(existing, block, shell=target_shell)

    if args.dry_run:
        print(f"Dry run only. Would update: {profile_path}")
        print("")
        print(updated)
        return 0

    profile_path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_profile(profile_path)
    profile_path.write_text(updated, encoding="utf-8")
    print(f"Updated profile: {profile_path}")
    if backup:
        print(f"Backup created: {backup}")

    if args.record_feedback:
        conn = connect(db_path)
        try:
            init_db(conn)
            for s in selected:
                record_feedback(
                    conn,
                    suggestion_name=s.name,
                    normalized_command=s.normalized,
                    decision="accept",
                    notes="auto: applied via shellsensei apply",
                )
                record_context_feedback(project_root, s.name, "accept")
        finally:
            conn.close()

    _log_event(
        db_path,
        "apply",
        {
            "shell": target_shell,
            "profile": str(profile_path),
            "selected_count": len(selected),
            "max_risk": args.max_risk,
        },
    )
    return 0


def cmd_feedback(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    conn = connect(db_path)
    try:
        init_db(conn)
        record_feedback(
            conn,
            suggestion_name=args.name,
            normalized_command=args.normalized,
            decision=args.decision,
            notes=args.notes,
        )
        counts = feedback_summary(conn)
    finally:
        conn.close()
    project_root = Path(args.project_root).expanduser().resolve()
    record_context_feedback(project_root, args.name, args.decision)
    print(f"Feedback recorded: {args.decision} for {args.name}")
    print(f"Summary => accept: {counts.get('accept', 0)}, reject: {counts.get('reject', 0)}")
    _log_event(db_path, "feedback", {"decision": args.decision, "name": args.name})
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' first.")
        return 1
    conn = connect(db_path)
    try:
        init_db(conn)
        payload = build_report_payload(conn, period=args.period, top=args.top)
    finally:
        conn.close()
    rendered = render_report_json(payload) if args.format == "json" else render_report_markdown(payload)
    _write_output(rendered, args.output)
    _log_event(db_path, "report", {"period": args.period, "format": args.format})
    return 0


def cmd_policy(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' first.")
        return 1
    conn = connect(db_path)
    try:
        init_db(conn)
        issues = check_command_policy(conn, max_allowed_risk=args.max_risk, sample_top=args.top)
    finally:
        conn.close()
    if not issues:
        print("Policy check passed. No violations found.")
        return 0
    print("Policy violations:")
    for issue in issues:
        print(f"- [{issue.severity}] {issue.command} :: {issue.message}")
    return 0


def cmd_pack_export(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    conn = connect(db_path)
    try:
        init_db(conn)
        suggestions = suggest_from_db(conn, min_count=args.min_count, limit=args.limit, prefix=args.prefix)
    finally:
        conn.close()
    target_shell = _resolve_suggest_shell(args.shell)
    suggestions = [s for s in suggestions if risk_allows(s.risk_level, args.max_risk)]
    out = Path(args.output).expanduser().resolve()
    export_pack(out, name=args.name, shell=target_shell, suggestions=suggestions)
    print(f"Pack exported: {out} ({len(suggestions)} suggestions)")
    return 0


def cmd_pack_import(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    pack_path = Path(args.input).expanduser().resolve()
    shell, suggestions = import_pack(pack_path)
    target_shell = _resolve_suggest_shell(args.shell if args.shell != "auto" else shell)
    selected = [s for s in suggestions if risk_allows(s.risk_level, args.max_risk)]
    profile_path = Path(args.profile).expanduser().resolve() if args.profile else resolve_profile_path(target_shell)
    block = render_profile_block(selected, shell=target_shell)
    existing = profile_path.read_text(encoding="utf-8", errors="ignore") if profile_path.exists() else ""
    updated = upsert_managed_block(existing, block, shell=target_shell)
    if args.dry_run:
        print(f"Dry run only. Would import pack to: {profile_path}")
        print("")
        print(updated)
        return 0
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    backup = backup_profile(profile_path)
    profile_path.write_text(updated, encoding="utf-8")
    print(f"Pack imported to profile: {profile_path}")
    if backup:
        print(f"Backup created: {backup}")
    _log_event(db_path, "pack_import", {"input": str(pack_path), "shell": target_shell, "count": len(selected)})
    return 0


def cmd_telemetry(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    conn = connect(db_path)
    try:
        init_db(conn)
        if args.action == "enable":
            set_telemetry_opt_in(conn, True)
            print("Telemetry enabled (opt-in).")
        elif args.action == "disable":
            set_telemetry_opt_in(conn, False)
            print("Telemetry disabled.")
        else:
            enabled = get_telemetry_opt_in(conn)
            print(f"Telemetry opt-in: {'enabled' if enabled else 'disabled'}")
    finally:
        conn.close()
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    print(f"ShellSensei {__version__}")
    return 0


def cmd_self_update(args: argparse.Namespace) -> int:
    code, output = run_self_update(package_name=args.package)
    if output:
        print(output)
    return 0 if code == 0 else 1


def cmd_hook(args: argparse.Namespace) -> int:
    shell = _resolve_suggest_shell(args.shell)
    if args.action == "show":
        print(hook_snippet(shell, enable_auto=args.enable_auto))
        return 0
    profile = Path(args.profile).expanduser().resolve() if args.profile else None
    path, updated = install_hook(shell=shell, profile_path=profile, dry_run=args.dry_run, enable_auto=args.enable_auto)
    if args.dry_run:
        print(f"Dry run only. Would update hook in: {path}")
        print("")
        print(updated)
    else:
        print(f"Hook installed in: {path}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    payload = run_normalize_benchmark(sample_count=args.samples)
    if args.format == "json":
        rendered = json.dumps(payload, indent=2)
    else:
        rendered = (
            "ShellSensei Benchmark\n"
            "---------------------\n"
            f"Samples: {payload['sample_count']}\n"
            f"Elapsed (s): {payload['elapsed_seconds']}\n"
            f"Ops/sec: {payload['ops_per_second']}\n"
            f"Hashes generated: {payload['hashes_generated']}"
        )
    _write_output(rendered, args.output)
    return 0


def cmd_coach(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    repo = detect_repo_type(root)
    hints = repo_coaching_hints(repo)
    lines = [f"Repo type: {repo}", "Hints:"]
    lines.extend([f"- {h}" for h in hints])
    print("\n".join(lines))
    return 0


def cmd_llm_parse(args: argparse.Namespace) -> int:
    root = Path(args.project_root).expanduser().resolve()
    parsed = parse_intent(args.text, root=root, profile=args.profile, backend=args.backend)
    if args.format == "json":
        print(json.dumps(parsed, indent=2))
    else:
        print(f"Intent: {parsed['intent']}")
        print(f"Backend: {parsed['backend']}")
        print(f"Redacted: {parsed['redacted_text']}")
    return 0


def cmd_ci_lint(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    findings = lint_shell_files(root)
    prof = load_ci_profile(args.profile, custom_file=args.custom_profile_file)
    max_risk = prof.get("max_risk", "high")
    order = {"low": 0, "medium": 1, "high": 2}
    findings = [f for f in findings if order[f["risk"]] >= order[max_risk]]
    if args.format == "json":
        rendered = json.dumps({"count": len(findings), "findings": findings}, indent=2)
    else:
        if not findings:
            rendered = "No CI lint findings."
        else:
            lines = [f"CI lint findings: {len(findings)}"]
            for f in findings[: args.max_print]:
                lines.append(
                    f"- [{f['risk']}] {f['file']}:{f['line']} :: {', '.join(f['reasons'])}"
                )
            rendered = "\n".join(lines)
    _write_output(rendered, args.output)
    return 1 if findings else 0


def cmd_ide(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    if args.action == "vscode":
        out = write_vscode_tasks(root)
        print(f"Wrote VS Code tasks: {out}")
        return 0
    if args.action == "snippets":
        out = write_vscode_snippets(root)
        print(f"Wrote VS Code snippets: {out}")
        return 0
    if args.action == "diagnostics":
        findings = lint_shell_files(root)
        out = write_diagnostics_bridge(root, findings, output=args.output)
        print(f"Wrote diagnostics bridge file: {out}")
        return 0
    print("Unsupported IDE action.")
    return 1


def cmd_intent_profile(args: argparse.Namespace) -> int:
    root = Path(args.project_root).expanduser().resolve()
    patterns = [p.strip() for p in args.pattern if p.strip()]
    if not patterns:
        print("No valid patterns provided.")
        return 1
    out = save_custom_profile(root, patterns)
    print(f"Saved custom intent redaction profile: {out}")
    return 0


def cmd_quality_gate(args: argparse.Namespace) -> int:
    payload = run_quality_gate(min_ops_per_sec=args.min_ops_per_sec)
    rendered = json.dumps(payload, indent=2) if args.format == "json" else (
        "ShellSensei Quality Gate\n"
        "------------------------\n"
        f"Tests OK: {payload['tests_ok']}\n"
        f"Benchmark OK: {payload['bench_ok']}\n"
        f"Ops/sec: {payload['bench']['ops_per_second']} (min {payload['min_ops_per_sec']})\n"
        f"Overall OK: {payload['overall_ok']}"
    )
    _write_output(rendered, args.output)
    return 0 if payload["overall_ok"] else 1


def cmd_metrics(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' first.")
        return 1
    conn = connect(db_path)
    try:
        init_db(conn)
        payload = build_metrics(conn)
    finally:
        conn.close()
    rendered = json.dumps(payload, indent=2) if args.format == "json" else (
        "ShellSensei Metrics\n"
        "-------------------\n"
        f"Commands: {payload['summary']['total_commands']}\n"
        f"Unique normalized: {payload['summary']['unique_normalized']}\n"
        f"Feedback total: {payload['feedback']['total']}\n"
        f"Low-value rate (%): {payload['feedback']['low_value_rate_percent']}\n"
        f"Phase1 target met (<10% low-value): {payload['phase_criteria']['phase1_low_value_target_met']}\n"
        f"Feedback sufficient (>=10): {payload['phase_criteria']['phase1_feedback_sufficient']}"
    )
    _write_output(rendered, args.output)
    return 0


def cmd_phase_status(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' first.")
        return 1
    conn = connect(db_path)
    try:
        init_db(conn)
        metrics = build_metrics(conn)
    finally:
        conn.close()

    root = Path(args.root).expanduser().resolve()
    bp = board_path(root)
    board = load_board(bp)
    board_posts = len(board.get("posts", []))
    phases = evaluate_phase_status(metrics, board_posts=board_posts)
    payload = {
        "phases": phases,
        "metrics": metrics,
        "board_posts": board_posts,
    }
    if args.format == "json":
        rendered = json.dumps(payload, indent=2)
    else:
        lines = [
            "ShellSensei Phase Status",
            "------------------------",
            f"Phase 0 (Foundation): {phases['phase0_foundation']}",
            f"Phase 1 (Personal Coaching): {phases['phase1_personal_coaching']}",
            f"Phase 2 (Safe Automation): {phases['phase2_safe_automation']}",
            f"Phase 3 (Team Intelligence): {phases['phase3_team_intelligence']}",
            f"Phase 4 (Productization): {phases['phase4_productization']}",
            "",
            f"Board posts: {board_posts}",
            f"Feedback total: {metrics['feedback']['total']}",
            f"Low-value rate (%): {metrics['feedback']['low_value_rate_percent']}",
        ]
        rendered = "\n".join(lines)
    _write_output(rendered, args.output)
    return 0


def _load_filtered_suggestions(
    db_path: Path,
    min_count: int,
    limit: int,
    prefix: str,
    max_risk: str,
    project_root: Path | None = None,
    threshold: float = 0.35,
) -> list[Suggestion]:
    conn = connect(db_path)
    try:
        init_db(conn)
        suggestions = suggest_from_db(conn, min_count=min_count, limit=limit, prefix=prefix)
    finally:
        conn.close()
    filtered = [s for s in suggestions if risk_allows(s.risk_level, max_risk)]
    if project_root is not None:
        return rerank_suggestions(filtered, project_root=project_root, threshold=threshold)
    return filtered


def cmd_automate(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' and 'shellsensei ingest' first.")
        return 1
    target_shell = _resolve_suggest_shell(args.shell)
    project_root = Path(args.project_root).expanduser().resolve()
    suggestions = _load_filtered_suggestions(
        db_path,
        args.min_count,
        args.limit,
        args.prefix,
        args.max_risk,
        project_root=project_root,
        threshold=args.threshold,
    )
    if not suggestions:
        print("No suggestions available for wrapper generation.")
        return 0
    out_dir = Path(args.out_dir).expanduser().resolve()
    manifest = generate_wrappers(out_dir, suggestions, target_shell)
    print(f"Generated {manifest['count']} wrapper scripts at: {out_dir}")
    print(f"Manifest: {out_dir / 'manifest.json'}")
    return 0


def cmd_board(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    path = board_path(root)

    if args.action == "list":
        payload = load_board(path)
        if args.format == "json":
            print(json.dumps(payload, indent=2))
            return 0
        print(f"Board posts: {len(payload.get('posts', []))}")
        for post in payload.get("posts", [])[: args.limit]:
            print(f"- #{post['id']} {post['created_at']} {post['author']} ({len(post['suggestions'])} suggestions)")
        return 0

    if args.action in {"approve", "reject"}:
        if args.post_id is None:
            print("--post-id is required for approve/reject")
            return 1
        review = review_post(
            path=path,
            post_id=args.post_id,
            reviewer=args.reviewer or getuser(),
            decision="approved" if args.action == "approve" else "rejected",
            note=args.note,
        )
        print(f"Post #{review['post_id']} {review['decision']} by {review['reviewer']}")
        return 0

    db_path = _resolve_db_path(args.db)
    if not db_path.exists():
        print(f"Database not found: {db_path}. Run 'shellsensei init' and 'shellsensei ingest' first.")
        return 1

    suggestions = _load_filtered_suggestions(
        db_path,
        args.min_count,
        args.limit,
        args.prefix,
        args.max_risk,
        project_root=root,
        threshold=args.threshold,
    )
    if not suggestions:
        print("No suggestions to post.")
        return 0
    post = post_suggestions(
        path=path,
        author=args.author or getuser(),
        suggestions=suggestions,
        message=args.message,
    )
    print(f"Posted board entry #{post['id']} with {len(post['suggestions'])} suggestions -> {path}")
    if args.git_sync:
        code, out = git_sync(root, path, message=args.git_message or f"shellsensei: board post #{post['id']}")
        if out.strip():
            print(out.strip())
        if code != 0:
            return code
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="shellsensei", description="Local-first terminal workflow coach")
    parser.add_argument("--db", help="Path to SQLite DB (default: ~/.shellsensei/shellsensei.db)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize local SQLite database")
    p_init.set_defaults(func=cmd_init)

    p_ingest = sub.add_parser("ingest", help="Ingest shell history into local database")
    p_ingest.add_argument("--shell", choices=["auto", "powershell", "bash", "zsh"], default="auto")
    p_ingest.add_argument("--limit", type=int, default=None, help="Only ingest last N commands per shell")
    p_ingest.set_defaults(func=cmd_ingest)

    p_stats = sub.add_parser("stats", help="Show summary and top command patterns")
    p_stats.add_argument("--top", type=int, default=10, help="Number of top commands to show")
    p_stats.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format for stats report",
    )
    p_stats.add_argument("--output", help="Write report to file instead of stdout")
    p_stats.set_defaults(func=cmd_stats)

    p_doctor = sub.add_parser("doctor", help="Check environment and history source availability")
    p_doctor.set_defaults(func=cmd_doctor)

    p_suggest = sub.add_parser("suggest", help="Suggest aliases/functions from repeated command patterns")
    p_suggest.add_argument("--min-count", type=int, default=3, help="Minimum repeat count to qualify")
    p_suggest.add_argument("--limit", type=int, default=10, help="Maximum number of suggestions")
    p_suggest.add_argument("--prefix", default="ss", help="Prefix for suggested alias/function names")
    p_suggest.add_argument(
        "--shell",
        choices=["auto", "powershell", "bash", "zsh"],
        default="auto",
        help="Generate snippets for target shell profile",
    )
    p_suggest.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format for suggestions",
    )
    p_suggest.add_argument(
        "--max-risk",
        choices=["low", "medium", "high"],
        default="high",
        help="Filter out suggestions above this risk level",
    )
    p_suggest.add_argument("--project-root", default=".", help="Project root for contextual ranking")
    p_suggest.add_argument("--threshold", type=float, default=0.35, help="Minimum contextual score [0..1]")
    p_suggest.add_argument("--output", help="Write suggestions to file instead of stdout")
    p_suggest.set_defaults(func=cmd_suggest)

    p_apply = sub.add_parser("apply", help="Apply selected suggestions into shell profile")
    p_apply.add_argument("--min-count", type=int, default=3, help="Minimum repeat count to qualify")
    p_apply.add_argument("--limit", type=int, default=10, help="Maximum number of suggestions to consider")
    p_apply.add_argument("--prefix", default="ss", help="Prefix for suggestion names")
    p_apply.add_argument(
        "--shell",
        choices=["auto", "powershell", "bash", "zsh"],
        default="auto",
        help="Target shell profile to update",
    )
    group = p_apply.add_mutually_exclusive_group(required=True)
    group.add_argument("--interactive", action="store_true", help="Review each suggestion before applying")
    group.add_argument("--all", action="store_true", help="Apply all currently suggested entries")
    group.add_argument("--name", action="append", help="Apply one suggestion by name; pass multiple times")
    p_apply.add_argument("--profile", help="Override profile path (default depends on --shell)")
    p_apply.add_argument("--dry-run", action="store_true", help="Print resulting profile content without writing")
    p_apply.add_argument(
        "--max-risk",
        choices=["low", "medium", "high"],
        default="medium",
        help="Do not apply suggestions above this risk level",
    )
    p_apply.add_argument("--project-root", default=".", help="Project root for contextual ranking")
    p_apply.add_argument("--threshold", type=float, default=0.35, help="Minimum contextual score [0..1]")
    p_apply.add_argument(
        "--no-record-feedback",
        action="store_false",
        dest="record_feedback",
        help="Do not auto-record accepted suggestions in feedback table",
    )
    p_apply.set_defaults(record_feedback=True)
    p_apply.set_defaults(func=cmd_apply)

    p_feedback = sub.add_parser("feedback", help="Record suggestion feedback for confidence tuning")
    p_feedback.add_argument("--name", required=True, help="Suggestion name")
    p_feedback.add_argument("--normalized", required=True, help="Normalized command for the suggestion")
    p_feedback.add_argument("--decision", choices=["accept", "reject"], required=True)
    p_feedback.add_argument("--notes", help="Optional short notes")
    p_feedback.add_argument("--project-root", default=".", help="Project root for context memory updates")
    p_feedback.set_defaults(func=cmd_feedback)

    p_report = sub.add_parser("report", help="Generate daily/weekly reports")
    p_report.add_argument("--period", choices=["daily", "weekly"], default="weekly")
    p_report.add_argument("--format", choices=["markdown", "json"], default="markdown")
    p_report.add_argument("--top", type=int, default=10)
    p_report.add_argument("--output", help="Write report to file instead of stdout")
    p_report.set_defaults(func=cmd_report)

    p_policy = sub.add_parser("policy", help="Run safety policy checks on observed command patterns")
    p_policy.add_argument("--max-risk", choices=["low", "medium", "high"], default="medium")
    p_policy.add_argument("--top", type=int, default=30, help="Number of top commands to evaluate")
    p_policy.set_defaults(func=cmd_policy)

    p_pack = sub.add_parser("pack", help="Export/import team workflow packs")
    p_pack_sub = p_pack.add_subparsers(dest="pack_command", required=True)

    p_pack_export = p_pack_sub.add_parser("export", help="Export suggestions to pack file")
    p_pack_export.add_argument("--name", required=True, help="Pack name")
    p_pack_export.add_argument("--output", required=True, help="Pack output path (.json)")
    p_pack_export.add_argument("--min-count", type=int, default=3)
    p_pack_export.add_argument("--limit", type=int, default=20)
    p_pack_export.add_argument("--prefix", default="ss")
    p_pack_export.add_argument("--shell", choices=["auto", "powershell", "bash", "zsh"], default="auto")
    p_pack_export.add_argument("--max-risk", choices=["low", "medium", "high"], default="medium")
    p_pack_export.set_defaults(func=cmd_pack_export)

    p_pack_import = p_pack_sub.add_parser("import", help="Import pack file into shell profile")
    p_pack_import.add_argument("--input", required=True, help="Pack file path")
    p_pack_import.add_argument("--shell", choices=["auto", "powershell", "bash", "zsh"], default="auto")
    p_pack_import.add_argument("--profile", help="Override profile path")
    p_pack_import.add_argument("--dry-run", action="store_true")
    p_pack_import.add_argument("--max-risk", choices=["low", "medium", "high"], default="medium")
    p_pack_import.set_defaults(func=cmd_pack_import)

    p_telemetry = sub.add_parser("telemetry", help="Manage telemetry opt-in state")
    p_telemetry.add_argument("action", choices=["status", "enable", "disable"])
    p_telemetry.set_defaults(func=cmd_telemetry)

    p_version = sub.add_parser("version", help="Show ShellSensei version")
    p_version.set_defaults(func=cmd_version)

    p_update = sub.add_parser("self-update", help="Upgrade ShellSensei package using pip")
    p_update.add_argument("--package", default="shellsensei", help="Package name to upgrade")
    p_update.set_defaults(func=cmd_self_update)

    p_hook = sub.add_parser("hook", help="Manage shell hook snippets")
    p_hook.add_argument("action", choices=["show", "install"])
    p_hook.add_argument("--shell", choices=["auto", "powershell", "bash", "zsh"], default="auto")
    p_hook.add_argument("--profile", help="Override profile path for hook install")
    p_hook.add_argument("--enable-auto", action="store_true", help="Enable contextual loop hook behavior")
    p_hook.add_argument("--dry-run", action="store_true")
    p_hook.set_defaults(func=cmd_hook)

    p_bench = sub.add_parser("benchmark", help="Run local performance benchmark")
    p_bench.add_argument("--samples", type=int, default=10000)
    p_bench.add_argument("--format", choices=["text", "json"], default="text")
    p_bench.add_argument("--output", help="Write benchmark output to file")
    p_bench.set_defaults(func=cmd_benchmark)

    p_coach = sub.add_parser("coach", help="Repo-aware coaching hints (Rust/Python/Frappe/Kafka)")
    p_coach.add_argument("--path", default=".")
    p_coach.set_defaults(func=cmd_coach)

    p_llm = sub.add_parser("llm-parse", help="Local redacted intent parsing (v2 foundation)")
    p_llm.add_argument("--text", required=True)
    p_llm.add_argument("--format", choices=["text", "json"], default="text")
    p_llm.add_argument("--project-root", default=".")
    p_llm.add_argument("--profile", choices=["strict", "default", "custom"], default="default")
    p_llm.add_argument("--backend", choices=["heuristic", "rule"], default="heuristic")
    p_llm.set_defaults(func=cmd_llm_parse)

    p_intent_profile = sub.add_parser("intent-profile", help="Set custom redaction patterns for local intent parsing")
    p_intent_profile.add_argument("--project-root", default=".")
    p_intent_profile.add_argument("--pattern", action="append", required=True, help="Regex pattern; pass multiple times")
    p_intent_profile.set_defaults(func=cmd_intent_profile)

    p_ci = sub.add_parser("ci-lint", help="Lint shell scripts/runbooks for risky commands")
    p_ci.add_argument("--path", default=".")
    p_ci.add_argument("--format", choices=["text", "json"], default="text")
    p_ci.add_argument("--max-print", type=int, default=20)
    p_ci.add_argument("--profile", choices=["baseline", "strict", "custom"], default="baseline")
    p_ci.add_argument("--custom-profile-file", help="Path to custom CI profile json")
    p_ci.add_argument("--output", help="Write lint report to file")
    p_ci.set_defaults(func=cmd_ci_lint)

    p_ide = sub.add_parser("ide", help="IDE integrations")
    p_ide.add_argument("action", choices=["vscode", "snippets", "diagnostics"])
    p_ide.add_argument("--path", default=".")
    p_ide.add_argument("--output", default=".shellsensei/diagnostics.json")
    p_ide.set_defaults(func=cmd_ide)

    p_metrics = sub.add_parser("metrics", help="Show plan criteria metrics and completion status")
    p_metrics.add_argument("--format", choices=["text", "json"], default="text")
    p_metrics.add_argument("--output", help="Write metrics output to file")
    p_metrics.set_defaults(func=cmd_metrics)

    p_phase = sub.add_parser("phase-status", help="Show plan phase completion status (Phase 0-4)")
    p_phase.add_argument("--root", default=".", help="Repo root for board status lookup")
    p_phase.add_argument("--format", choices=["text", "json"], default="text")
    p_phase.add_argument("--output", help="Write phase status output to file")
    p_phase.set_defaults(func=cmd_phase_status)

    p_automate = sub.add_parser("automate", help="Generate executable wrapper scripts from suggestions")
    p_automate.add_argument("--min-count", type=int, default=3)
    p_automate.add_argument("--limit", type=int, default=20)
    p_automate.add_argument("--prefix", default="ss")
    p_automate.add_argument("--shell", choices=["auto", "powershell", "bash", "zsh"], default="auto")
    p_automate.add_argument("--max-risk", choices=["low", "medium", "high"], default="medium")
    p_automate.add_argument("--project-root", default=".", help="Project root for contextual ranking")
    p_automate.add_argument("--threshold", type=float, default=0.35, help="Minimum contextual score [0..1]")
    p_automate.add_argument("--out-dir", default="./.shellsensei/wrappers")
    p_automate.set_defaults(func=cmd_automate)

    p_board = sub.add_parser("board", help="Shared recommendation board (git-friendly)")
    p_board.add_argument("action", choices=["post", "list", "approve", "reject"])
    p_board.add_argument("--root", default=".", help="Repo root for .shellsensei board store")
    p_board.add_argument("--format", choices=["text", "json"], default="text")
    p_board.add_argument("--limit", type=int, default=20)
    p_board.add_argument("--author", help="Board post author")
    p_board.add_argument("--message", help="Short board post message")
    p_board.add_argument("--git-sync", action="store_true", help="Commit updated board file with git")
    p_board.add_argument("--git-message", help="Commit message for board sync")
    p_board.add_argument("--post-id", type=int, help="Board post id for approve/reject")
    p_board.add_argument("--reviewer", help="Reviewer name for approve/reject")
    p_board.add_argument("--note", help="Review note")
    p_board.add_argument("--min-count", type=int, default=3)
    p_board.add_argument("--prefix", default="ss")
    p_board.add_argument("--max-risk", choices=["low", "medium", "high"], default="medium")
    p_board.add_argument("--threshold", type=float, default=0.35, help="Minimum contextual score [0..1]")
    p_board.set_defaults(func=cmd_board)

    p_qg = sub.add_parser("quality-gate", help="Run release quality gates (tests + benchmark budget)")
    p_qg.add_argument("--min-ops-per-sec", type=float, default=15000.0)
    p_qg.add_argument("--format", choices=["text", "json"], default="text")
    p_qg.add_argument("--output", help="Write quality-gate report to file")
    p_qg.set_defaults(func=cmd_quality_gate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
