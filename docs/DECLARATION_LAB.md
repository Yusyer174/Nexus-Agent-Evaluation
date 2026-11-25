# Declaration lab and release candidate

This is a review candidate for **0.3.0rc1**, not a published release. It is an educational, declaration-only evaluator; no agent execution, evidence authentication or runtime enforcement is provided.

## Reproduce

Use Python 3.10+ in a checkout of this candidate branch:

```sh
python -m unittest discover -s tests -v
python -m unittest discover -s tests -p test_declaration_lab.py -v
python evaluator.py examples/cases.json examples/predictions.json
python evaluator.py examples/cases.json examples/rejected-predictions.json
```

The first CLI example should exit 0; the second should exit 1. The lab is a fixed public synthetic library-record workflow, not a held-out model benchmark. Eight scenarios cover valid, missing, stale, conflicting, invalid and unverified records and missing/revoked review approval. The six test methods contain 22 subtests varying one declaration at a time. Expectations are explicit fixtures, not inferred by the evaluator. Two counterexamples show that identical declarations cannot establish source truth and allowed action sets are not required action sets. No real permissions, tools or external effects are involved.

Local validation of the new module: Python 3.13.5, six unittest methods passed; pytest reported six passed and 22 subtests passed. The evaluator blob matched main at b735b467e59302cf6f2c67b42ebf51e5c2f59d0e. Full candidate CI and artifact builds are separate checks.

## Candidate review checklist

- Verify all six workflows on the exact candidate head, including distribution checks and Python 3.10–3.13.
- Confirm source and wheel metadata agree on 0.3.0rc1, include the MIT license, and install in clean environments.
- Confirm the evaluator and action semantics are unchanged.
- Review the version and change notes. Do not create tags, releases or PyPI uploads without a separate owner decision.
- Seek genuine independent feedback using [the five-minute trial](TRY_IT.md) and [issue 8](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8). A synthetic test pass is not independent adoption.

## Reference

The lab was independently authored after studying high-level governance and benchmark concepts in [AgentGuard](https://github.com/MohamedYasir-006/AgentGuard). No code was copied. No AgentGuard benchmark result is reproduced or claimed. All examples here are synthetic and public.
