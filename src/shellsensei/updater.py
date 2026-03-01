from __future__ import annotations

import subprocess
import sys


def run_self_update(package_name: str = "shellsensei") -> tuple[int, str]:
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_name]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()
