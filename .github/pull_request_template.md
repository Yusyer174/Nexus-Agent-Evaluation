## What problem does this solve?

<!-- Link an issue or describe a reproducible problem. -->

## Changes

<!-- Explain the smallest relevant behavior or documentation change. -->

## Validation

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python evaluator.py examples/cases.json examples/predictions.json`
- [ ] Added or updated regression tests if behavior changed
- [ ] Used synthetic, non-sensitive test data
- [ ] Reviewed the documentation and scope limitations

Tested SHA and environment:

Failing-before / passing-after evidence, or reason no behavior test is needed:

Checks blocked or not run (with reason):

## Coordination and independent review

Issue claim and related PRs checked:

Human / AI-assisted authorship and retained external credits:

Independent reviewer and commands they personally reproduced (or awaiting review):

<!-- CI and author self-checks do not count as independent review. Do not claim
reserved contributor tasks or merge/publish without maintainer authorization.
See docs/DEVELOPMENT_TEAM.md for handoff and conflict handling. -->

## Safety and scope

Does this modify acceptance gates, data parsing, or critical-case handling? If so, describe exactly how and provide tests. This tool checks declared outputs only; do not claim to have validated actual runtime permissions or independent safety.
