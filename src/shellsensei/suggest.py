from __future__ import annotations

import re
from dataclasses import dataclass

from .risk import classify_risk
from .storage import repeated_patterns

_COMPLEX_MARKERS = ("|", "&&", "||", ";", ">", "<")


@dataclass(frozen=True)
class Suggestion:
    kind: str
    name: str
    command: str
    count: int
    normalized: str
    rationale: str
    confidence: float = 0.5
    risk_level: str = "low"


def _sanitize_name(raw: str) -> str:
    token = raw.strip().split(" ", 1)[0].lower() if raw.strip() else "cmd"
    token = re.sub(r"[^a-z0-9_]+", "_", token)
    token = token.strip("_")
    return token or "cmd"


def _is_complex(raw_command: str) -> bool:
    return any(marker in raw_command for marker in _COMPLEX_MARKERS)


def _confidence_score(count: int, kind: str, risk_level: str) -> float:
    # Frequency is the strongest confidence signal in MVP.
    base = 0.35 + min(count, 20) * 0.025
    if kind == "function":
        base -= 0.03
    if risk_level == "high":
        base -= 0.18
    elif risk_level == "medium":
        base -= 0.08
    return round(max(0.05, min(base, 0.98)), 2)


def build_suggestions(
    patterns: list[tuple[str, str, int]],
    prefix: str = "ss",
) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    used_names: set[str] = set()

    for normalized, raw_command, count in patterns:
        base = _sanitize_name(raw_command)
        kind = "function" if _is_complex(raw_command) else "alias"
        risk = classify_risk(raw_command)
        stem = f"{prefix}_{base}"
        name = stem
        i = 2
        while name in used_names:
            name = f"{stem}_{i}"
            i += 1
        used_names.add(name)

        if kind == "alias":
            rationale = f"simple command repeated {count} times; alias reduces typing"
        else:
            rationale = f"compound command repeated {count} times; function improves reuse"
        if risk.level != "low":
            rationale = f"{rationale}; caution: {risk.level} risk"

        suggestions.append(
            Suggestion(
                kind=kind,
                name=name,
                command=raw_command,
                count=count,
                normalized=normalized,
                rationale=rationale,
                confidence=_confidence_score(count=count, kind=kind, risk_level=risk.level),
                risk_level=risk.level,
            )
        )

    return suggestions


def suggest_from_db(
    conn,
    min_count: int = 3,
    limit: int = 10,
    prefix: str = "ss",
) -> list[Suggestion]:
    patterns = repeated_patterns(conn, min_count=min_count, limit=limit)
    return build_suggestions(patterns, prefix=prefix)
