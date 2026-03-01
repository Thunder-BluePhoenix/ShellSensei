from __future__ import annotations

from dataclasses import dataclass

from .risk import classify_risk
from .storage import top_commands


@dataclass(frozen=True)
class PolicyIssue:
    severity: str
    command: str
    message: str


def check_command_policy(conn, max_allowed_risk: str = "medium", sample_top: int = 30) -> list[PolicyIssue]:
    order = {"low": 0, "medium": 1, "high": 2}
    issues: list[PolicyIssue] = []
    for command, count in top_commands(conn, limit=sample_top):
        risk = classify_risk(command)
        if order[risk.level] > order[max_allowed_risk]:
            issues.append(
                PolicyIssue(
                    severity="high" if risk.level == "high" else "medium",
                    command=command,
                    message=f"risk={risk.level} repeats={count}",
                )
            )
    return issues
