# Changelog

## Unreleased

- Report JSON decoder nesting-limit failures as CLI input errors (exit 2),
  without a traceback or overwriting an existing report. Evaluation rules,
  report fields and the browser's documented input limits are unchanged.

## 0.3.0rc1 — unpublished review candidate

- Prepare PyPI-compatible documentation links, controlled reproducible maintainer archives and an owner-approved Trusted Publishing procedure; reject ambiguous/special archive members, retain executable file modes and resolve generated artifact names without a fixed version. Later maintenance added a guarded, manual TestPyPI workflow; ordinary tests do not publish packages.
- Add eight synthetic declaration-lab scenarios, regression checks for wrong decisions, unlisted actions and missing evidence, and explicit counterexamples documenting the limits of declaration-only evaluation.
- Add deterministic report-order and input-type regressions; cover duplicate evidence IDs and duplicate keys in cases input.
- Add the browser-based Evaluation Lab and link its published demo. No model benchmark or independent adoption is claimed.

- Add a reproducible caller demonstration with retained reports and exact expected exits, and verify the published Action at reviewed commit 1449a91. Include its runner/fixtures in source archives. This is synthetic software evidence, not an adoption claim.

- Escape non-ASCII characters in CLI JSON reports so valid evaluations retain exit 0 or 1 on ASCII and CP1252 stdout. Parsed Unicode values and report fields are unchanged; regression coverage includes critical failures and unexpected prediction IDs at threshold zero.

- Use SPDX MIT metadata and explicit license-file inclusion with setuptools 77.0.3+, without changing license terms or the Python 3.10 minimum.
- Include public test fixtures and documentation in source distributions.
- Verify sdist/wheel contents, unpacked regression tests and isolated console installations across platforms and the minimum build backend.

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

- Add seven external regression tests for exact CLI threshold boundaries ([PR #26](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/26), Aadithya-kl), invalid UTF-8 inputs ([PR #27](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/27), Aadithya-kl), and optional case metadata versus required prediction lists ([PR #28](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/28), jwalith4418-Mj). All three contributions are test-only; 44 tests and six workflows passed on main at `0f4933d`. No evaluator behavior changes or adoption claims.

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
