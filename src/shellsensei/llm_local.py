from __future__ import annotations

import re


_TOKEN_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{12,}"),
    re.compile(r"ghp_[A-Za-z0-9]{12,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"\b\d{12,19}\b"),  # long numeric sequences
]


def redact_sensitive(text: str) -> str:
    redacted = text
    for pattern in _TOKEN_PATTERNS:
        redacted = pattern.sub("<REDACTED>", redacted)
    return redacted


def parse_intent_local(text: str) -> dict:
    safe = redact_sensitive(text)
    lower = safe.lower()
    if "suggest" in lower or "alias" in lower:
        intent = "suggest"
    elif "apply" in lower or "install" in lower:
        intent = "apply"
    elif "report" in lower:
        intent = "report"
    elif "policy" in lower or "risk" in lower:
        intent = "policy"
    else:
        intent = "unknown"
    return {
        "intent": intent,
        "redacted_text": safe,
        "mode": "local-heuristic",
    }
