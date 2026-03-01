from __future__ import annotations

import json
from pathlib import Path


def vscode_tasks_template() -> dict:
    return {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "ShellSensei: Suggest",
                "type": "shell",
                "command": "python -m shellsensei suggest --format markdown --output ./.shellsensei/suggestions.md",
                "group": "build",
                "problemMatcher": [],
            },
            {
                "label": "ShellSensei: Policy",
                "type": "shell",
                "command": "python -m shellsensei policy --max-risk medium",
                "group": "test",
                "problemMatcher": [],
            },
        ],
    }


def write_vscode_tasks(root: Path) -> Path:
    out = root / ".vscode" / "tasks.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(vscode_tasks_template(), indent=2) + "\n", encoding="utf-8")
    return out
