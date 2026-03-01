from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _context_path(root: Path) -> Path:
    return root / ".shellsensei" / "project_context.json"


def load_context(root: Path) -> dict:
    path = _context_path(root)
    if not path.exists():
        return {
            "version": 2,
            "last_updated": None,
            "repo_type": "generic",
            "accepted_suggestions": {},
            "rejected_suggestions": {},
            "preferred_risk": "medium",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_context(root: Path, payload: dict) -> Path:
    path = _context_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["last_updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def record_context_feedback(root: Path, suggestion_name: str, decision: str) -> Path:
    payload = load_context(root)
    key = "accepted_suggestions" if decision == "accept" else "rejected_suggestions"
    bucket = payload.setdefault(key, {})
    bucket[suggestion_name] = int(bucket.get(suggestion_name, 0)) + 1
    return save_context(root, payload)
