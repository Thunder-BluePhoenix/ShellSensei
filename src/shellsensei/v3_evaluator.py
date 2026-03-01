from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .storage import feedback_counts_since


def _baseline_path(root: Path) -> Path:
    return root / ".shellsensei" / "v3_eval_baseline.json"


def evaluate_quality(conn, root: Path, window_days: int = 14, regression_threshold: float = 10.0) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    counts = feedback_counts_since(conn, since)
    accept = counts.get("accept", 0)
    reject = counts.get("reject", 0)
    total = accept + reject
    accept_rate = round((accept / total) * 100, 2) if total else None

    base_path = _baseline_path(root)
    baseline = None
    if base_path.exists():
        baseline = json.loads(base_path.read_text(encoding="utf-8"))
    baseline_rate = baseline.get("accept_rate_percent") if baseline else None
    regression_alert = False
    regression_drop = None
    if accept_rate is not None and baseline_rate is not None:
        regression_drop = round(baseline_rate - accept_rate, 2)
        regression_alert = regression_drop >= regression_threshold

    return {
        "window_days": window_days,
        "since_utc": since,
        "accept": accept,
        "reject": reject,
        "total": total,
        "accept_rate_percent": accept_rate,
        "baseline_accept_rate_percent": baseline_rate,
        "regression_drop_percent": regression_drop,
        "regression_alert": regression_alert,
    }


def set_baseline(root: Path, payload: dict) -> Path:
    path = _baseline_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    baseline = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "accept_rate_percent": payload.get("accept_rate_percent"),
        "window_days": payload.get("window_days"),
    }
    path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    return path
