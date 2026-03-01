from __future__ import annotations

import platform
import sys
import tempfile
from pathlib import Path

from .benchmark import run_normalize_benchmark
from .storage import connect, create_session, get_summary, init_db, insert_commands
from .suggest import suggest_from_db


def health_check(db_path: Path, min_ops_per_sec: float = 15000.0) -> dict:
    conn = connect(db_path)
    try:
        init_db(conn)
        summary = get_summary(conn)
    finally:
        conn.close()
    bench = run_normalize_benchmark(sample_count=5000)
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "db_path": str(db_path),
        "summary": summary,
        "bench": bench,
        "slo": {
            "min_ops_per_sec": min_ops_per_sec,
            "bench_ok": bench["ops_per_second"] >= min_ops_per_sec,
        },
    }


def soak_test(iterations: int = 20) -> dict:
    failures = []
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "soak.db"
        for i in range(iterations):
            try:
                conn = connect(db_path)
                init_db(conn)
                sid = create_session(conn, "bash", f"soak-{i}")
                cmds = [(f"cargo check -p core {j}", "cargo check -p core <num>", "h1") for j in range(50)]
                insert_commands(conn, sid, cmds)
                _ = suggest_from_db(conn, min_count=1, limit=5, prefix="ss")
                conn.close()
            except Exception as e:
                failures.append({"iteration": i, "error": str(e)})
    return {
        "iterations": iterations,
        "failures": failures,
        "failure_count": len(failures),
        "ok": len(failures) == 0,
    }


def upgrade_check(root: Path, db_path: Path) -> dict:
    checks = []
    checks.append({"name": "python>=3.9", "ok": sys.version_info >= (3, 9), "value": sys.version.split()[0]})
    checks.append({"name": "migration_doc", "ok": (root / "docs" / "MIGRATION_V1_TO_V2.md").exists()})
    checks.append({"name": "plan_exists", "ok": (root / "plan.md").exists()})
    try:
        conn = connect(db_path)
        init_db(conn)
        conn.close()
        checks.append({"name": "db_open", "ok": True})
    except Exception as e:
        checks.append({"name": "db_open", "ok": False, "error": str(e)})
    all_ok = all(c["ok"] for c in checks)
    return {"checks": checks, "all_ok": all_ok}
