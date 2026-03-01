from shellsensei.phase_status import evaluate_phase_status


def test_phase_status_evaluation() -> None:
    metrics = {
        "summary": {"total_commands": 50, "unique_normalized": 20},
        "feedback": {"total": 12, "low_value_rate_percent": 8.3},
    }
    phases = evaluate_phase_status(metrics, board_posts=2)
    assert phases["phase0_foundation"] == "complete"
    assert phases["phase1_personal_coaching"] == "complete"
    assert phases["phase3_team_intelligence"] == "complete"


def test_phase_status_in_progress_without_feedback() -> None:
    metrics = {
        "summary": {"total_commands": 10, "unique_normalized": 5},
        "feedback": {"total": 0, "low_value_rate_percent": None},
    }
    phases = evaluate_phase_status(metrics, board_posts=0)
    assert phases["phase1_personal_coaching"] == "in_progress"
    assert phases["phase3_team_intelligence"] == "in_progress"
