# Architecture and trust boundaries

| Component | Input and output | Boundary / relevant checks |
| --- | --- | --- |
| `evaluator.py: evaluate` | In-memory cases and predictions to deterministic report | Declared strings only; no execution, evidence lookup or permission enforcement |
| `evaluator.py: main` | UTF-8 JSON files, threshold, optional report path | Duplicate-key rejection, input alias protection, exits 0/1/2; `tests/test_cli.py` |
| `action.yml` | Literal caller filenames and threshold to CLI arguments | Caller supplies Python/Bash; composite-action smoke CI covers wrapper behavior |
| `docs/lab/engine.js` | Browser JSON to equivalent report | Independent JS port, own-property lookup and documented resource limits; Python/Node parity |
| `docs/lab/build.py` and `template.html` | Sources to checked-in `index.html` | Freshness check; no network/service needed for local evaluation |
| Packaging and `tools/build_reproducible.py` | Committed snapshot to wheel/sdist plus hashes | Build tools only; normalized archives preserve payload and executable semantics |
| CI and manual publication | Source/tests to evidence; separately approved upload | Read-only tests; manual TestPyPI workflow is outside ordinary PR validation |

The Python module has no runtime dependency. Its callable evaluator does not apply
the CLI threshold: callers combine `gate_passed` and `pass_rate` with their policy.
Missing or malformed predictions fail cases. Failed critical cases and unexpected
prediction IDs always close the gate. Lists of allowed actions permit subsets;
evidence IDs establish presence of declarations, not authenticity of records.

Keep tests in [tests/](../tests/), public examples in [examples/](../examples/),
and user contract changes in [INTEGRATION.md](INTEGRATION.md). Browser restrictions
are described in [the lab guide](lab/README.md); they do not impose the same size
limits on Python. The Python JSON decoder can reject excessive nesting with exit 2;
that is parser error handling, not a new evaluation rule or a security sandbox.

Development and CI evidence cannot establish the isolation of a deployed system.
Use [the review preparation](ISOLATION_REVIEW_PREPARATION.md) to identify the missing
evidence, and [the team protocol](DEVELOPMENT_TEAM.md) to separate authorship from review.
