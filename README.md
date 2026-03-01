# ShellSensei

ShellSensei is a local-first terminal workflow coach.

## Current Capabilities (Phase 0-4 MVP)
- Shell history ingestion for PowerShell, Bash, and Zsh.
- Command normalization for frequency analysis.
- Local SQLite storage with sessions and commands.
- Suggestion confidence + risk classification.
- Feedback tracking and daily/weekly reports.
- Plan metrics with explicit phase-criteria status.
- Phase completion dashboard command (`phase-status`).
- Safety policy checks and team pack export/import.
- Wrapper script generation with rollback hints.
- Shared recommendation board with optional git sync.
- Telemetry opt-in controls.
- Update channel, shell hooks, benchmarks, and beta demo helpers.
- Stretch v2 foundations: repo-aware coaching, local redacted intent parsing, CI linting, IDE tasks integration.
- CLI commands: `init`, `ingest`, `stats`, `doctor`, `suggest`, `apply`, `feedback`, `report`, `metrics`, `phase-status`, `policy`, `policy-simulate`, `pack`, `automate`, `board`, `telemetry`, `version`, `self-update`, `hook`, `benchmark`, `coach`, `llm-parse`, `intent-profile`, `ci-lint`, `ide`, `quality-gate`, `evaluate`, `health`, `soak`, `upgrade-check`.

## Quick Start

```bash
# From project root
python -m shellsensei init
python -m shellsensei ingest --shell auto
python -m shellsensei stats
python -m shellsensei stats --format markdown --output stats.md
python -m shellsensei stats --format json
python -m shellsensei doctor
python -m shellsensei suggest --min-count 3
python -m shellsensei suggest --shell powershell
python -m shellsensei suggest --shell bash --format markdown --output suggestions_bash.md
python -m shellsensei suggest --format markdown --output suggestions.md
python -m shellsensei suggest --format json
python -m shellsensei suggest --max-risk medium
python -m shellsensei apply --shell bash --interactive
python -m shellsensei apply --shell powershell --all --dry-run
python -m shellsensei apply --shell bash --all
python -m shellsensei apply --shell bash --name ss_git --name ss_cargo
python -m shellsensei feedback --name ss_git --normalized "git status" --decision accept
python -m shellsensei report --period weekly --format markdown --output weekly_report.md
python -m shellsensei policy --max-risk medium
python -m shellsensei pack export --name team-core --output ./team-core.shellsensei.json
python -m shellsensei pack import --input ./team-core.shellsensei.json --dry-run
python -m shellsensei telemetry status
python -m shellsensei telemetry enable
python -m shellsensei metrics --format json
python -m shellsensei phase-status --format text
python -m shellsensei automate --shell auto --out-dir ./.shellsensei/wrappers
python -m shellsensei board post --root . --message "daily recommendations" --git-sync
python -m shellsensei board list --root .
python -m shellsensei board approve --root . --post-id 1 --reviewer lead
python -m shellsensei board activate --root . --post-id 1
python -m shellsensei board retire --root . --post-id 1 --note "superseded"
python -m shellsensei policy-simulate --project-root . --max-risk medium --format json
python -m shellsensei version
python -m shellsensei benchmark --samples 20000 --format json
python -m shellsensei quality-gate --format text
python -m shellsensei evaluate --project-root . --window-days 14 --format text
python -m shellsensei health --format text
python -m shellsensei soak --iterations 20 --format text
python -m shellsensei upgrade-check --project-root . --format text
python -m shellsensei hook show --shell bash
python -m shellsensei hook install --shell powershell --enable-auto --dry-run
python -m shellsensei coach --path .
python -m shellsensei intent-profile --project-root . --pattern "secret_[A-Za-z0-9]+"
python -m shellsensei llm-parse --project-root . --profile custom --text "suggest aliases for my build workflow with key sk-123..."
python -m shellsensei ci-lint --path . --profile strict --format json --output ./ci_lint_report.json
python -m shellsensei ide vscode --path .
python -m shellsensei ide snippets --path .
python -m shellsensei ide diagnostics --path . --output ./.shellsensei/diagnostics.json
```

## Optional install (editable)

```bash
pip install -e .
shellsensei --help
```

## Installer scripts

```bash
./scripts/install.sh
```

```powershell
.\scripts\install.ps1
```

## Beta Demo (under 3 minutes)

```bash
python -m shellsensei init
python -m shellsensei ingest --shell auto --limit 300
python -m shellsensei suggest --max-risk medium --format markdown --output ./.shellsensei/suggestions.md
python -m shellsensei apply --shell auto --interactive --dry-run
python -m shellsensei report --period weekly --format markdown --output ./.shellsensei/weekly_report.md
```
