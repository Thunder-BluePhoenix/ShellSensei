from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from .storage import feedback_summary, get_summary, top_commands_since


def _period_start(period: str) -> datetime:
    now = datetime.now(timezone.utc)
    if period == "daily":
        return now - timedelta(days=1)
    if period == "weekly":
        return now - timedelta(days=7)
    raise ValueError(f"Unsupported period: {period}")


def build_report_payload(conn, period: str, top: int = 10) -> dict:
    since = _period_start(period)
    summary = get_summary(conn)
    feedback = feedback_summary(conn)
    top_period = top_commands_since(conn, since.isoformat(), limit=top)
    accepts = feedback.get("accept", 0)
    rejects = feedback.get("reject", 0)
    denom = accepts + rejects
    accept_rate = round((accepts / denom) * 100, 1) if denom else None
    low_value_rate = round((rejects / denom) * 100, 1) if denom else None

    return {
        "period": period,
        "since_utc": since.isoformat(),
        "summary": summary,
        "feedback": {
            "accept": accepts,
            "reject": rejects,
            "accept_rate_percent": accept_rate,
            "low_value_rate_percent": low_value_rate,
        },
        "phase_criteria": {
            "phase1_low_value_target_met": (low_value_rate is not None and low_value_rate < 10.0),
            "phase1_feedback_sufficient": denom >= 10,
        },
        "top_commands_period": [{"command": cmd, "count": count} for cmd, count in top_period],
    }


def render_report_markdown(payload: dict) -> str:
    lines = [
        f"# ShellSensei {payload['period'].capitalize()} Report",
        "",
        f"- **Since (UTC)**: `{payload['since_utc']}`",
        f"- **Sessions**: {payload['summary']['total_sessions']}",
        f"- **Commands**: {payload['summary']['total_commands']}",
        f"- **Unique normalized commands**: {payload['summary']['unique_normalized']}",
        f"- **Accepted suggestions**: {payload['feedback']['accept']}",
        f"- **Rejected suggestions**: {payload['feedback']['reject']}",
        f"- **Acceptance rate**: {payload['feedback']['accept_rate_percent'] if payload['feedback']['accept_rate_percent'] is not None else 'N/A'}",
        f"- **Low-value rate**: {payload['feedback']['low_value_rate_percent'] if payload['feedback']['low_value_rate_percent'] is not None else 'N/A'}",
        f"- **Phase1 target met (<10% low-value)**: {payload['phase_criteria']['phase1_low_value_target_met']}",
        f"- **Phase1 feedback sufficient (>=10)**: {payload['phase_criteria']['phase1_feedback_sufficient']}",
        "",
        "## Top Commands (Period)",
        "",
        "| Count | Command |",
        "|---:|---|",
    ]
    for item in payload["top_commands_period"]:
        safe = item["command"].replace("|", "\\|")
        lines.append(f"| {item['count']} | `{safe}` |")
    return "\n".join(lines)


def render_report_json(payload: dict) -> str:
    return json.dumps(payload, indent=2)
