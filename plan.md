# ShellSensei - Product Plan

## Final Product Vision
ShellSensei is a local-first terminal intelligence product that turns command history into safe, high-leverage automation. The mature product is not just an alias generator; it acts as a workflow mentor that helps individuals and teams work faster, with fewer mistakes, while preserving privacy.

In the final state, users install ShellSensei once and continuously receive practical guidance:
- Repeated patterns become reusable commands, scripts, or task templates.
- Risky command behavior is flagged before damage happens.
- Team members share proven CLI workflows with traceability.
- Terminal productivity improves without surrendering shell history to cloud systems.

## Why This Product Matters
Most engineers spend meaningful time repeating command chains, context switching across repos, and recovering from avoidable CLI mistakes. Existing tooling is fragmented: shell history exists, snippets exist, aliases exist, but there is little intelligence connecting them into adaptive, safe, personalized coaching.

ShellSensei fills that gap by combining:
- Behavioral insight (what users actually do),
- Recommendation quality (what should be automated), and
- Operational safety (what must never be auto-applied blindly).

## Target Users
- Individual developers who live in terminal workflows.
- Platform/SRE engineers with repetitive operational runbooks.
- Engineering teams that want standardized, high-quality command practices.

## Non-Goals (For v1)
- Full remote command execution/orchestration platform.
- Replacing shells or terminal emulators.
- Cloud-first telemetry as a default behavior.

## Product Principles
- Local-first and privacy-preserving by default.
- Suggestions must be explainable, ranked, and reversible.
- Automation must include safety guardrails before convenience.
- Adoption must be zero-friction: install, observe, improve.

## Technical Direction (High Level)
- Ingestion adapters for PowerShell/Bash/Zsh history and optional live capture.
- Normalization engine to remove noise and identify intent-level command patterns.
- Local data store (SQLite in MVP) for sessions, outcomes, and recommendation state.
- Policy/risk subsystem to classify dangerous operations and enforce prompts.
- Optional sharing layer for team workflow packs.

## Phase 0 - Foundation (Week 1)
Goal: establish trusted data capture and normalization.

What this phase solves:
- Without reliable input quality, all downstream intelligence degrades.
- Normalized command representation is required for repeat-pattern detection.

Deliverables:
- Cross-shell ingestion adapters (PowerShell, Bash, Zsh).
- Normalization pipeline (argument masking, path canonicalization, duplicate collapse).
- SQLite schema for sessions, commands, command groups, and execution outcomes.
- Core CLI commands: `init`, `ingest`, `stats`, `doctor`.

Success criteria:
- Ingest 30 days of history in under 2 minutes on a typical developer machine.
- Produce stable command-frequency summaries across shells.

## Phase 1 - Personal Coaching MVP (Weeks 2-3)
Goal: deliver immediate solo-user value from recommendations.

What this phase solves:
- Users need obvious utility within first day, not abstract analytics.

Deliverables:
- Repetition detector for common command chains.
- Recommendation engine for aliases, shell functions, and mini scripts.
- Confidence scoring + rationale text for each recommendation.
- Daily/weekly CLI and Markdown reports.

Success criteria:
- At least 5 accepted recommendations within first week for active user.
- Less than 10% of suggestions marked low-value by user feedback.

## Phase 2 - Safe Automation Layer (Weeks 4-5)
Goal: convert recommendations into safe executable automation.

What this phase solves:
- Advice alone has lower compounding impact than reusable execution artifacts.

Deliverables:
- One-click generation of scripts/functions from validated patterns.
- Risk classifier for destructive flags, permission boundaries, and environment sensitivity.
- Dry-run previews and script diffs before activation.
- Execution wrappers with logging and rollback hints.

Success criteria:
- Generated automations succeed in common scenarios with explicit confirmation flow.
- No high-risk automation executes without additional user confirmation.

## Phase 3 - Team Intelligence (Weeks 6-8)
Goal: enable collaborative CLI standards and sharing.

What this phase solves:
- Team productivity gains require reusable, auditable workflow packs.

Deliverables:
- Pack format (`.shellsensei-pack`) with metadata and versioning.
- Export/import and approval workflow for shared automations.
- Team policy checks (unsafe patterns, naming conventions, shell compatibility).
- Shared recommendation board (git-backed sync in MVP).

Success criteria:
- Two or more users can share packs and activate them reliably.
- Policy checks prevent known unsafe patterns from shared rollout.

## Phase 4 - Productization (Weeks 9-10)
Goal: prepare for public beta and maintainability.

What this phase solves:
- A useful prototype must be installable, observable, and supportable.

Deliverables:
- Installer and update channels for major OSes.
- Shell plugin UX for inline suggestions and accept/reject actions.
- Opt-in quality telemetry (never raw command content by default).
- Documentation, benchmarks, and launch demos.

Success criteria:
- Fresh install to first recommendation in under 3 minutes.
- Public beta with clear docs and reproducible demo scenarios.

## V1 Shipping Status (Completed)
Status snapshot date: March 2, 2026

- Phase 0 - Foundation: `shipped`
  Notes: ingestion, normalization, SQLite storage, and core CLI are complete.
- Phase 1 - Personal Coaching MVP: `shipped`
  Notes: suggestions, confidence/rationale, reports, and measurable feedback criteria are complete.
