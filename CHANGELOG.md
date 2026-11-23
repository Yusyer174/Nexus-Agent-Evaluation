# Changelog

## Unreleased

- Prevent report output from overwriting either input through a hard link, with regression tests.
- Pass composite-action paths as literal CLI arguments, including filenames starting with `-`.
- Exercise the actual action on Linux, Windows and macOS with caller paths containing spaces and shell characters.
- Add persistent Copilot guidance and a scoped maintenance review with release and contributor follow-ups.

- Add a standalone GitHub composite action, a smoke-test workflow, and a copyable downstream CI example.
- Provide an independent five-minute trial with accepted and rejected synthetic predictions.
- Provide a structured, privacy-conscious trial feedback issue template.

- Protect the evaluator's input files from accidental overwrite through `--output`.
- Expand regression coverage for output aliases, malformed cases and acceptance-gate edge cases.
- Document the JSON integration contract, security disclosure and contributor workflow.
- Add a structured bug report form and pull request checklist.

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
