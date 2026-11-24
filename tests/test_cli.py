import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluator import evaluate

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.predictions = json.loads((ROOT / "examples/predictions.json").read_text(encoding="utf-8"))
        self.input = self.directory / "predictions.json"

    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "evaluator.py"), str(ROOT / "examples/cases.json"),
             str(self.input), *args],
            capture_output=True, text=True, timeout=10
        )

    def write_predictions(self):
        self.input.write_text(json.dumps(self.predictions), encoding="utf-8")

    def test_accepted_report(self):
        self.write_predictions()
        out = self.directory / "report.json"
        result = self.invoke("--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["accepted"])
        self.assertEqual(report, json.loads(out.read_text(encoding="utf-8")))

    def test_unicode_reports_preserve_values_and_exit_status(self):
        case_id = "caso-caf\u00e9-\u6f22-\U0001f9ea"
        forbidden = "prohibida-\u6f22-\U0001f4a5"
        evidence_id = "evidencia-\u00f1-\U0001f50e"
        unexpected_id = "extra-\u65e5-\U0001f916"
        cases = self.directory / "cases.json"
        cases.write_text(json.dumps([{
            "id": case_id, "expected_decision": "permitir-\u2705",
            "allowed_actions": [], "required_evidence": [evidence_id], "critical": True,
        }], ensure_ascii=False), encoding="utf-8")
        for encoding, handler in (("ascii", "strict"), ("cp1252", "strict"),
                                  ("cp1252", "replace"), ("utf-8", "strict")):
            for outcome in ("accepted", "critical_failure", "unexpected_prediction"):
                with self.subTest(encoding=encoding, handler=handler, outcome=outcome):
                    predictions = {case_id: {
                        "decision": "permitir-\u2705", "actions": [], "evidence": [evidence_id],
                    }}
                    errors = []
                    if outcome == "critical_failure":
                        predictions[case_id]["actions"] = [forbidden]
                        predictions[case_id]["evidence"] = []
                        errors = ["unauthorized actions: " + forbidden,
                                  "missing evidence: " + evidence_id]
                    elif outcome == "unexpected_prediction":
                        predictions[unexpected_id] = {}
                    self.input.write_text(json.dumps(predictions, ensure_ascii=False), encoding="utf-8")
                    output = self.directory / "unicode-report.json"
                    environment = os.environ.copy()
                    environment["PYTHONIOENCODING"] = encoding + ":" + handler
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "evaluator.py"), str(cases), str(self.input),
                         "--min-pass-rate=0", "--output", str(output)],
                        env=environment, capture_output=True, timeout=10,
                    )
                    accepted = outcome == "accepted"
                    self.assertEqual(result.returncode, 0 if accepted else 1, result.stderr)
                    self.assertEqual(result.stderr, b"")
                    report = json.loads(result.stdout.decode(encoding))
                    self.assertEqual(report, json.loads(output.read_text(encoding="utf-8")))
                    self.assertEqual(report, {
                        "total": 1, "passed": 0 if errors else 1,
                        "pass_rate": 0.0 if errors else 1.0,
                        "critical_failures": [case_id] if errors else [],
                        "unexpected_predictions": [unexpected_id] if outcome == "unexpected_prediction" else [],
                        "gate_passed": accepted,
                        "results": [{"id": case_id, "critical": True, "passed": not errors, "errors": errors}],
                        "minimum_pass_rate": 0.0, "accepted": accepted,
                    })

    def test_noncritical_failure_threshold(self):
        self.predictions["research-01"]["decision"] = "wrong"
        self.write_predictions()
        self.assertEqual(self.invoke().returncode, 1)
        result = self.invoke("--min-pass-rate", "0.5")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["accepted"])

    def test_critical_failure_never_accepted(self):
        self.predictions["permissions-01"]["actions"].append("forbidden")
        self.write_predictions()
        result = self.invoke("--min-pass-rate", "0")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["gate_passed"])

    def test_duplicate_json_keys_rejected(self):
        self.input.write_text('{"x": {}, "x": {}}', encoding="utf-8")
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate JSON key", result.stderr)

    def test_duplicate_json_keys_in_cases_rejected(self):
        cases = self.directory / "cases.json"
        cases.write_text(
            '[{"id":"case-a","id":"case-b",'
            '"expected_decision":"reject","allowed_actions":[]}]',
            encoding="utf-8",
        )
        self.write_predictions()
        result = subprocess.run(
            [sys.executable, str(ROOT / "evaluator.py"), str(cases), str(self.input)],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("duplicate JSON key", result.stderr)

    def test_malformed_json(self):
        self.input.write_text("{", encoding="utf-8")
        self.assertEqual(self.invoke().returncode, 2)

    def test_missing_file(self):
        self.assertEqual(self.invoke().returncode, 2)

    def test_invalid_threshold(self):
        self.write_predictions()
        self.assertEqual(self.invoke("--min-pass-rate", "nan").returncode, 2)

    def test_refuses_to_overwrite_prediction_input(self):
        self.write_predictions()
        original = self.input.read_bytes()
        result = self.invoke("--output", str(self.input))
        self.assertEqual(result.returncode, 2)
        self.assertIn("must not overwrite", result.stderr)
        self.assertEqual(self.input.read_bytes(), original)

    def test_refuses_to_overwrite_input_via_relative_alias(self):
        self.write_predictions()
        original = self.input.read_bytes()
        alias = self.directory / "." / "predictions.json"
        result = self.invoke("--output", str(alias))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.input.read_bytes(), original)

    def test_refuses_to_overwrite_either_input_via_hardlink(self):
        self.write_predictions()
        cases = self.directory / "cases.json"
        cases.write_bytes((ROOT / "examples/cases.json").read_bytes())
        for source in (cases, self.input):
            with self.subTest(source=source.name):
                cases.write_bytes((ROOT / "examples/cases.json").read_bytes())
                self.write_predictions()
                alias = self.directory / (source.stem + "-report.json")
                original = source.read_bytes()
                alias.hardlink_to(source)
                result = subprocess.run(
                    [sys.executable, str(ROOT / "evaluator.py"), str(cases),
                     str(self.input), "--output", str(alias)],
                    capture_output=True, text=True, timeout=10
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("must not overwrite", result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(alias.read_bytes(), original)

    def test_output_file_can_be_replaced_when_it_is_not_an_input(self):
        self.write_predictions()
        out = self.directory / "existing report.json"
        out.write_text("old report", encoding="utf-8")
        result = self.invoke("--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), json.loads(out.read_text(encoding="utf-8")))

    def test_invalid_python_prediction_key(self):
        cases = json.loads((ROOT / "examples/cases.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            evaluate(cases, {1: {}})


if __name__ == "__main__":
    unittest.main()
