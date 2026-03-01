from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskResult:
    level: str
    reasons: list[str]


def classify_risk(command: str) -> RiskResult:
    text = command.lower()
    reasons: list[str] = []

    high_patterns = [
        (re.compile(r"\brm\s+-rf\b"), "destructive recursive delete"),
        (re.compile(r"\bremove-item\s+-recurse\b"), "destructive recursive delete"),
        (re.compile(r"\bdel\s+/f\b"), "force delete"),
        (re.compile(r"(^|\s)format(\s|$)"), "disk/volume formatting"),
        (re.compile(r"\bshutdown\b"), "system shutdown/restart"),
        (re.compile(r"\bgit\s+push\s+--force\b"), "history rewrite force push"),
    ]
    medium_patterns = [
        (re.compile(r"\bsudo\b"), "privileged operation"),
        (re.compile(r"\bchmod\s+777\b"), "overly broad permissions"),
        (re.compile(r"\bchown\s+-r\b"), "recursive ownership change"),
        (re.compile(r"\|\s*sh\b"), "piped shell execution"),
        (re.compile(r"\binvoke-expression\b"), "dynamic command execution"),
    ]

    for pattern, reason in high_patterns:
        if pattern.search(text):
            reasons.append(reason)
    if reasons:
        return RiskResult(level="high", reasons=sorted(set(reasons)))

    for pattern, reason in medium_patterns:
        if pattern.search(text):
            reasons.append(reason)
    if re.search(r">\s*/dev/null", text) and "command -v" not in text:
        reasons.append("output suppression may hide errors")
    if reasons:
        return RiskResult(level="medium", reasons=sorted(set(reasons)))

    return RiskResult(level="low", reasons=[])


def risk_allows(level: str, max_allowed: str) -> bool:
    order = {"low": 0, "medium": 1, "high": 2}
    return order[level] <= order[max_allowed]
