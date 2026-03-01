from __future__ import annotations

from .repo_context import detect_repo_type
from .suggest import Suggestion
from .v2_context import load_context


def _repo_bonus(repo_type: str, command: str) -> float:
    c = command.lower()
    if repo_type == "rust" and "cargo" in c:
        return 0.18
    if repo_type == "python" and ("python" in c or "pip" in c or "pytest" in c):
        return 0.18
    if repo_type == "frappe" and "bench" in c:
        return 0.18
    if repo_type == "kafka" and ("kafka" in c or "consumer" in c or "topic" in c):
        return 0.18
    return 0.0


def rerank_suggestions(suggestions: list[Suggestion], project_root, threshold: float = 0.35) -> list[Suggestion]:
    repo = detect_repo_type(project_root)
    ctx = load_context(project_root)
    accepted = ctx.get("accepted_suggestions", {})
    rejected = ctx.get("rejected_suggestions", {})
    reranked: list[tuple[float, Suggestion]] = []
    for s in suggestions:
        score = s.confidence
        score += _repo_bonus(repo, s.command)
        score += min(accepted.get(s.name, 0) * 0.02, 0.1)
        score -= min(rejected.get(s.name, 0) * 0.03, 0.15)
        score = max(0.0, min(score, 1.0))
        reranked.append((score, s))
    reranked.sort(key=lambda x: x[0], reverse=True)
    return [s for score, s in reranked if score >= threshold]
