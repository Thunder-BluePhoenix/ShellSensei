from pathlib import Path

from shellsensei.board import activate_post, board_path, post_suggestions, review_post_with_rules, retire_post
from shellsensei.policy_engine import effective_max_risk, resolve_policy, simulate_apply
from shellsensei.suggest import Suggestion
from shellsensei.v3_evaluator import evaluate_quality, set_baseline
from shellsensei.v3_ops import soak_test, upgrade_check
from shellsensei.storage import connect, create_session, init_db, insert_commands, record_feedback


def _s(name: str) -> Suggestion:
    return Suggestion(
        kind="alias",
        name=name,
        command="git status",
        count=3,
        normalized="git status",
        rationale="r",
        confidence=0.6,
        risk_level="low",
    )


def test_policy_effective_risk_and_simulation(tmp_path: Path) -> None:
    (tmp_path / "shellsensei-policy.toml").write_text("[risk]\nmax_allowed='low'\n", encoding="utf-8")
    policy = resolve_policy(tmp_path)
    assert effective_max_risk("high", policy["risk"]["max_allowed"]) == "low"
    sim = simulate_apply(policy, [{"name": "x", "risk": "medium"}], requested_max_risk="high")
    assert sim["effective_max_risk"] == "low"
    assert sim["can_apply"] is False


def test_board_lifecycle_with_required_approvers(tmp_path: Path) -> None:
    path = board_path(tmp_path)
    post = post_suggestions(path, author="a", suggestions=[_s("ss_git")], message="m")
    review_post_with_rules(path, post["id"], reviewer="r1", decision="approved", required_approvers=2)
    review_post_with_rules(path, post["id"], reviewer="r2", decision="approved", required_approvers=2)
    active = activate_post(path, post["id"])
    assert active["status"] == "active"
    retired = retire_post(path, post["id"], note="done")
    assert retired["status"] == "retired"


def test_v3_evaluator_baseline_and_regression(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    conn = connect(db)
    try:
        init_db(conn)
        sid = create_session(conn, "bash", "h")
        insert_commands(conn, sid, [("git status", "git status", "h1")])
        for _ in range(8):
            record_feedback(conn, "ss_a", "git status", "accept")
        for _ in range(2):
            record_feedback(conn, "ss_b", "git status", "reject")
        first = evaluate_quality(conn, root=tmp_path, window_days=30, regression_threshold=5)
    finally:
        conn.close()
    set_baseline(tmp_path, first)
    conn = connect(db)
    try:
        for _ in range(9):
            record_feedback(conn, "ss_c", "git status", "reject")
        second = evaluate_quality(conn, root=tmp_path, window_days=30, regression_threshold=5)
    finally:
        conn.close()
    assert second["regression_alert"] is True


def test_v3_ops_smoke(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    checks = upgrade_check(tmp_path, db)
    assert "checks" in checks
    soak = soak_test(iterations=3)
    assert soak["iterations"] == 3
