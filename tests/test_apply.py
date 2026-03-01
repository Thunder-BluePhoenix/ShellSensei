from pathlib import Path

from shellsensei.apply import (
    backup_profile,
    render_profile_block,
    upsert_managed_block,
)
from shellsensei.suggest import Suggestion


def _sample_suggestion(name: str = "ss_git") -> Suggestion:
    return Suggestion(
        kind="alias",
        name=name,
        command="git status",
        count=6,
        normalized="git status",
        rationale="simple command repeated 6 times; alias reduces typing",
    )


def test_render_profile_block_contains_markers() -> None:
    block = render_profile_block([_sample_suggestion()], shell="bash")
    assert "# >>> ShellSensei (bash) >>>" in block
    assert "# <<< ShellSensei <<<" in block
    assert 'alias ss_git="git status"' in block


def test_upsert_managed_block_inserts_when_missing() -> None:
    existing = "export PATH=$PATH:/custom/bin\n"
    block = render_profile_block([_sample_suggestion()], shell="bash")
    updated = upsert_managed_block(existing, block, shell="bash")
    assert "export PATH=$PATH:/custom/bin" in updated
    assert "# >>> ShellSensei (bash) >>>" in updated


def test_upsert_managed_block_replaces_existing_section() -> None:
    old = (
        "export X=1\n\n"
        "# >>> ShellSensei (bash) >>>\n"
        "old content\n"
        "# <<< ShellSensei <<<\n\n"
        "export Y=2\n"
    )
    block = render_profile_block([_sample_suggestion("ss_new")], shell="bash")
    updated = upsert_managed_block(old, block, shell="bash")
    assert "old content" not in updated
    assert "ss_new" in updated
    assert "export X=1" in updated
    assert "export Y=2" in updated


def test_backup_profile_creates_timestamped_copy(tmp_path: Path) -> None:
    profile = tmp_path / ".bashrc"
    profile.write_text("export A=1\n", encoding="utf-8")
    backup = backup_profile(profile)
    assert backup is not None
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "export A=1\n"
