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

GitHub Actions verified 43 unittest tests, including the six declaration-lab methods, on Python 3.13 at [candidate commit 35bdc88](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45657420051/job/139357735857). All six workflows succeeded on that commit, including [distribution checks](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45657419977). The evaluator blob matched main at b735b467e59302cf6f2c67b42ebf51e5c2f59d0e. Recheck CI on subsequent revisions.

## Validation after main synchronization

On 2026-11-26, the candidate was combined with main at `0355eb574a7e3563e7b32d35170996d42926ac13`, preserving the seven regression tests and contributor credits from PRs #26, #27 and #28. The README and changelog merged without conflicts; their earlier 43- and 44-test results remain historical records.

Local validation on Windows with Python 3.13.18 passed all **50 unittest methods** (including the six declaration-lab methods and their 22 subtests). With Node.js 24.22.3, `python docs/lab/build.py --check` passed, and `python docs/lab/test_parity.py` passed **254/254 shared scenarios** plus **5/5 deliberate browser-only restrictions**. The evaluator and composite action are unchanged from that main commit. These checks use only synthetic fixtures and do not establish independent adoption or runtime safety. Hosted workflows must still be checked on the resulting candidate head.

## Candidate review checklist

- Verify all six workflows on the exact candidate head, including distribution checks and Python 3.10–3.13.
- Confirm source and wheel metadata agree on 0.3.0rc1, include the MIT license, and install in clean environments.
- Confirm the evaluator and action semantics are unchanged.
- Review the version and change notes. Do not create tags, releases or PyPI uploads without a separate owner decision.
- Seek genuine independent feedback using [the five-minute trial](TRY_IT.md) and [issue 8](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8). A synthetic test pass is not independent adoption.

## Reference

The lab was independently authored after studying high-level governance and benchmark concepts in [AgentGuard](https://github.com/MohamedYasir-006/AgentGuard). No code was copied. No AgentGuard benchmark result is reproduced or claimed. All examples here are synthetic and public.
