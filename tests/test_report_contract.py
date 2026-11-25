"""Regression coverage for the existing declaration-only report contract."""
import copy
import itertools
import unittest

from evaluator import evaluate


def fixture():
    cases = [
        {"id": "z-case", "expected_decision": "review", "critical": True,
         "allowed_actions": [], "required_evidence": ["z-source", "a-source"]},
        {"id": "a-case", "expected_decision": "review", "critical": True,
         "allowed_actions": [], "required_evidence": []},
    ]
    predictions = {
        "z-case": {"decision": "review", "actions": [], "evidence": ["z-source", "a-source"]},
        "a-case": {"decision": "review", "actions": [], "evidence": []},
    }
    return cases, predictions


class ReportContractTests(unittest.TestCase):
    def test_report_order_is_independent_of_prediction_order(self):
        cases, predictions = fixture()
        predictions["z-case"]["actions"] = ["z-action", "a-action"]
        predictions["z-case"]["evidence"] = []
        predictions["a-case"]["decision"] = "wrong"
        predictions.update({"z-extra": {}, "a-extra": {}})
        expected = {
            "total": 2, "passed": 0, "pass_rate": 0.0,
            "critical_failures": ["z-case", "a-case"],
            "unexpected_predictions": ["a-extra", "z-extra"],
            "gate_passed": False,
            "results": [
                {"id": "z-case", "critical": True, "passed": False,
                 "errors": ["unauthorized actions: a-action, z-action",
                            "missing evidence: a-source, z-source"]},
                {"id": "a-case", "critical": True, "passed": False,
                 "errors": ["decision mismatch"]},
            ],
        }
        for ordering in itertools.permutations(predictions):
            with self.subTest(ordering=ordering):
                self.assertEqual(evaluate(cases, {k: predictions[k] for k in ordering}), expected)

    def test_malformed_case_string_lists_are_invalid_input(self):
        for field in ("allowed_actions", "required_evidence"):
            for value in ([True], [0], [None], [" "], "not-a-list"):
                with self.subTest(field=field, value=value):
                    cases, predictions = fixture()
                    cases[0][field] = value
                    with self.assertRaisesRegex(ValueError, rf"z-case\.{field} must be a list of non-empty strings"):
                        evaluate(cases, predictions)

    def test_malformed_prediction_lists_fail_the_critical_case(self):
        for field in ("actions", "evidence"):
            for value in ([True], [0], [None], [" "], "not-a-list"):
                with self.subTest(field=field, value=value):
                    cases, predictions = fixture()
                    predictions["z-case"][field] = value
                    report = evaluate(cases, predictions)
                    self.assertFalse(report["gate_passed"])
                    self.assertEqual(report["critical_failures"], ["z-case"])
                    self.assertEqual(report["passed"], 1)
                    self.assertFalse(report["results"][0]["passed"])
                    self.assertEqual(report["results"][0]["errors"],
                                     [f"{field} must be a list of non-empty strings"])

    def test_nonboolean_critical_values_are_invalid_input(self):
        for value in (0, 1, None, "true", "false", []):
            with self.subTest(value=value):
                cases, predictions = fixture()
                cases[0]["critical"] = value
                with self.assertRaisesRegex(ValueError, r"z-case\.critical must be a boolean"):
                    evaluate(cases, predictions)

    def test_evaluation_preserves_inputs(self):
        cases, predictions = fixture()
        predictions["z-case"]["actions"] = ["z-action", "a-action"]
        before = copy.deepcopy((cases, predictions))
        evaluate(cases, predictions)
