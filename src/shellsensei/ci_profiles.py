from __future__ import annotations

import json
from pathlib import Path


def load_ci_profile(profile: str, custom_file: str | None = None) -> dict:
    defaults = {
        "baseline": {"max_risk": "high"},
        "strict": {"max_risk": "medium"},
    }
    if profile in defaults:
        return defaults[profile]
    if profile == "custom" and custom_file:
        path = Path(custom_file).expanduser().resolve()
        return json.loads(path.read_text(encoding="utf-8"))
    return defaults["baseline"]
