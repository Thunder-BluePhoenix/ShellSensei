from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class HistorySource:
    shell: str
    path: Path


def _powershell_history_path() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return (
            Path(appdata)
            / "Microsoft"
            / "Windows"
            / "PowerShell"
            / "PSReadLine"
            / "ConsoleHost_history.txt"
        )
    return (
        Path.home()
        / "AppData"
        / "Roaming"
        / "Microsoft"
        / "Windows"
        / "PowerShell"
        / "PSReadLine"
        / "ConsoleHost_history.txt"
    )


def discover_history_sources() -> list[HistorySource]:
    sources: list[HistorySource] = []
    system = platform.system().lower()

    sources.append(HistorySource(shell="powershell", path=_powershell_history_path()))

    if system in {"linux", "darwin"}:
        sources.append(HistorySource(shell="bash", path=Path.home() / ".bash_history"))
        sources.append(HistorySource(shell="zsh", path=Path.home() / ".zsh_history"))
    else:
        sources.append(HistorySource(shell="bash", path=Path.home() / ".bash_history"))
        sources.append(HistorySource(shell="zsh", path=Path.home() / ".zsh_history"))

    return sources


def read_history_lines(source: HistorySource, limit: int | None = None) -> list[str]:
    if not source.path.exists():
        return []

    lines = source.path.read_text(encoding="utf-8", errors="ignore").splitlines()
    parsed: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if source.shell == "zsh" and line.startswith(": ") and ";" in line:
            line = line.split(";", 1)[1].strip()
        parsed.append(line)

    if limit and limit > 0:
        return parsed[-limit:]
    return parsed


def select_sources(shell: str) -> Iterable[HistorySource]:
    sources = discover_history_sources()
    if shell == "auto":
        return sources
    return [s for s in sources if s.shell == shell]
