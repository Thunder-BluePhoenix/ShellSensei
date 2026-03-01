from __future__ import annotations

from pathlib import Path


def detect_repo_type(root: Path) -> str:
    if (root / "Cargo.toml").exists():
        return "rust"
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return "python"
    if (root / "apps.txt").exists() or (root / "sites").exists():
        return "frappe"
    if (root / "docker-compose.yml").exists() and any((root / p).exists() for p in ["kafka", "redpanda"]):
        return "kafka"
    return "generic"


def repo_coaching_hints(repo_type: str) -> list[str]:
    hints = {
        "rust": [
            "Prefer `cargo check` for fast iteration before `cargo build`.",
            "Use workspace-targeted commands (`-p <crate>`) to reduce build time.",
        ],
        "python": [
            "Use virtualenv and lock dependencies for reproducible runs.",
            "Automate lint + tests with a single project command.",
        ],
        "frappe": [
            "Standardize `bench migrate` and backup routines before patch deploys.",
            "Track slow background jobs and worker queue distribution.",
        ],
        "kafka": [
            "Automate consumer lag checks before schema changes.",
            "Validate DLQ and redrive policy in staging first.",
        ],
        "generic": [
            "Promote repeated command chains into named shell functions.",
            "Prefer dry-run and policy checks for risky command patterns.",
        ],
    }
    return hints.get(repo_type, hints["generic"])
