from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_PATTERNS = {
    "strict": [
        r"sk-[A-Za-z0-9]{12,}",
        r"ghp_[A-Za-z0-9]{12,}",
        r"AKIA[0-9A-Z]{16}",
        r"\b\d{12,19}\b",
        r"(?i)password\s*=\s*[^ ]+",
    ],
    "default": [
        r"sk-[A-Za-z0-9]{12,}",
        r"ghp_[A-Za-z0-9]{12,}",
        r"AKIA[0-9A-Z]{16}",
    ],
    "custom": [],
}


def _profile_file(root: Path) -> Path:
    return root / ".shellsensei" / "redaction_profiles.json"


def load_profiles(root: Path) -> dict:
    path = _profile_file(root)
    if not path.exists():
        return DEFAULT_PATTERNS.copy()
    payload = json.loads(path.read_text(encoding="utf-8"))
    merged = DEFAULT_PATTERNS.copy()
    merged.update(payload)
    return merged


def save_custom_profile(root: Path, patterns: list[str]) -> Path:
    payload = load_profiles(root)
    payload["custom"] = patterns
    path = _profile_file(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def redact(text: str, patterns: list[str]) -> str:
    out = text
    for p in patterns:
        out = re.sub(p, "<REDACTED>", out)
    return out


def parse_intent(text: str, root: Path, profile: str = "default", backend: str = "heuristic") -> dict:
    profiles = load_profiles(root)
    patterns = profiles.get(profile, profiles["default"])
    safe = redact(text, patterns)
    lower = safe.lower()
    if backend not in {"heuristic", "rule"}:
        backend = "heuristic"

    if "suggest" in lower or "alias" in lower:
        intent = "suggest"
    elif "apply" in lower or "install" in lower:
        intent = "apply"
    elif "report" in lower:
        intent = "report"
    elif "policy" in lower or "risk" in lower or "lint" in lower:
        intent = "policy"
    elif "board" in lower or "share" in lower or "pack" in lower:
        intent = "collaborate"
    else:
        intent = "unknown"
    return {
        "intent": intent,
        "backend": backend,
        "profile": profile,
        "redacted_text": safe,
    }
