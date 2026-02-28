# ShellSensei

ShellSensei is a local-first terminal workflow coach.

## Current MVP (Phase 0)
- Shell history ingestion for PowerShell, Bash, and Zsh.
- Command normalization for frequency analysis.
- Local SQLite storage with sessions and commands.
- CLI commands: `init`, `ingest`, `stats`, `doctor`, `suggest`.

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
```

## Optional install (editable)

```bash
pip install -e .
shellsensei --help
```
