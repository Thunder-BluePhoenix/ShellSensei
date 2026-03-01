from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .suggest import Suggestion


def export_pack(path: Path, name: str, shell: str, suggestions: list[Suggestion]) -> Path:
    payload = {
        "pack_name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "shell": shell,
        "suggestions": [
            {
                "kind": s.kind,
                "name": s.name,
                "command": s.command,
                "count": s.count,
                "normalized": s.normalized,
                "rationale": s.rationale,
                "confidence": s.confidence,
                "risk_level": s.risk_level,
            }
            for s in suggestions
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def import_pack(path: Path) -> tuple[str, list[Suggestion]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    shell = payload.get("shell", "bash")
    items = payload.get("suggestions", [])
    suggestions = [
        Suggestion(
            kind=item["kind"],
            name=item["name"],
            command=item["command"],
            count=item.get("count", 1),
            normalized=item.get("normalized", item["command"]),
            rationale=item.get("rationale", "Imported from pack"),
            confidence=float(item.get("confidence", 0.5)),
            risk_level=item.get("risk_level", "low"),
        )
        for item in items
    ]
    return shell, suggestions
