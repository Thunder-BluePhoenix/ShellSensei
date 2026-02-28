from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


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
        """
    )
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
