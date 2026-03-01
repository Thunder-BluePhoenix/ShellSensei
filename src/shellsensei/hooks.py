from __future__ import annotations

from pathlib import Path

from .apply import resolve_profile_path


def _hook_markers(shell: str) -> tuple[str, str]:
    return (f"# >>> ShellSensei Hook ({shell}) >>>", "# <<< ShellSensei Hook <<<")


def hook_snippet(shell: str, enable_auto: bool = False) -> str:
    start, end = _hook_markers(shell)
    if shell == "powershell":
        auto_line = "Set-PSReadLineOption -PredictionSource History" if enable_auto else "# Set-PSReadLineOption -PredictionSource History"
        body = [
            start,
            "function global:ss_hint {",
            "  # Shows top local suggestion quickly.",
            "  python -m shellsensei suggest --limit 1 --max-risk medium",
            "}",
            "if (-not (Get-Alias ss-hint -ErrorAction SilentlyContinue)) {",
            "  Set-Alias ss-hint ss_hint",
            "}",
            auto_line,
            end,
        ]
    else:
        auto_line = "PROMPT_COMMAND=\"ss_hint >/dev/null 2>&1; ${PROMPT_COMMAND:-:}\"" if enable_auto else "# PROMPT_COMMAND=\"ss_hint >/dev/null 2>&1; ${PROMPT_COMMAND:-:}\""
        body = [
            start,
            "ss_hint() {",
            "  python -m shellsensei suggest --limit 1 --max-risk medium",
            "}",
            "# Optional auto-hint on prompt: uncomment to enable",
            auto_line,
            end,
        ]
    return "\n".join(body)


def install_hook(
    shell: str,
    profile_path: Path | None = None,
    dry_run: bool = False,
    enable_auto: bool = False,
) -> tuple[Path, str]:
    path = profile_path if profile_path else resolve_profile_path(shell)
    existing = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    snippet = hook_snippet(shell, enable_auto=enable_auto)
    start, end = _hook_markers(shell)
    if start in existing and end in existing:
        s = existing.find(start)
        e = existing.find(end) + len(end)
        before = existing[:s].rstrip()
        after = existing[e:].lstrip()
        parts = [p for p in [before, snippet, after] if p]
        updated = "\n\n".join(parts) + "\n"
    else:
        updated = (existing.rstrip() + "\n\n" if existing.strip() else "") + snippet + "\n"
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")
    return path, updated
