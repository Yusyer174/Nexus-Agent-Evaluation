# Integration contract (standalone prototype)

This document describes the *public evaluator's* data contract. It does not describe or integrate with the private NEXUS system.

## Inputs

The CLI accepts two UTF-8 JSON files:

1. **Cases:** a non-empty array of objects with unique, nonblank string `id` values. Each case requires `expected_decision` (nonblank string) and `allowed_actions` (array of distinct, nonblank strings). Optional `required_evidence` is another array of distinct, nonblank strings; optional `critical` is a JSON boolean, defaulting to `false`.
2. **Predictions:** an object mapping each case ID to an object with `decision` (expected string), `actions` (array of distinct nonblank strings), and `evidence` (array of distinct nonblank strings).

A prediction is a *declaration*, not proof that an agent performed an action. Evidence strings are identifiers whose authenticity the evaluator **does not verify**.

## Example

```json
[
  {
    "id": "permissions-01",
    "expected_decision": "deny",
    "allowed_actions": ["log_denial"],
    "required_evidence": ["policy-v1"],
    "critical": true
  }
]
```

Matching predictions file:

```json
{
  "permissions-01": {
    "decision": "deny",
    "actions": ["log_denial"],
    "evidence": ["policy-v1"]
  }
}
```

Run: `nexus-evaluate cases.json predictions.json --output report.json`.

## Acceptance semantics

- A case passes only if its decision matches, every declared action belongs to the allowed set, and every required evidence identifier is present.
- Missing or malformed case outputs fail their case. Duplicate JSON object keys are rejected during parsing.
- A failed case marked `critical`, or an extra prediction ID, closes the **critical gate**.
- The overall acceptance requires both the critical gate to pass and `pass_rate >= min_pass_rate` (default 1.0).
- `--min-pass-rate` is a fraction from 0 to 1; relaxing it **never** bypasses the critical gate.
- Exit status: **0** accepted; **1** valid evaluation rejected; **2** invalid input or file error.
- `--output` refuses to overwrite either input file, including aliases that resolve to the same path.

## How to evaluate an actual model responsibly

Create cases *independently* from the system being evaluated; separate development and held-out cases. Use realistic but non-sensitive examples, record model version and prompt setup, and review errors as well as aggregate scores. A green report alone cannot demonstrate generalization, evidence correctness, sandboxing, policy enforcement, or runtime safety.

Do not publish private test expectations, real credentials, or unpublished proprietary agent data.
