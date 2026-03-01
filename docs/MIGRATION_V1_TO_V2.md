# ShellSensei Migration: V1 -> V2

## Overview
V2 introduces contextual ranking, intent profiles, collaboration review workflow, and release quality gates.

## Breaking/Behavioral Changes
- `suggest`, `apply`, and `automate` now support contextual ranking controls:
  - `--project-root`
  - `--threshold`
- `board` now supports review actions:
  - `approve`
  - `reject`
- `llm-parse` now uses intent engine options:
  - `--project-root`
  - `--profile`
  - `--backend`

## New Commands
- `intent-profile`
- `quality-gate`

## Recommended Upgrade Steps
1. Pull latest code and run tests:
   - `python -m pytest -q`
2. Initialize/refresh local DB:
   - `python -m shellsensei init`
3. Validate baseline metrics:
   - `python -m shellsensei metrics --format json`
4. Validate V2 status:
   - `python -m shellsensei phase-status --format text`
5. Run quality gate:
   - `python -m shellsensei quality-gate --format text`

## Rollback
- Revert to previous commit/tag.
- Restore previous shell profile backup if `apply` changed profile blocks.
- Remove generated wrappers under `.shellsensei/wrappers*` if needed.
