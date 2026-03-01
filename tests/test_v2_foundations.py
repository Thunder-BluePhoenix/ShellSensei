from pathlib import Path

from shellsensei.benchmark import run_normalize_benchmark
from shellsensei.ci_lint import lint_shell_files
from shellsensei.hooks import hook_snippet
from shellsensei.ide import write_diagnostics_bridge, write_vscode_snippets, write_vscode_tasks
from shellsensei.llm_local import parse_intent_local, redact_sensitive
from shellsensei.repo_context import detect_repo_type, repo_coaching_hints
from shellsensei.risk import classify_risk


def test_benchmark_payload_shape() -> None:
    payload = run_normalize_benchmark(sample_count=1000)
    assert payload["sample_count"] == 1000
    assert payload["hashes_generated"] == 1000
    assert payload["ops_per_second"] > 0


def test_hook_snippet_contains_markers() -> None:
    bash = hook_snippet("bash")
    ps = hook_snippet("powershell")
    assert "ShellSensei Hook (bash)" in bash
    assert "ShellSensei Hook (powershell)" in ps
    auto = hook_snippet("bash", enable_auto=True)
    assert "PROMPT_COMMAND=" in auto


def test_repo_detection_and_hints(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname='x'\n", encoding="utf-8")
    repo = detect_repo_type(tmp_path)
    assert repo == "rust"
    hints = repo_coaching_hints(repo)
    assert hints


def test_local_llm_redaction_and_intent() -> None:
    text = "please suggest alias with key sk-1234567890abcdef"
    redacted = redact_sensitive(text)
    assert "sk-1234567890abcdef" not in redacted
    parsed = parse_intent_local(text)
    assert parsed["intent"] == "suggest"


def test_ci_lint_finds_risky_line(tmp_path: Path) -> None:
    f = tmp_path / "deploy.sh"
    f.write_text("echo ok\nrm -rf /tmp/x\n", encoding="utf-8")
    findings = lint_shell_files(tmp_path)
    assert findings
    assert classify_risk(findings[0]["text"]).level in {"medium", "high"}


def test_ide_vscode_tasks_write(tmp_path: Path) -> None:
    out = write_vscode_tasks(tmp_path)
    assert out.exists()
    assert "tasks" in out.read_text(encoding="utf-8")


def test_ide_snippets_and_diagnostics(tmp_path: Path) -> None:
    snip = write_vscode_snippets(tmp_path)
    assert snip.exists()
    diag = write_diagnostics_bridge(tmp_path, diagnostics=[{"msg": "x"}])
    assert diag.exists()
