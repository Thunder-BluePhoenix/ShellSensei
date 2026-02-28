from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from .config import default_db_path
from .history import discover_history_sources, read_history_lines, select_sources
from .normalize import command_hash, normalize_command
from .storage import connect, create_session, get_summary, init_db, insert_commands, top_commands
from .suggest import suggest_from_db


def _resolve_db_path(db_arg: str | None) -> Path:
    return Path(db_arg).expanduser().resolve() if db_arg else default_db_path()


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


def cmd_init(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(args.db)
    conn = connect(db_path)
    try:
        init_db(conn)
    finally:
        conn.close()
    print(f"Initialized ShellSensei DB at: {db_path}")
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

    conn = connect(db_path)
    try:
        suggestions = suggest_from_db(
            conn,
            min_count=args.min_count,
            limit=args.limit,
            prefix=args.prefix,
        )
    finally:
        conn.close()

    if not suggestions:
        print("No suggestions found. Try lowering --min-count or ingest more history.")
        return 0

    lines = ["ShellSensei Suggestions", "----------------------", ""]
    for suggestion in suggestions:
        if suggestion.kind == "alias":
            snippet = f'alias {suggestion.name}="{_quote_for_alias(suggestion.command)}"'
        else:
            snippet = (
                f"{suggestion.name}() {{\n"
                f"  {suggestion.command}\n"
                "}"
            )
        lines.extend(
            [
                f"[{suggestion.kind.upper()}] {suggestion.name}  (repeats: {suggestion.count})",
                f"Reason: {suggestion.rationale}",
                "Snippet:",
                snippet,
                "",
            ]
        )
    _write_output("\n".join(lines).rstrip(), args.output)
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
    p_suggest.add_argument("--output", help="Write suggestions to file instead of stdout")
    p_suggest.set_defaults(func=cmd_suggest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
