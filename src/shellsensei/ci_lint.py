from __future__ import annotations

from pathlib import Path

from .risk import classify_risk


def lint_shell_files(root: Path) -> list[dict]:
    findings: list[dict] = []
    patterns = ["*.sh", "*.bash", "*.zsh", "*.ps1"]
    files: list[Path] = []
    for pat in patterns:
        files.extend(root.rglob(pat))
    for file in files:
        if ".git" in file.parts:
            continue
        try:
            lines = file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, start=1):
            risk = classify_risk(line)
            if risk.level != "low":
                findings.append(
                    {
                        "file": str(file),
                        "line": idx,
                        "risk": risk.level,
                        "reasons": risk.reasons,
                        "text": line.strip(),
                    }
                )
    return findings
