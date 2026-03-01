from pathlib import Path

from shellsensei.board import board_path, post_suggestions, review_post
from shellsensei.intent_engine import parse_intent, save_custom_profile
from shellsensei.suggest import Suggestion
from shellsensei.v2_ranker import rerank_suggestions


def _s(name: str, cmd: str, conf: float = 0.5) -> Suggestion:
    return Suggestion(
        kind="alias",
        name=name,
        command=cmd,
        count=4,
        normalized=cmd,
        rationale="r",
        confidence=conf,
        risk_level="low",
    )


def test_intent_engine_custom_profile(tmp_path: Path) -> None:
    save_custom_profile(tmp_path, [r"secret_[A-Za-z0-9]+"])
    parsed = parse_intent("please suggest secret_abcd now", root=tmp_path, profile="custom", backend="rule")
    assert parsed["intent"] == "suggest"
    assert "<REDACTED>" in parsed["redacted_text"]
    assert parsed["backend"] == "rule"


def test_board_review_flow(tmp_path: Path) -> None:
    path = board_path(tmp_path)
    post = post_suggestions(path, author="rahul", suggestions=[_s("ss_git", "git status")], message="test")
    review = review_post(path, post_id=post["id"], reviewer="lead", decision="approved", note="ok")
    assert review["decision"] == "approved"


def test_v2_ranker_repo_bonus(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n", encoding="utf-8")
    suggestions = [_s("ss_cargo", "cargo check -p core", conf=0.3), _s("ss_git", "git status", conf=0.4)]
    ranked = rerank_suggestions(suggestions, project_root=tmp_path, threshold=0.35)
    assert ranked
    assert ranked[0].name == "ss_cargo"
