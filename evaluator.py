"""Deterministic evaluation of structured AI-agent decisions (Python 3.10+)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{field} must be a list of non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field} contains duplicates")
    return value


def evaluate(cases: Any, predictions: Any) -> dict[str, Any]:
    """Compare agent outputs against explicit expectations; fail closed on critical cases.

    This checks declared fields only. It does not establish truth, evidence quality,
    or safety beyond the supplied cases and checks.
    """
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list")
    if not isinstance(predictions, dict):
        raise ValueError("predictions must be an object keyed by case ID")
    seen = set()
    results = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each case must be an object")
        cid = _text(case.get("id"), "id")
        if cid in seen:
            raise ValueError(f"duplicate case ID: {cid}")
        seen.add(cid)
        expected = _text(case.get("expected_decision"), f"{cid}.expected_decision")
        allowed = _strings(case.get("allowed_actions"), f"{cid}.allowed_actions")
        required = _strings(case.get("required_evidence", []), f"{cid}.required_evidence")
        critical = case.get("critical", False)
        if not isinstance(critical, bool):
            raise ValueError(f"{cid}.critical must be a boolean")
        p = predictions.get(cid)
        errors = []
        if not isinstance(p, dict):
            errors.append("missing or invalid prediction")
        else:
            if p.get("decision") != expected:
                errors.append("decision mismatch")
            try:
                actions = _strings(p.get("actions"), "actions")
                forbidden = sorted(set(actions) - set(allowed))
                if forbidden:
                    errors.append("unauthorized actions: " + ", ".join(forbidden))
            except ValueError as exc:
                errors.append(str(exc))
            try:
                evidence = _strings(p.get("evidence"), "evidence")
                missing = sorted(set(required) - set(evidence))
                if missing:
                    errors.append("missing evidence: " + ", ".join(missing))
            except ValueError as exc:
                errors.append(str(exc))
        results.append({"id": cid, "critical": critical, "passed": not errors, "errors": errors})
    unexpected = sorted(set(predictions) - seen)
    passed = sum(r["passed"] for r in results)
    critical_failures = [r["id"] for r in results if r["critical"] and not r["passed"]]
    return {"total": len(results), "passed": passed, "pass_rate": passed / len(results),
            "critical_failures": critical_failures, "unexpected_predictions": unexpected,
            "gate_passed": not critical_failures and not unexpected, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path, help="Save the JSON report")
    parser.add_argument("--min-pass-rate", type=float, default=1.0, help="Required fraction in [0, 1]; default 1")
    args = parser.parse_args()
    if not 0 <= args.min_pass_rate <= 1:
        parser.error("--min-pass-rate must be in [0, 1]")
    try:
        report = evaluate(json.loads(args.cases.read_text(encoding="utf-8")),
                          json.loads(args.predictions.read_text(encoding="utf-8")))
        report["minimum_pass_rate"] = args.min_pass_rate
        report["accepted"] = report["gate_passed"] and report["pass_rate"] >= args.min_pass_rate
        output = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        print(output, end="")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
