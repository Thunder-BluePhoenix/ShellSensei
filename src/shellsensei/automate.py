from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .suggest import Suggestion


def _script_extension(shell: str) -> str:
    return ".ps1" if shell == "powershell" else ".sh"


def _script_body(suggestion: Suggestion, shell: str) -> str:
    if shell == "powershell":
        return (
            "$ErrorActionPreference = \"Stop\"\n"
            f"# ShellSensei wrapper for {suggestion.name}\n"
            f"{suggestion.command}\n"
        )
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"# ShellSensei wrapper for {suggestion.name}\n"
        f"{suggestion.command}\n"
    )


def generate_wrappers(
    out_dir: Path,
    suggestions: list[Suggestion],
    shell: str,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "shell": shell,
        "count": len(suggestions),
        "scripts": [],
        "rollback_hint": "Remove generated scripts and restore shell profile backup if applied.",
    }
    ext = _script_extension(shell)
    for s in suggestions:
        script_path = out_dir / f"{s.name}{ext}"
        script_path.write_text(_script_body(s, shell), encoding="utf-8")
        if shell != "powershell":
            try:
                script_path.chmod(0o755)
            except OSError:
                pass
        manifest["scripts"].append(
            {
                "name": s.name,
                "path": str(script_path),
                "risk": s.risk_level,
                "confidence": s.confidence,
            }
        )

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
