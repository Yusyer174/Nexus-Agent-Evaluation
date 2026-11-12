# Contributing

Thanks for considering a contribution. This project is an early, standalone evaluation tool, not a runtime security sandbox.

## Development

Use Python 3.10 or newer. Clone the repository, make changes on a separate branch, and run:

```sh
python -m unittest discover -s tests -v
python evaluator.py examples/cases.json examples/predictions.json
```

No external packages or API keys are required. Add regression tests for behavior changes. Keep examples synthetic and distinguish example results from real model evaluations.

## Reporting issues

Describe the expected and actual behavior, the Python version, and a minimal reproducible example. Never include secrets, private data, or proprietary agent outputs. For security-sensitive reports, do not publish exploit details or credentials in public issues; contact the maintainer privately if a suitable channel is available.

## Pull requests

Explain the problem and the proposed change, link any relevant issue, and report the tests you ran. Preserve deterministic evaluation and fail-closed handling of critical cases. Keep changes focused; documentation corrections are welcome.
