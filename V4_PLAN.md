# ShellSensei V4 Plan

Date: March 3, 2026  
Baseline: V3 shipped (V1+V2+Stretch+V3 complete)

## V4 Vision
Make ShellSensei feel less like a powerful toolkit and more like a reliable daily assistant for teams: lower noise, clearer governance, better defaults, and smoother integration into existing engineering workflows.

## Likely User Feedback Driving V4
- Suggestions are useful, but ranking still needs tighter project-specific precision.
- Policy and governance are powerful, but configuration is hard for new teams.
- Board workflows exist, but discoverability and conflict resolution need improvement.
- CI and IDE integrations work, but need cleaner “drop-in” enterprise presets.
- Operators want simpler health dashboards and fewer commands for common workflows.

## V4 Phase 1 - Recommendation Precision
Goal: significantly reduce low-value suggestions and improve first-run relevance.

Deliverables:
- Hybrid ranking model combining:
  - acceptance history,
  - repo context,
  - command sequence patterns (not single-command only).
- “Cold start” profile templates by role:
  - backend-dev, platform, SRE, data-engineering.
- Suggestion deduplication and fatigue controls:
  - suppress near-identical repeats,
  - cooldown windows for rejected suggestions.

Exit criteria:
- Low-value rate remains below 8% for active users.
- First 20 suggestions show measurable acceptance improvement vs V3.

## V4 Phase 2 - Policy UX and Safety Hardening
Goal: make policy-as-code easy to adopt and safer by default.

Deliverables:
- `shellsensei policy init` scaffold with commented templates.
- Policy linter and validator command:
  - schema checks,
  - conflict checks (global vs repo overrides),
  - risk-policy simulation preview.
- Action guardrails:
  - block high-risk apply unless explicit `--allow-high-risk` with reason.
- Policy decision trace in reports.

Exit criteria:
- New teams can initialize and validate policy in <10 minutes.
- No ambiguous policy precedence cases in validation tests.

## V4 Phase 3 - Collaboration Workflow 2.0
Goal: make board/pack governance practical for multi-team environments.

Deliverables:
- Board filtering and queue views:
  - pending approvals,
  - active automations,
  - retire candidates.
- Conflict diagnostics:
  - same command name collisions,
  - contradictory policies between packs.
- Mandatory approval rules:
  - minimum reviewer count by risk level.
- Board export/import snapshots for audit handoff.

Exit criteria:
- Multi-team board workflow runs without manual spreadsheets/chat tracking.
- High-risk posts cannot be activated without required approvals.

## V4 Phase 4 - Integration Presets and Enterprise Fit
Goal: reduce setup friction in CI/IDE and improve portability.

Deliverables:
- CI preset packs:
  - GitHub Actions,
  - GitLab CI,
  - generic runner output.
- IDE preset packs:
  - VS Code starter bundle (tasks + snippets + diagnostics config).
- Team onboarding command:
  - `shellsensei bootstrap --profile <team-profile>`.
- Optional local API profile with explicit security modes.

Exit criteria:
- Teams can onboard with a single command and default preset.
- CI/IDE setup reduced to under 5 minutes in common environments.

## V4 Phase 5 - Operability and Product Experience
Goal: simplify day-2 operations and improve observability.

Deliverables:
- Unified `status` command:
  - health,
  - phase status,
  - quality gate summary,
  - policy state.
- Event timeline command for operator debugging.
- “One-shot report” command that bundles:
  - metrics,
  - evaluate,
  - policy simulation,
  - board state.
- Better error taxonomy and actionable remediation hints.

Exit criteria:
- Most troubleshooting can be done from `status` + one-shot report.
- Mean time to identify configuration issues drops significantly.

## V4 Non-Goals
- Cloud-hosted multi-tenant control plane.
- Replacing shell/terminal ecosystems.
- Full LLM dependency for core functionality.

## V4 Success Metrics
- Suggestion acceptance rate vs V3 baseline.
- Low-value suggestion rate trend.
- Time to policy onboarding for new teams.
- Board approval cycle time (pending -> active).
- CI/IDE integration setup time.
- Operator issue resolution time.

## First 2-Week Execution Slice (Recommended)
1. Implement `policy init` + policy validator.
2. Add dedup/cooldown logic in suggestion pipeline.
3. Add board queue views and approval-rule enforcement by risk.
4. Add `status` command MVP with health + phase + quality summary.
5. Run pilot with one real project and capture pain points for sprint 2.
