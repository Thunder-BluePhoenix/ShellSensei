# ShellSensei Release Checklist

Target release: `v3.0.0`  
Date: March 3, 2026

## 1. Scope Freeze
- [ ] Confirm release scope (no new feature merges after freeze).
- [ ] Update version in:
  - [ ] `src/shellsensei/__init__.py`
  - [ ] `pyproject.toml`
- [ ] Ensure `plan.md` shipping sections reflect actual state.

## 2. Quality Gates
- [ ] Run tests:
  - [ ] `python -m pytest -q`
- [ ] Run performance gate:
  - [ ] `python -m shellsensei quality-gate --format text`
- [ ] Run operational checks:
  - [ ] `python -m shellsensei health --format text`
  - [ ] `python -m shellsensei soak --iterations 20 --format text`
  - [ ] `python -m shellsensei upgrade-check --project-root . --format text`

## 3. Functional Smoke Tests
- [ ] Init and ingest:
  - [ ] `python -m shellsensei init`
  - [ ] `python -m shellsensei ingest --shell auto --limit 300`
- [ ] Suggest and apply:
  - [ ] `python -m shellsensei suggest --project-root . --format markdown --output ./.shellsensei/suggestions.md`
  - [ ] `python -m shellsensei apply --shell auto --interactive --dry-run`
- [ ] Reporting and metrics:
  - [ ] `python -m shellsensei report --period weekly --format markdown --output ./.shellsensei/weekly_report.md`
  - [ ] `python -m shellsensei metrics --format json`
  - [ ] `python -m shellsensei phase-status --format text`
- [ ] Policy and governance:
  - [ ] `python -m shellsensei policy-simulate --project-root . --format text`
  - [ ] `python -m shellsensei board list --root . --format text`
- [ ] V2/V3 integrations:
  - [ ] `python -m shellsensei llm-parse --project-root . --profile default --backend heuristic --text "suggest build alias"`
  - [ ] `python -m shellsensei ci-lint --path . --profile strict --format text`
  - [ ] `python -m shellsensei ide vscode --path .`
  - [ ] `python -m shellsensei ide snippets --path .`
  - [ ] `python -m shellsensei ide diagnostics --path . --output ./.shellsensei/diagnostics.json`

## 4. Docs and Migration
- [ ] Validate docs consistency:
  - [ ] `README.md`
  - [ ] `plan.md`
  - [ ] `docs/how_to_use_shellsensei.md`
  - [ ] `docs/MIGRATION_V1_TO_V2.md`
  - [ ] `purpose.md`
- [ ] Add release notes (`CHANGELOG.md` or release description).
- [ ] Include migration/rollback notes in release body.

## 5. Packaging and Installers
- [ ] Validate editable install:
  - [ ] `pip install -e .`
- [ ] Validate script installers:
  - [ ] `scripts/install.sh`
  - [ ] `scripts/install.ps1`
- [ ] Validate self-update path:
  - [ ] `python -m shellsensei self-update --package shellsensei`

## 6. Security and Privacy
- [ ] Confirm telemetry defaults to disabled.
- [ ] Confirm no raw secrets appear in logs/reports for redacted flows.
- [ ] Run a quick redaction test:
  - [ ] `python -m shellsensei llm-parse --project-root . --profile strict --text "token sk-abcdef1234567890"`

## 7. Git and Release
- [ ] Final review of diff.
- [ ] Create release commit.
- [ ] Create and push tag:
  - [ ] `git tag v3.0.0`
  - [ ] `git push origin v3.0.0`
- [ ] Publish release notes and artifacts.

## 8. Post-Release Monitoring (First 7 Days)
- [ ] Daily check:
  - [ ] `python -m shellsensei phase-status --format text`
  - [ ] `python -m shellsensei evaluate --project-root . --window-days 7 --format text`
- [ ] Track top user issues and convert into V4 tasks.
- [ ] Validate no regressions in quality-gate benchmark floor.
