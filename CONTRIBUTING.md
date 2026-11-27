# Contributing

Thanks for considering a contribution. This project is an early, standalone evaluation tool, not a runtime security sandbox.

## Development

Start with the [team coordination and review protocol](docs/DEVELOPMENT_TEAM.md),
[architecture map](docs/ARCHITECTURE.md) and [assistant agreement](AGENTS.md).
Check issue comments and open PRs before starting; leave a short outline to avoid
duplicating a contributor's work. The roadmap links the current small tasks.

Use Python 3.10 or newer. Clone the repository, make changes on a separate branch, and run:

```sh
python -m unittest discover -s tests -v
python evaluator.py examples/cases.json examples/predictions.json
python evaluator.py examples/cases.json examples/rejected-predictions.json --min-pass-rate 0
```

The commands should respectively pass, exit 0 and exit 1. The last command must
report a failed critical gate even at threshold zero. No external packages or API
keys are required for these checks. Add regression tests for behavior changes.
Keep examples synthetic and distinguish example results from real model evaluations.

For JavaScript or lab source changes, install Node.js 24 as a development tool and run:

```sh
python docs/lab/build.py --check
python docs/lab/test_parity.py
```

If source generation changed, first run `python docs/lab/build.py` and review the
generated diff. UI changes also need the optional browser test documented in
[the lab guide](docs/lab/README.md). Browser CI wiring remains contributor issue #29.

## Packaging checks

For packaging changes, install the build frontend in your development environment and build both artifacts:

```sh
python -m pip install build
python -m build
python tests/check_distribution.py --sdist dist/nexus_agent_evaluation-0.3.0rc1.tar.gz --wheel dist/nexus_agent_evaluation-0.3.0rc1-py3-none-any.whl
```

Use the actual filenames if the version changes. The build frontend and setuptools 77.0.3+ are build tools; the evaluator still has no runtime dependencies. Building may download tooling. The artifact checker runs the unpacked source tests, checks metadata/license/fixtures, creates temporary virtual environments, installs both artifacts and runs the installed console command from a separate caller directory. Installing the source artifact may download its build backend. It never publishes anything.

The distribution workflow tests Python 3.10 with the minimum backend and Python 3.13 on Linux, Windows and macOS. The regular unit workflow continues testing Python 3.10–3.13. Keep the MIT license text, runtime requirement and critical gates unchanged when maintaining packaging.

For two controlled builds with fixed tooling, archive normalization, SHA-256 comparison and future Trusted Publishing requirements, follow [distribution preparation](docs/DISTRIBUTION.md). This process builds from a committed Git snapshot and never uploads packages.

## Reporting issues

Describe the expected and actual behavior, the Python version, and a minimal reproducible example. Never include secrets, private data, or proprietary agent outputs. For security-sensitive reports, do not publish exploit details or credentials in public issues; contact the maintainer privately if a suitable channel is available.

## Pull requests

Explain the problem and the proposed change, link any relevant issue, and report the tests you ran. Preserve deterministic evaluation and fail-closed handling of critical cases. Keep changes focused; documentation corrections are welcome.

## Integration and security

See [docs/INTEGRATION.md](docs/INTEGRATION.md) for the public schema, gates and limitations. Run the CLI and its tests locally before submitting a PR. Security-sensitive findings should follow [SECURITY.md](SECURITY.md); public issues must contain no secrets or sensitive exploit details.
