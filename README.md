# NEXUS Agent Evaluation

[![Python tests](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/workflows/tests.yml/badge.svg)](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/workflows/tests.yml)
[![GitHub Action smoke test](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/workflows/action-smoke.yml/badge.svg)](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/workflows/action-smoke.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Test structured AI-agent decisions with deterministic, dependency-free Python.** NEXUS Agent Evaluation compares *reported* decisions, actions and evidence IDs against explicit test cases. It is useful as an offline regression check in development and CI.

No model, API key, service or runtime dependencies are required. Python **3.10+**.

**In one minute:** [Try a passing and deliberately failing case](docs/TRY_IT.md) · [Use the GitHub Action](#github-actions-integration) · [Give independent feedback](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8) · [Contribute](CONTRIBUTING.md)

> **Scope:** Early, standalone educational prototype. This does **not** execute agents, enforce permissions, authenticate evidence, or establish real-world safety. It is not a verified integration with the separate private NEXUS research project. No external adoption is claimed.

## See the result

Clone the repository and run the included synthetic cases:

```bash
git clone https://github.com/Yusyer174/Nexus-Agent-Evaluation.git
cd Nexus-Agent-Evaluation
python evaluator.py examples/cases.json examples/predictions.json --output report.json
```

The command exits **0** and generates a JSON report containing these fields:

```json
{
  "total": 3,
  "passed": 3,
  "pass_rate": 1.0,
  "critical_failures": [],
  "unexpected_predictions": [],
  "gate_passed": true,
  "minimum_pass_rate": 1.0,
  "accepted": true
}
```

*Excerpt only: the full report also contains per-case results.*

Now test a synthetic **critical failure**:

```bash
python evaluator.py examples/cases.json examples/rejected-predictions.json
```

This intentionally exits **1**, reports `gate_passed: false`, and identifies `permissions-01` as a critical failure. That case declares an action outside the permitted set. It changes no real permissions and runs no real agent.

| Situation | Result |
| --- | --- |
| All declared decisions and actions match | Accepted; exit **0** |
| A noncritical case fails and the minimum pass rate is not met | Rejected; exit **1** |
| Critical case fails, regardless of pass-rate setting | Rejected; exit **1** |
| Unexpected prediction ID | Rejected; exit **1** |
| Malformed input, duplicate JSON keys or invalid arguments | Error; exit **2** |

## What the evaluator actually checks

Each JSON case declares an expected decision, a set of allowed actions, optional evidence identifiers, and whether the case is critical. Predictions are keyed by case ID. The evaluator checks:

- **Decision match**: exactly the expected decision.
- **Declared action bounds**: every listed action belongs to the case's allowed set.
- **Declared evidence IDs**: every required ID is listed; authenticity is **not** verified.
- **Acceptance gate**: a critical failure or unexpected case ID blocks acceptance even if the overall pass rate is sufficient.

The complete JSON contract, example objects, validation details and exit codes are documented in [docs/INTEGRATION.md](docs/INTEGRATION.md).

## GitHub Actions integration

A [composite GitHub Action](action.yml) allows an existing project to evaluate its exported JSON files as a CI step. It consumes files in the caller workspace and produces a JSON report. It does **not** run the agent itself.

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0
  with:
    python-version: '3.11'
- uses: Yusyer174/Nexus-Agent-Evaluation@754dcf51ff4fb5b15a648d4f633b55ee5fe0a3f7
  with:
    cases: tests/agent/cases.json
    predictions: tests/agent/predictions.json
    report-path: agent-evaluation-report.json
```

Replace the example paths with your own files. The action reference above is a tested historical commit; review changes before pinning a newer commit. See the [full workflow example](examples/github-actions/evaluate-agent.yml) and the [local action smoke test](.github/workflows/action-smoke.yml).

The setup-python action uses Node 24. Self-hosted runners running this example require Actions Runner 2.327.1 or newer; the repository CI uses GitHub-hosted runners.

Alternatively, install a local checkout as a CLI package:

```bash
python -m pip install .
nexus-evaluate examples/cases.json examples/predictions.json
```

Run these example paths from the source directory. Source archives include the synthetic fixtures, tests and public documentation; wheels install the evaluator and CLI. For other working directories, supply paths to your own JSON files. The installed interpreter can also run the same CLI with `python -m evaluator`. See [packaging checks](CONTRIBUTING.md#packaging-checks) for reproducible artifact and installation validation.

The project is **not published on PyPI**. The package metadata currently identifies version `0.2.0`; see [CHANGELOG.md](CHANGELOG.md) for subsequent changes on `main`.

See the [maintenance review](docs/MAINTENANCE_REVIEW.md) for the compatibility and release plan, prioritized follow-ups and evidence-based contribution opportunities.

## When *not* to use it

This is not a substitute for execution traces, sandbox enforcement, permission checks, review independence, statistical model evaluation, or the validation of evidence integrity. An agent can report an allowed action without actually behaving correctly.

Use independently designed development and held-out cases for meaningful evaluation; do not give hidden expected answers to the agent under test. See [SECURITY.md](SECURITY.md).

## Contribute or test it

The most valuable feedback is **independent and reproducible**, including negative results.

- [Five-minute trial](docs/TRY_IT.md) · [Submit genuine feedback](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/new?template=trial_feedback.yml)
- [Open, beginner-friendly test issue](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/9) · [Public roadmap](docs/ROADMAP.md)
- [Contributor guide](CONTRIBUTING.md) · [Bug reports and other issues](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues)

Please use only synthetic or non-sensitive examples and never publish credentials or private agent data. Stars, forks and issue replies are not evidence of genuine usage without supporting details.

## Repository layout

```text
evaluator.py                    # CLI and deterministic evaluation
action.yml                      # Optional CI integration
examples/                       # Passing and failing synthetic JSON
tests/                          # Python regression tests
docs/INTEGRATION.md             # Input/output contract
docs/TRY_IT.md                  # Independent five-minute trial
docs/ROADMAP.md                 # Prioritized opportunities
.github/workflows/              # Python and composite-action CI
```

MIT-licensed source code: [LICENSE](LICENSE).
