from __future__ import annotations

import time

from .normalize import command_hash, normalize_command


def run_normalize_benchmark(sample_count: int = 10000) -> dict:
    samples = [f'cargo check -p core --job {i} "https://example.com/{i}" /tmp/{i}' for i in range(sample_count)]
    start = time.perf_counter()
    out = []
    for s in samples:
        n = normalize_command(s)
        out.append(command_hash(n))
    elapsed = time.perf_counter() - start
    ops = sample_count / elapsed if elapsed > 0 else 0
    return {
        "sample_count": sample_count,
        "elapsed_seconds": round(elapsed, 4),
        "ops_per_second": round(ops, 1),
        "hashes_generated": len(out),
    }
