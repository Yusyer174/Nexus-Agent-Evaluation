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
- `--output` refuses to overwrite either input file, including relative aliases, symbolic links and hard links. Existing unrelated report files can be replaced. This prevents accidental collisions; it is not a guarantee against concurrent filesystem changes.

For filenames beginning with `-`, put options before a `--` separator:

```sh
nexus-evaluate --output=report.json -- --cases.json --predictions.json
```

The composite action handles this automatically, resolves relative paths from the caller workspace, and requires Python 3.10+ and Bash on the runner. Input strings are passed literally, including spaces and shell characters. A valid rejected evaluation writes a report and exits 1; invalid input exits 2 and may produce no report. Use a fresh report path or remove an old report before a run so that an error cannot leave a stale artifact mistaken for a new result.

## Report encoding

The CLI prints JSON to stdout and saves the same report with `--output` using UTF-8. Non-ASCII characters use standard JSON escapes in both outputs, so Unicode identifiers and diagnostics also work with ASCII or legacy Windows stdout encodings such as CP1252. For example, the identifier `café` is serialized as `"caf\u00e9"`; a JSON parser restores the original string. Characters outside the Basic Multilingual Plane use JSON surrogate-pair escapes.

Compare parsed JSON values rather than the spelling of escaped strings. This serialization change preserves report keys, Unicode values, evaluation rules and exit codes; reports containing only ASCII text retain their existing representation.

## How to evaluate an actual model responsibly

Create cases *independently* from the system being evaluated; separate development and held-out cases. Use realistic but non-sensitive examples, record model version and prompt setup, and review errors as well as aggregate scores. A green report alone cannot demonstrate generalization, evidence correctness, sandboxing, policy enforcement, or runtime safety.

Do not publish private test expectations, real credentials, or unpublished proprietary agent data.
