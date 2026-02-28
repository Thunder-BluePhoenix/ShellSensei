from pathlib import Path

from shellsensei.storage import (
    connect,
    create_session,
    get_summary,
    init_db,
    insert_commands,
    repeated_patterns,
    top_commands,
)


def test_storage_summary_and_top_commands(tmp_path: Path) -> None:
    db_path = tmp_path / "shellsensei.db"
    conn = connect(db_path)
    try:
        init_db(conn)
        session = create_session(conn, shell="powershell", source_path="test-history")
        insert_commands(
            conn,
            session,
            [
                ("git status", "git status", "h1"),
                ("git status", "git status", "h1"),
                ("cargo check -p core", "cargo check -p core", "h2"),
            ],
        )
        summary = get_summary(conn)
        top = top_commands(conn, limit=2)
    finally:
        conn.close()

    assert summary["total_sessions"] == 1
    assert summary["total_commands"] == 3
    assert summary["unique_normalized"] == 2
    assert top[0] == ("git status", 2)


def test_repeated_patterns_selects_best_raw_variant(tmp_path: Path) -> None:
    db_path = tmp_path / "shellsensei.db"
    conn = connect(db_path)
    try:
        init_db(conn)
        session = create_session(conn, shell="bash", source_path="test-history")
        insert_commands(
            conn,
            session,
            [
                ("git status", "git status", "h1"),
                ("git status", "git status", "h1"),
                ("git status -s", "git status", "h1"),
                ("cargo check", "cargo check", "h2"),
                ("cargo check", "cargo check", "h2"),
            ],
        )
        patterns = repeated_patterns(conn, min_count=2, limit=5)
    finally:
        conn.close()

    # format: (normalized, representative_raw, total_count)
    assert patterns[0] == ("git status", "git status", 3)
    assert ("cargo check", "cargo check", 2) in patterns
