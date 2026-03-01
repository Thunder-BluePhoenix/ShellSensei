import json

from shellsensei.cli import (
    _interactive_select_suggestions,
    _render_suggest_markdown,
    _render_suggest_text,
    _resolve_suggest_shell,
    _suggestion_snippet,
)
from shellsensei.suggest import Suggestion, build_suggestions


def test_build_suggestions_generates_alias_and_function_with_unique_names() -> None:
    patterns = [
        ("git status", "git status", 5),
        ("git status", "git status -s", 4),
        ("cat file | rg todo", "cat file | rg todo", 3),
    ]
    suggestions = build_suggestions(patterns, prefix="ss")
    names = [s.name for s in suggestions]
    kinds = [s.kind for s in suggestions]

    assert names[0] == "ss_git"
    assert names[1] == "ss_git_2"
    assert "function" in kinds


def test_suggestion_snippet_formats_alias_and_function() -> None:
    alias = Suggestion(
        kind="alias",
        name="ss_git",
        command='git commit -m "x"',
        count=3,
        normalized="git commit -m <str>",
        rationale="r",
    )
    function = Suggestion(
        kind="function",
        name="ss_pipe",
        command="cat a | rg b",
        count=3,
        normalized="cat a | rg b",
        rationale="r",
    )
    assert _suggestion_snippet(alias, shell="bash").startswith('alias ss_git="')
    assert "ss_pipe() {" in _suggestion_snippet(function, shell="zsh")
    assert _suggestion_snippet(alias, shell="powershell").startswith("function ss_git {")


def test_render_suggest_markdown_and_text() -> None:
    suggestions = [
        Suggestion(
            kind="alias",
            name="ss_git",
            command="git status",
            count=6,
            normalized="git status",
            rationale="simple command repeated 6 times; alias reduces typing",
        )
    ]
    md = _render_suggest_markdown(suggestions, shell="bash")
    txt = _render_suggest_text(suggestions, shell="bash")
    assert md.startswith("# ShellSensei Suggestions")
    assert "- **Shell profile**: `bash`" in md
    assert "| Type | Name | Repeats | Confidence | Risk | Reason |" in md
    assert "```bash" in md
    assert txt.startswith("ShellSensei Suggestions")
    assert "[ALIAS] ss_git" in txt
    assert "Confidence:" in txt


def test_suggest_json_payload_shape() -> None:
    suggestion = Suggestion(
        kind="alias",
        name="ss_git",
        command="git status",
        count=6,
        normalized="git status",
        rationale="simple command repeated 6 times; alias reduces typing",
    )
    payload = {
        "shell": "bash",
        "suggestions": [
            {
                "kind": suggestion.kind,
                "name": suggestion.name,
                "count": suggestion.count,
                "normalized": suggestion.normalized,
                "command": suggestion.command,
                "rationale": suggestion.rationale,
                "snippet": _suggestion_snippet(suggestion, shell="bash"),
            }
        ],
    }
    encoded = json.dumps(payload, indent=2)
    decoded = json.loads(encoded)
    assert decoded["shell"] == "bash"
    assert decoded["suggestions"][0]["name"] == "ss_git"
    assert decoded["suggestions"][0]["snippet"].startswith("alias ss_git=")


def test_resolve_suggest_shell_auto_maps_to_current_platform() -> None:
    shell = _resolve_suggest_shell("auto")
    assert shell in {"bash", "powershell"}


def test_interactive_select_suggestions_yes_no_quit(monkeypatch) -> None:
    suggestions = [
        Suggestion(
            kind="alias",
            name="ss_a",
            command="git status",
            count=5,
            normalized="git status",
            rationale="r",
        ),
        Suggestion(
            kind="alias",
            name="ss_b",
            command="cargo check",
            count=4,
            normalized="cargo check",
            rationale="r",
        ),
        Suggestion(
            kind="function",
            name="ss_c",
            command="cat a | rg b",
            count=3,
            normalized="cat a | rg b",
            rationale="r",
        ),
    ]
    answers = iter(["y", "n", "q"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    selected = _interactive_select_suggestions(suggestions)
    assert [s.name for s in selected] == ["ss_a"]
