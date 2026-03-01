from pathlib import Path

from shellsensei.automate import generate_wrappers
from shellsensei.board import board_path, load_board, post_suggestions
from shellsensei.metrics import build_metrics
from shellsensei.storage import connect, create_session, init_db, insert_commands, record_feedback
from shellsensei.suggest import Suggestion


def _s(name: str, cmd: str = "git status") -> Suggestion:
    return Suggestion(
        kind="alias",
        name=name,
        command=cmd,
        count=5,
        normalized=cmd,
        rationale="r",
        confidence=0.7,
        risk_level="low",
    )


def test_generate_wrappers_writes_manifest_and_scripts(tmp_path: Path) -> None:
    out = tmp_path / "wrappers"
    manifest = generate_wrappers(out, [_s("ss_git"), _s("ss_build", "cargo build")], shell="bash")
    assert manifest["count"] == 2
    assert (out / "ss_git.sh").exists()
    assert (out / "manifest.json").exists()


def test_board_post_and_load(tmp_path: Path) -> None:
    path = board_path(tmp_path)
    post = post_suggestions(path, author="rahul", suggestions=[_s("ss_git")], message="daily picks")
    payload = load_board(path)
    assert post["id"] == 1
    assert payload["posts"][0]["author"] == "rahul"
    assert payload["posts"][0]["suggestions"][0]["name"] == "ss_git"


def test_metrics_phase_criteria(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    conn = connect(db)
    try:
        init_db(conn)
        sid = create_session(conn, "bash", "h")
        insert_commands(conn, sid, [("git status", "git status", "h1")])
        for _ in range(9):
            record_feedback(conn, "ss_git", "git status", "accept")
        record_feedback(conn, "ss_bad", "rm -rf x", "reject")
        metrics = build_metrics(conn)
    finally:
        conn.close()

    assert metrics["feedback"]["total"] == 10
    assert metrics["feedback"]["low_value_rate_percent"] == 10.0
    assert metrics["phase_criteria"]["phase1_feedback_sufficient"] is True
