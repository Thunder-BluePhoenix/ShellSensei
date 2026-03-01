from __future__ import annotations

import tomllib
from pathlib import Path


def _default_policy() -> dict:
    return {
        "risk": {"max_allowed": "medium"},
        "board": {"required_approvers": 1},
    }


def _merge(base: dict, override: dict) -> dict:
    out = {**base}
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def resolve_policy(project_root: Path) -> dict:
    default = _default_policy()
    global_path = Path.home() / ".shellsensei" / "shellsensei-policy.toml"
    repo_path = project_root / "shellsensei-policy.toml"
    global_policy = _load_toml(global_path)
    repo_policy = _load_toml(repo_path)
    merged = _merge(default, global_policy)
    merged = _merge(merged, repo_policy)
    return merged


def effective_max_risk(requested: str, policy_max: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    # stricter (lower order) wins
    return requested if order[requested] < order[policy_max] else policy_max


def simulate_apply(policy: dict, suggestion_payload: list[dict], requested_max_risk: str) -> dict:
    policy_max = policy.get("risk", {}).get("max_allowed", "medium")
    final_max = effective_max_risk(requested_max_risk, policy_max)
    order = {"low": 0, "medium": 1, "high": 2}
    violations = []
    for s in suggestion_payload:
        risk = s.get("risk", "low")
        if order[risk] > order[final_max]:
            violations.append(
                {
                    "name": s.get("name"),
                    "risk": risk,
                    "reason": f"risk exceeds allowed level ({final_max})",
                }
            )
    return {
        "requested_max_risk": requested_max_risk,
        "policy_max_risk": policy_max,
        "effective_max_risk": final_max,
        "violations": violations,
        "can_apply": len(violations) == 0,
    }
