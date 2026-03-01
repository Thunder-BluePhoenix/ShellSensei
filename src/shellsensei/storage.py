from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    def _open(path: Path) -> sqlite3.Connection:
        path.parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(path)
        c.execute("PRAGMA journal_mode=WAL;")
        c.execute("PRAGMA foreign_keys=ON;")
        return c

    try:
        return _open(db_path)
    except sqlite3.OperationalError:
        fallback = (Path.cwd() / ".shellsensei" / "shellsensei.db").resolve()
        if fallback == db_path.resolve():
            raise
        return _open(fallback)


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            shell TEXT NOT NULL,
            source_path TEXT NOT NULL,
            imported_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            raw_command TEXT NOT NULL,
            normalized_command TEXT NOT NULL,
            command_hash TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_commands_session ON commands(session_id);
        CREATE INDEX IF NOT EXISTS idx_commands_hash ON commands(command_hash);
        CREATE INDEX IF NOT EXISTS idx_commands_normalized ON commands(normalized_command);

        CREATE TABLE IF NOT EXISTS suggestion_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            suggestion_name TEXT NOT NULL,
            normalized_command TEXT NOT NULL,
            decision TEXT NOT NULL,
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_feedback_name ON suggestion_feedback(suggestion_name);
        CREATE INDEX IF NOT EXISTS idx_feedback_decision ON suggestion_feedback(decision);

        CREATE TABLE IF NOT EXISTS telemetry_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            opt_in INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS telemetry_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT
        );
        """
    )
    conn.execute("INSERT OR IGNORE INTO telemetry_settings(id, opt_in) VALUES (1, 0)")
    conn.commit()


def create_session(conn: sqlite3.Connection, shell: str, source_path: str) -> str:
    session_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO sessions(id, created_at, shell, source_path, imported_count) VALUES (?, ?, ?, ?, 0)",
        (session_id, utc_now(), shell, source_path),
    )
    conn.commit()
    return session_id


def insert_commands(
    conn: sqlite3.Connection,
    session_id: str,
    commands: list[tuple[str, str, str]],
) -> int:
    now = utc_now()
    conn.executemany(
        """
        INSERT INTO commands(session_id, raw_command, normalized_command, command_hash, imported_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(session_id, raw, norm, chash, now) for raw, norm, chash in commands],
    )
    conn.execute(
        "UPDATE sessions SET imported_count = imported_count + ? WHERE id = ?",
        (len(commands), session_id),
    )
    conn.commit()
    return len(commands)


def get_summary(conn: sqlite3.Connection) -> dict[str, int]:
    total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    total_commands = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    unique_normalized = conn.execute(
        "SELECT COUNT(DISTINCT normalized_command) FROM commands"
    ).fetchone()[0]
    return {
        "total_sessions": total_sessions,
        "total_commands": total_commands,
        "unique_normalized": unique_normalized,
    }


def top_commands(conn: sqlite3.Connection, limit: int = 10) -> list[tuple[str, int]]:
    rows = conn.execute(
        """
        SELECT normalized_command, COUNT(*) as c
        FROM commands
        GROUP BY normalized_command
        ORDER BY c DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def top_commands_since(conn: sqlite3.Connection, since_iso: str, limit: int = 10) -> list[tuple[str, int]]:
    rows = conn.execute(
        """
        SELECT normalized_command, COUNT(*) as c
        FROM commands
        WHERE imported_at >= ?
        GROUP BY normalized_command
        ORDER BY c DESC
        LIMIT ?
        """,
        (since_iso, limit),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def repeated_patterns(
    conn: sqlite3.Connection,
    min_count: int = 3,
    limit: int = 20,
) -> list[tuple[str, str, int]]:
    rows = conn.execute(
        """
        WITH raw_counts AS (
            SELECT normalized_command, raw_command, COUNT(*) AS raw_count
            FROM commands
            GROUP BY normalized_command, raw_command
        ),
        ranked AS (
            SELECT
                normalized_command,
                raw_command,
                raw_count,
                ROW_NUMBER() OVER (
                    PARTITION BY normalized_command
                    ORDER BY raw_count DESC, raw_command ASC
                ) AS rn
            FROM raw_counts
        ),
        totals AS (
            SELECT normalized_command, SUM(raw_count) AS total_count
            FROM raw_counts
            GROUP BY normalized_command
        )
        SELECT
            totals.normalized_command,
            ranked.raw_command,
            totals.total_count
        FROM totals
        JOIN ranked ON ranked.normalized_command = totals.normalized_command
        WHERE ranked.rn = 1
          AND totals.total_count >= ?
        ORDER BY totals.total_count DESC, totals.normalized_command ASC
        LIMIT ?
        """,
        (min_count, limit),
    ).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


def record_feedback(
    conn: sqlite3.Connection,
    suggestion_name: str,
    normalized_command: str,
    decision: str,
    notes: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO suggestion_feedback(created_at, suggestion_name, normalized_command, decision, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (utc_now(), suggestion_name, normalized_command, decision, notes),
    )
    conn.commit()


def feedback_summary(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        "SELECT decision, COUNT(*) FROM suggestion_feedback GROUP BY decision"
    ).fetchall()
    counts = {"accept": 0, "reject": 0}
    for decision, count in rows:
        counts[decision] = count
    return counts


def feedback_counts_since(conn: sqlite3.Connection, since_iso: str) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT decision, COUNT(*)
        FROM suggestion_feedback
        WHERE created_at >= ?
        GROUP BY decision
        """,
        (since_iso,),
    ).fetchall()
    counts = {"accept": 0, "reject": 0}
    for decision, count in rows:
        counts[decision] = count
    return counts


def set_telemetry_opt_in(conn: sqlite3.Connection, enabled: bool) -> None:
    conn.execute("UPDATE telemetry_settings SET opt_in = ? WHERE id = 1", (1 if enabled else 0,))
    conn.commit()


def get_telemetry_opt_in(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT opt_in FROM telemetry_settings WHERE id = 1").fetchone()
    return bool(row[0]) if row else False


def log_telemetry_event(conn: sqlite3.Connection, event_type: str, payload_json: str | None = None) -> None:
    if not get_telemetry_opt_in(conn):
        return
    conn.execute(
        """
        INSERT INTO telemetry_events(created_at, event_type, payload_json)
        VALUES (?, ?, ?)
        """,
        (utc_now(), event_type, payload_json),
    )
    conn.commit()
