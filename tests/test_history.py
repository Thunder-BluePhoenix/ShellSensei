from pathlib import Path

from shellsensei.history import HistorySource, read_history_lines


def test_read_history_lines_missing_file() -> None:
    source = HistorySource(shell="bash", path=Path("Z:/definitely/missing/.bash_history"))
    assert read_history_lines(source) == []


def test_read_history_lines_parses_zsh_extended_history(tmp_path: Path) -> None:
    history_file = tmp_path / ".zsh_history"
    history_file.write_text(
        ": 1700000000:0;git status\n"
        ": 1700000001:0;cargo check\n"
        "plain-command\n",
        encoding="utf-8",
    )

    source = HistorySource(shell="zsh", path=history_file)
    lines = read_history_lines(source)
    assert lines == ["git status", "cargo check", "plain-command"]


def test_read_history_lines_limit_keeps_last_n(tmp_path: Path) -> None:
    history_file = tmp_path / ".bash_history"
    history_file.write_text("a\nb\nc\nd\n", encoding="utf-8")
    source = HistorySource(shell="bash", path=history_file)
    assert read_history_lines(source, limit=2) == ["c", "d"]
