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
        return {"version": 2, "posts": [], "reviews": []}
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
        "status": "pending",
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


def review_post(path: Path, post_id: int, reviewer: str, decision: str, note: str | None = None) -> dict:
    return review_post_with_rules(path, post_id, reviewer, decision, required_approvers=1, note=note)


def review_post_with_rules(
    path: Path,
    post_id: int,
    reviewer: str,
    decision: str,
    required_approvers: int = 1,
    note: str | None = None,
) -> dict:
    payload = load_board(path)
    target = None
    for post in payload.get("posts", []):
        if post.get("id") == post_id:
            target = post
            break
    if target is None:
        raise ValueError(f"Post #{post_id} not found")
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")

    # Prevent duplicate approval credit from same reviewer.
    prior = [
        r for r in payload.get("reviews", [])
        if r.get("post_id") == post_id and r.get("reviewer") == reviewer and r.get("decision") == decision
    ]
    if prior:
        raise ValueError(f"Reviewer '{reviewer}' already submitted decision '{decision}' for post #{post_id}")

    review = {
        "post_id": post_id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewer": reviewer,
        "decision": decision,
        "note": note or "",
    }
    payload.setdefault("reviews", []).append(review)

    if decision == "rejected":
        target["status"] = "rejected"
    else:
        approved_reviewers = {
            r["reviewer"]
            for r in payload.get("reviews", [])
            if r.get("post_id") == post_id and r.get("decision") == "approved"
        }
        target["status"] = "approved" if len(approved_reviewers) >= required_approvers else "pending"

    save_board(path, payload)
    return review


def _find_post(payload: dict, post_id: int) -> dict:
    for post in payload.get("posts", []):
        if post.get("id") == post_id:
            return post
    raise ValueError(f"Post #{post_id} not found")


def activate_post(path: Path, post_id: int) -> dict:
    payload = load_board(path)
    post = _find_post(payload, post_id)
    if post.get("status") != "approved":
        raise ValueError("Only approved posts can be activated")
    post["status"] = "active"
    post["activated_at"] = datetime.now(timezone.utc).isoformat()
    save_board(path, payload)
    return post


def retire_post(path: Path, post_id: int, note: str | None = None) -> dict:
    payload = load_board(path)
    post = _find_post(payload, post_id)
    if post.get("status") not in {"active", "approved"}:
        raise ValueError("Only active/approved posts can be retired")
    post["status"] = "retired"
    post["retired_at"] = datetime.now(timezone.utc).isoformat()
    post["retire_note"] = note or ""
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
