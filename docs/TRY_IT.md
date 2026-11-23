# Try NEXUS Agent Evaluation in 5 minutes

**Seeking independent feedback from Python and agent developers.** This project is an early MIT-licensed, dependency-free evaluator of *structured output declarations*. It does **not** execute agents, verify evidence authenticity, or establish runtime safety.

## Option A — Run without a model or API key

With Python 3.10+:

```bash
git clone https://github.com/Yusyer174/Nexus-Agent-Evaluation.git
cd Nexus-Agent-Evaluation
python evaluator.py examples/cases.json examples/predictions.json --output trial-report.json
```

The bundled synthetic predictions should be accepted (exit code 0). Open `trial-report.json` to inspect per-case outcomes.

Now run the deliberately failing example:

```bash
python evaluator.py examples/cases.json examples/rejected-predictions.json
```

Expected: exit code **1** and `gate_passed: false` because a critical case declares an unauthorized action. The expected rejection is intentional; it does **not** require changing real agent permissions.

## Option B — Evaluate declarations from your own system

Write the two JSON files described in [INTEGRATION.md](INTEGRATION.md), or adapt the synthetic examples. Your agent only needs to export `decision`, `actions` and `evidence` fields; **NEXUS does not run the agent**.

Run with a held-out case set you designed independently:

```bash
python evaluator.py cases.json predictions.json --min-pass-rate 1 --output report.json
```

To call the evaluator as a GitHub Action, see [the copyable workflow](../examples/github-actions/evaluate-agent.yml). The action is experimental: pin its revision to a reviewed commit in downstream CI instead of depending on a moving branch.

## Feedback we would value

- Could you understand the input contract and produce a successful and a rejected report without assistance?
- Are any error messages ambiguous? Include Python version, operating system, and **synthetic** reproduction steps.
- Would a declaration-only, deterministic gate complement your agent test setup? Where would it be inadequate?
- What one small change would make this tool more useful? Please avoid requesting claims of runtime safety that the tool cannot support.

Use [the independent trial feedback form](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/new?template=trial_feedback.yml) or [open a regular issue](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues). You can also propose a focused PR after reading [CONTRIBUTING.md](../CONTRIBUTING.md).

No credentials, proprietary agent traces, hidden test sets, personal information or financial data should be shared. Negative feedback is valuable; we will not count issue responses as adoption, installations or endorsements.
