from __future__ import annotations

import subprocess
import sys

from .benchmark import run_normalize_benchmark


def run_quality_gate(min_ops_per_sec: float = 15000.0) -> dict:
    pytest_run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        capture_output=True,
        text=True,
    )
    bench = run_normalize_benchmark(sample_count=10000)
    tests_ok = pytest_run.returncode == 0
    bench_ok = bench["ops_per_second"] >= min_ops_per_sec
    return {
        "tests_ok": tests_ok,
        "tests_output_tail": (pytest_run.stdout or "")[-1000:],
        "bench": bench,
        "bench_ok": bench_ok,
        "min_ops_per_sec": min_ops_per_sec,
        "overall_ok": tests_ok and bench_ok,
    }