- Phase 2 - Safe Automation Layer: `shipped`
  Notes: risk classifier, dry-run/apply safety, wrapper generation, and rollback hints are complete.
- Phase 3 - Team Intelligence: `shipped`
  Notes: pack export/import, policy checks, and shared board workflow are complete.
- Phase 4 - Productization: `shipped`
  Notes: installer scripts, update command path, telemetry opt-in, benchmarking, docs, and beta demo flow are complete.

## V2 Plan (Next Roadmap)
V2 focus: improve intelligence quality, collaboration depth, and integration maturity while staying local-first.

### V2 Phase 1 - Contextual Intelligence
Goal: make suggestions context-aware by repository and workflow intent.

Deliverables:
- Repo-aware ranking model (Rust/Python/Frappe/Kafka tuned scoring).
- Context memory per project (local-only profiles).
- Suggestion quality scoring pipeline with threshold tuning.

Exit criteria:
- Measurable increase in accepted suggestions vs V1 baseline.
- Reduced generic/noisy suggestions in mixed-codebase environments.

### V2 Phase 2 - Local Intent Engine
Goal: move from keyword heuristics to stronger local intent understanding with strict redaction.

Deliverables:
- Local intent parser abstraction (heuristic + pluggable local model backend).
- Redaction policy profiles (strict/default/custom).
- Intent-to-action planner for suggest/apply/report/policy flows.

Exit criteria:
- Intent classification accuracy target met on internal eval set.
- No raw sensitive tokens stored in logs or telemetry payloads.

### V2 Phase 3 - Team Collaboration Depth
Goal: make shared workflows auditable and reviewable for teams.

Deliverables:
- Approval workflow for incoming packs/board posts.
- Change history and review metadata for shared automations.
- Git-native sync helpers (status, conflict guidance, batch publish).

Exit criteria:
- Two-team scenario can share, review, and adopt workflow packs with audit trail.
- Conflicts are detected and resolved with clear operator guidance.

### V2 Phase 4 - Integration Maturity
Goal: deepen CI and IDE workflows so ShellSensei becomes part of daily engineering loops.

Deliverables:
- CI lint profiles (baseline, strict, custom policy packs).
- IDE integrations expanded beyond VS Code tasks (command palette snippets and diagnostics bridge).
- Hook behavior upgrade from helper command to practical inline recommendation loop.

Exit criteria:
- CI policy checks are reliable in real pipelines.
- IDE-assisted workflow adoption validated on at least one team project.

### V2 Phase 5 - Reliability and Release
Goal: harden performance, quality, and operational readiness for broader adoption.

Deliverables:
- Regression test suites for suggestion quality and risk gating.
- Performance budgets for ingest/suggest/report paths.
- Release quality gates and migration notes for upgrading from V1.

Exit criteria:
- Stable release candidate with documented upgrade path.
- Quality gates pass across supported shells and OS targets.

## V2 Shipping Status (Completed)
Status snapshot date: March 2, 2026

- V2 Phase 1 - Contextual Intelligence: `shipped`
  Notes: contextual ranking by repo type + project context memory and thresholds are implemented.
- V2 Phase 2 - Local Intent Engine: `shipped`
  Notes: local intent parser abstraction, strict/default/custom redaction profiles, and profile management are implemented.
- V2 Phase 3 - Team Collaboration Depth: `shipped`
  Notes: board post/list + approve/reject review workflow and git-backed sync are implemented.
- V2 Phase 4 - Integration Maturity: `shipped`
  Notes: CI lint profiles, expanded integration commands, and practical hook helpers are implemented.
- V2 Phase 5 - Reliability and Release: `shipped`
  Notes: quality gate command (tests + benchmark budget), regression tests, and migration-ready release posture are implemented.

## Risks and Mitigations
- Risk: Noisy recommendations reduce trust.
  Mitigation: confidence thresholds, explicit rationale, user feedback loop.
- Risk: Safety regressions in auto-generated scripts.
  Mitigation: mandatory dry-run and policy-gated execution.
- Risk: Shell compatibility fragmentation.
  Mitigation: adapter boundaries and compatibility test matrix.

## Stretch Vision (v2+)
- Repo-aware coaching tuned for Rust, Python, Frappe, Kafka workflows.
- Local intent parsing with strict redaction and pluggable local model backends.
- CI linting and policy packs for shell scripts and runbooks.
- IDE and terminal integrations with contextual recommendation loops.

## Stretch Vision Status (Completed)
Status snapshot date: March 2, 2026

- Repo-aware coaching tuned for Rust/Python/Frappe/Kafka: `shipped`
  Notes: repo detection + contextual ranking and coach hints are implemented.
- Local intent parsing with strict redaction + pluggable local backend: `shipped`
  Notes: strict/default/custom redaction profiles and backend selector are implemented.
- CI linting and policy packs for scripts/runbooks: `shipped`
  Notes: baseline/strict/custom CI profile support and policy-driven filtering are implemented.
- IDE + terminal contextual recommendation loops: `shipped`
  Notes: shell hook auto mode, VS Code tasks/snippets, and diagnostics bridge export are implemented.

## Success Metrics
- Weekly active users.
- Recommendation acceptance rate.
- Estimated time saved per user/week.
- Safety incident rate (target: near zero).
- 30-day retention.
