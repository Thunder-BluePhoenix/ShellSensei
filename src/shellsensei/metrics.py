from __future__ import annotations

from .storage import feedback_summary, get_summary


def build_metrics(conn) -> dict:
    summary = get_summary(conn)
    feedback = feedback_summary(conn)
    accept = feedback.get("accept", 0)
    reject = feedback.get("reject", 0)
    total_fb = accept + reject
    low_value_rate = round((reject / total_fb) * 100, 1) if total_fb else None

    return {
        "summary": summary,
        "feedback": {
            "accept": accept,
            "reject": reject,
            "total": total_fb,
            "low_value_rate_percent": low_value_rate,
        },
        "phase_criteria": {
            "phase1_low_value_target_met": (low_value_rate is not None and low_value_rate < 10.0),
            "phase1_feedback_sufficient": total_fb >= 10,
        },
    }
