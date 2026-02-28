# ShellSensei - Product Philosophy

## Purpose
ShellSensei exists to make terminal work more intentional, safer, and more compounding. It should help users spend less energy repeating command mechanics and more energy solving real engineering problems.

## Core Beliefs
- Terminal behavior is a rich source of practical knowledge.
- Small workflow improvements compound dramatically over time.
- Trust is earned through correctness, safety, and transparency.
- Privacy is a product feature, not a compliance checkbox.

## Design Philosophy
- Local-first by default: user command history is sensitive and should remain local unless explicitly shared.
- Explain before suggesting: every recommendation should include rationale and confidence.
- Human-in-control automation: no irreversible actions without clear confirmation.
- Progressive capability: start with insights, then recommendations, then guarded automation.

## Safety Philosophy
- Assume commands can be destructive.
- Favor false negatives over dangerous false positives in automation.
- Require dry-run and preview for generated scripts.
- Keep audit logs of generated actions and user decisions.

## UX Philosophy
- Advice must be specific, not generic.
- Friction should be low for safe actions and high for risky ones.
- The product should feel like a mentor, not a nagging linter.
- Recommendations must adapt to user context and feedback.

## Team/Product Philosophy
- Shared workflows should be versioned, reviewable, and attributable.
- Standards should support autonomy, not enforce rigidity.
- The product should raise collective engineering quality over time.

## Anti-Patterns to Avoid
- Opaque AI suggestions with no explanation.
- Cloud-dependent design for basic features.
- Aggressive auto-fix behavior without user consent.
- Vanity metrics that do not reflect real productivity gains.

## Decision Filter
For each new feature ask:
1. Does it save meaningful terminal time?
2. Does it improve safety or maintainability?
3. Is it explainable to a skeptical engineer?
4. Can it work local-first?
5. Can users easily undo it?

If the answer is no to most of the above, the feature should be reworked or postponed.
