# NEXUS Agent Evaluation

[![Tests](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/workflows/tests.yml/badge.svg)](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/workflows/tests.yml)


A small, dependency-free Python tool for evaluating structured AI-agent decisions against explicit test cases. Inspired by the NEXUS project's emphasis on auditable decisions, permission boundaries, and independent validation.

**Status:** Early standalone prototype (v0.2.0). This is a new implementation, not an extraction from or verified integration with the private NEXUS codebase. No claims of adoption or production readiness are made.

## Try it and give independent feedback

**Five-minute, no-API-key trial:** [run a passing and deliberately failing agent-evaluation example](docs/TRY_IT.md). Feedback from developers who actually try the prototype is welcome, including confusing errors, integration gaps, or reasons it would *not* be useful.

- [Start the trial](docs/TRY_IT.md)
- [Submit test feedback](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/new?template=trial_feedback.yml)
- [Browse the JSON integration contract](docs/INTEGRATION.md)

The project has no claimed external users or validated deployments.


## Quick start

Requirements: Python 3.10 or newer. No API keys, network access, or third-party packages required.

```bash
python evaluator.py examples/cases.json examples/predictions.json
python -m unittest discover -s tests -v
```

### Install locally

From a clone of this repository, run:

```bash
python -m pip install .
nexus-evaluate examples/cases.json examples/predictions.json
```

This installs the local package; it is not published to PyPI. There are no runtime dependencies (installation may download build tools).

See [Integration contract](docs/INTEGRATION.md) for the exact JSON schema, failure gates, exit codes and example integrations.

### GitHub Actions integration (experimental)

A [composite GitHub Action](action.yml) is included for teams that already export structured agent predictions. It checks files from the caller's workspace and fails CI if the declared outputs fail the configured gates. It does **not** run the agent or enforce actual permissions.

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
- uses: Yusyer174/Nexus-Agent-Evaluation@754dcf51ff4fb5b15a648d4f633b55ee5fe0a3f7
  with:
    cases: tests/agent/cases.json
    predictions: tests/agent/predictions.json
    report-path: agent-evaluation-report.json
```

Replace the example paths with your own files. This example is pinned to a CI-tested commit; update that SHA **only after reviewing the changes**. The [complete example workflow](examples/github-actions/evaluate-agent.yml) also uploads the report.


On Windows use `py` instead of `python` if needed.

The example contains synthetic cases; all three example predictions are deliberately correct. This does not measure the performance of a real model.

## Project layout

- `pyproject.toml`: package metadata and CLI entry point.
- `evaluator.py`: evaluation logic and command-line interface.
- `examples/`: synthetic cases and example predictions.
- `tests/`: automated regression tests.
- `CONTRIBUTING.md`: how to propose changes and test them.

## Evaluate your own agent

1. Create a JSON array of cases with unique `id`, `expected_decision`, `allowed_actions`, `required_evidence` (optional), and `critical` (optional boolean).
2. Save your agent outputs as a JSON object keyed by case ID. Each output contains `decision`, `actions` (list), and `evidence` (list).
3. Run:

```bash
python evaluator.py my-cases.json my-predictions.json --output report.json --min-pass-rate 0.9
```

A case passes when the decision matches exactly, all declared actions are allowed, and all required evidence identifiers are present. Missing or malformed outputs fail their case. Duplicate JSON keys are rejected as invalid input. Critical-case failures and unexpected case IDs always block acceptance, regardless of the pass rate. By default, acceptance also requires every case to pass. The report separates the critical gate from the overall acceptance result. Exit codes: 0 accepted, 1 rejected, 2 invalid input or file error. The tool refuses to overwrite either input file with `--output`.

## Design boundaries

- This tool checks structured declarations, not actual execution or permissions. It is not a security sandbox or runtime authorization layer.
- Evidence IDs are checked for presence only, not authenticity or relevance.
- Allowed actions are a maximum permission set, not a requirement to perform an action.
- Use independently designed development and held-out cases for meaningful evaluation. Do not expose private held-out expectations to the agent being evaluated.
- The sample fixtures are synthetic and should not be used to claim real-world accuracy or safety.

## Contributing

Bug reports, additional synthetic scenarios, and reproducible test improvements are welcome. Please use the issue template, read [CONTRIBUTING.md](CONTRIBUTING.md), and consult [SECURITY.md](SECURITY.md) before disclosing sensitive details.

## License

[MIT](LICENSE).
