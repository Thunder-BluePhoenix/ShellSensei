from pathlib import Path

from shellsensei.pack import export_pack, import_pack
from shellsensei.policy import check_command_policy
from shellsensei.report import build_report_payload
from shellsensei.risk import classify_risk, risk_allows
from shellsensei.storage import (
    connect,
    create_session,
    init_db,
    insert_commands,
    record_feedback,
)
from shellsensei.suggest import Suggestion


def test_risk_classifier_and_policy_gate() -> None:
    assert classify_risk("rm -rf /tmp/x").level == "high"
    assert classify_risk("sudo apt update").level == "medium"
    assert classify_risk("git status").level == "low"
    assert risk_allows("low", "medium")
    assert not risk_allows("high", "medium")


def test_report_payload_has_feedback_and_period_top(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    conn = connect(db)
    try:
        init_db(conn)
        s = create_session(conn, "bash", "h")
        insert_commands(
            conn,
            s,
            [
                ("git status", "git status", "h1"),
                ("git status", "git status", "h1"),
                ("cargo check", "cargo check", "h2"),
            ],
        )
        record_feedback(conn, "ss_git", "git status", "accept")
        payload = build_report_payload(conn, period="weekly", top=5)
    finally:
        conn.close()

    assert payload["period"] == "weekly"
    assert payload["feedback"]["accept"] == 1
    assert payload["top_commands_period"][0]["command"] == "git status"


def test_pack_export_import_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "team-pack.json"
    suggestions = [
        Suggestion(
            kind="alias",
            name="ss_git",
            command="git status",
            count=5,
            normalized="git status",
            rationale="r",
            confidence=0.77,
            risk_level="low",
        )
    ]
    export_pack(path, name="team-core", shell="bash", suggestions=suggestions)
    shell, loaded = import_pack(path)
    assert shell == "bash"
    assert loaded[0].name == "ss_git"
    assert loaded[0].confidence == 0.77


def test_policy_check_finds_high_risk_command(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    conn = connect(db)
    try:
        init_db(conn)
        s = create_session(conn, "bash", "h")
        insert_commands(
            conn,
            s,
            [
                ("rm -rf build", "rm -rf build", "x1"),
                ("rm -rf build", "rm -rf build", "x1"),
                ("git status", "git status", "x2"),
            ],
        )
        issues = check_command_policy(conn, max_allowed_risk="medium", sample_top=10)
    finally:
        conn.close()
    assert issues
    assert "rm -rf build" in issues[0].command
