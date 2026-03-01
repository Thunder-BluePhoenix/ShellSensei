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


def vscode_snippets_template() -> dict:
    return {
        "ShellSensei Suggest": {
            "prefix": "ss-suggest",
            "body": ["python -m shellsensei suggest --format markdown --output ./.shellsensei/suggestions.md"],
            "description": "Run ShellSensei suggestions",
        },
        "ShellSensei Quality Gate": {
            "prefix": "ss-qgate",
            "body": ["python -m shellsensei quality-gate --format text"],
            "description": "Run ShellSensei quality gate",
        },
    }


def write_vscode_snippets(root: Path) -> Path:
    out = root / ".vscode" / "shellsensei.code-snippets"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(vscode_snippets_template(), indent=2) + "\n", encoding="utf-8")
    return out


def write_diagnostics_bridge(root: Path, diagnostics: list[dict], output: str = ".shellsensei/diagnostics.json") -> Path:
    out = root / output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"count": len(diagnostics), "diagnostics": diagnostics}, indent=2) + "\n", encoding="utf-8")
    return out
