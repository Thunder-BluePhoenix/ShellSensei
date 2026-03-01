# How To Use ShellSensei

## 1. Setup

From project root:

```bash
pip install -e .
```

Or run directly without install:

```bash
python -m shellsensei --help
```

## 2. Initialize and Ingest History

```bash
python -m shellsensei init
python -m shellsensei ingest --shell auto
```

Optional: limit import size for fast trials.

```bash
python -m shellsensei ingest --shell auto --limit 300
```

## 3. Inspect Current Usage

```bash
python -m shellsensei stats
python -m shellsensei stats --format markdown --output ./.shellsensei/stats.md
python -m shellsensei stats --format json
```

## 4. Generate Suggestions

```bash
python -m shellsensei suggest --min-count 3
python -m shellsensei suggest --shell powershell
python -m shellsensei suggest --max-risk medium --format markdown --output ./.shellsensei/suggestions.md
python -m shellsensei suggest --format json
```

## 5. Apply Suggestions Safely

Preview first:

```bash
python -m shellsensei apply --shell auto --all --dry-run
```

Interactive review:

```bash
python -m shellsensei apply --shell auto --interactive
```

Apply selected names only:

```bash
python -m shellsensei apply --shell bash --name ss_git --name ss_cargo
```

## 6. Record Feedback and Generate Reports

```bash
python -m shellsensei feedback --name ss_git --normalized "git status" --decision accept
python -m shellsensei report --period weekly --format markdown --output ./.shellsensei/weekly_report.md
python -m shellsensei report --period daily --format json
```

## 7. Run Safety and Team Workflows

Policy checks:

```bash
python -m shellsensei policy --max-risk medium
```

Pack export/import:

```bash
python -m shellsensei pack export --name team-core --output ./team-core.shellsensei.json
python -m shellsensei pack import --input ./team-core.shellsensei.json --dry-run
```

## 8. Productization and Integrations

Version and update:

```bash
python -m shellsensei version
python -m shellsensei self-update
```

Hooks:

```bash
python -m shellsensei hook show --shell bash
python -m shellsensei hook install --shell powershell --dry-run
```

Benchmark:

```bash
python -m shellsensei benchmark --samples 20000 --format json
```

CI lint:

```bash
python -m shellsensei ci-lint --path . --format text
```

IDE tasks (VS Code):

```bash
python -m shellsensei ide vscode --path .
```

## 9. Troubleshooting

- If DB errors occur, run `python -m shellsensei init` again.
- If no suggestions appear, increase history with `ingest` or lower `--min-count`.
- If apply fails, run with `--dry-run` and verify profile path/shell target.
- If CI lint returns non-zero, inspect findings and fix risky shell lines.
