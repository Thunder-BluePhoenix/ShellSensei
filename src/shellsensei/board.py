from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .suggest import Suggestion


def board_path(root: Path) -> Path:
    return root / ".shellsensei" / "board.json"


def load_board(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "posts": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_board(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def post_suggestions(path: Path, author: str, suggestions: list[Suggestion], message: str | None = None) -> dict:
    payload = load_board(path)
    post = {
        "id": len(payload["posts"]) + 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": author,
        "host": socket.gethostname(),
        "message": message or "",
        "suggestions": [
            {
                "name": s.name,
                "kind": s.kind,
                "command": s.command,
                "risk": s.risk_level,
                "confidence": s.confidence,
                "rationale": s.rationale,
            }
            for s in suggestions
        ],
    }
    payload["posts"].append(post)
    save_board(path, payload)
    return post


def git_sync(root: Path, path: Path, message: str) -> tuple[int, str]:
    rel = path.relative_to(root)
    cmd = [
        "git",
        "-C",
        str(root),
        "add",
        str(rel),
    ]
    p1 = subprocess.run(cmd, capture_output=True, text=True)
    if p1.returncode != 0:
        return p1.returncode, (p1.stdout or "") + (p1.stderr or "")

    p2 = subprocess.run(
        ["git", "-C", str(root), "commit", "-m", message],
        capture_output=True,
        text=True,
    )
    return p2.returncode, (p2.stdout or "") + (p2.stderr or "")
