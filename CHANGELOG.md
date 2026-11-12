# Changelog

## v0.2.0

- Add local Python packaging and the `nexus-evaluate` command-line entry point.
- Reject duplicate JSON object keys and invalid prediction IDs.
- Add CLI regression tests for acceptance thresholds, critical failures, malformed input, and report output.
- Check the installed command in CI.

## v0.1.0 — initial public prototype

- Evaluate structured decisions, declared actions, and evidence identifiers against explicit JSON cases.
- Reject critical-case failures and unexpected prediction IDs.
- Provide JSON reporting, a configurable minimum pass rate, synthetic examples, and unit tests.
- Add automated test workflow and contribution documentation.

This project does not claim production readiness, adoption, or real-world agent safety.
