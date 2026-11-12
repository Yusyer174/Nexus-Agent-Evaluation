import json
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

    def test_malformed_json(self):
        self.input.write_text("{", encoding="utf-8")
        self.assertEqual(self.invoke().returncode, 2)

    def test_missing_file(self):
        self.assertEqual(self.invoke().returncode, 2)

    def test_invalid_threshold(self):
        self.write_predictions()
        self.assertEqual(self.invoke("--min-pass-rate", "nan").returncode, 2)

    def test_invalid_python_prediction_key(self):
        cases = json.loads((ROOT / "examples/cases.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            evaluate(cases, {1: {}})


if __name__ == "__main__":
    unittest.main()
