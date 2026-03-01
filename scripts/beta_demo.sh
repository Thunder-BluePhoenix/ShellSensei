#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="src"

python -m shellsensei init
python -m shellsensei ingest --shell auto --limit 300
python -m shellsensei suggest --max-risk medium --format markdown --output ./.shellsensei/suggestions.md
python -m shellsensei apply --shell auto --interactive --dry-run
python -m shellsensei report --period weekly --format markdown --output ./.shellsensei/weekly_report.md

echo "Beta demo complete. See ./.shellsensei/ for generated outputs."
