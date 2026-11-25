# Public roadmap and contribution opportunities

NEXUS Agent Evaluation is a small educational Python evaluator for **structured agent declarations**. The roadmap is intentionally scoped to work that can be independently tested. Nothing here is a claim of production readiness or planned delivery dates.

## Now: reliability and new contributor experience

| Priority | Opportunity | How to verify it | Difficulty |
| --- | --- | --- | --- |
| High | Independent [five-minute trial and feedback](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8) | Reproducible commands, observed outcomes and genuine criticism | No code required |
| Completed | Regression coverage for report ordering and duplicate evidence IDs | [PR #21](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/21) and [PR #20](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/20) | Regression coverage |
| Medium | Clearer diagnostic messages for malformed nested predictions | Tests for each changed diagnostic; behavior unchanged | Intermediate |

The [declaration lab and candidate checklist](DECLARATION_LAB.md) document additional synthetic cases and known limits.

[Issue #9](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/9) tracks a regression test for the existing CLI exit status of 2 when the case file contains duplicate JSON object keys. [PR #16](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/16) contains the contributor’s test and its review and CI status.

## Next: integration quality

The CLI already has three-platform CI. The [maintenance review](MAINTENANCE_REVIEW.md) records the Action coverage changes, release plan and scoped follow-up tasks; check existing workflows and issues before proposing overlapping work.

- **Consumer trial.** The [pinned caller workflow](CONSUMER_TRIAL.md) demonstrates the action using synthetic files. Independent trials can help identify friction in other callers’ setups.
- **Result schema:** define a versioned machine-readable report contract *only if there is a genuine downstream consumer need*. Avoid breaking existing JSON keys without explicit migration.
- **Validation clarity:** document how strict case validation differs from failed prediction cases; introduce stricter input rejection only with tests and compatibility analysis.
- **Developer documentation:** independently review the quickstart on Windows, Linux and macOS.

## Later: meaningful evaluation (research, not promised features)

- Small held-out synthetic suites that stress expected decision matching and action-bound declarations.
- Comparison of deterministic declared-output gates against larger LLM evaluation toolkits, explicitly separating different goals and **without marketing accuracy claims**.
- Evaluate the limits of a declaration-only approach and record real counterexamples where it produces misleading confidence.

## How to get involved

1. Read [CONTRIBUTING.md](../CONTRIBUTING.md).
2. Choose an issue or submit your [independent feedback](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/new?template=trial_feedback.yml).
3. Reproduce it using public, synthetic data. Explain your observation and platform.
4. For code changes, open a focused PR with regression tests and documented limitations.

Useful contributions include saying **this did not help my workflow** and documenting why. No stars, endorsements, private data or contribution counts are requested. The public NEXUS evaluator is separate from any unpublished private project.
