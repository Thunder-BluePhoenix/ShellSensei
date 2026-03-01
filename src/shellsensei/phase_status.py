from __future__ import annotations


def evaluate_phase_status(metrics: dict, board_posts: int) -> dict:
    total_commands = metrics["summary"]["total_commands"]
    unique_normalized = metrics["summary"]["unique_normalized"]
    feedback_total = metrics["feedback"]["total"]
    low_value_rate = metrics["feedback"]["low_value_rate_percent"]

    phase0 = "complete" if total_commands > 0 and unique_normalized > 0 else "incomplete"
    if feedback_total >= 10 and low_value_rate is not None and low_value_rate < 10.0:
        phase1 = "complete"
    elif total_commands > 0:
        phase1 = "in_progress"
    else:
        phase1 = "incomplete"

    # Feature-level completion for MVP features implemented in codebase.
    phase2 = "complete"
    phase3 = "complete" if board_posts > 0 else "in_progress"
    phase4 = "complete"

    return {
        "phase0_foundation": phase0,
        "phase1_personal_coaching": phase1,
        "phase2_safe_automation": phase2,
        "phase3_team_intelligence": phase3,
        "phase4_productization": phase4,
    }
