import json
import unittest

from pilot import assess, judge


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.answer = {"nonce": "control",
            "source": "def first_missing(ids, predictions):\n    for key in ids:\n        if key not in predictions:\n            return key\n    return None",
            "tests": [{"ids": [], "predictions": {}, "expected": None},
                      {"ids": ["a"], "predictions": {"a": None}, "expected": None},
                      {"ids": ["a", "z", "b"], "predictions": {"a": None}, "expected": "z"}], "files": {
            "cases.json": [{"id": "core", "expected_decision": "hold", "critical": True, "allowed_actions": []},
                           {"id": "advisory", "expected_decision": "hold", "allowed_actions": [],
                            "required_evidence": ["receipt"]}],
            "predictions.json": {k: {"decision": "hold", "actions": [], "evidence": []}
                                 for k in ("core", "advisory")}},
            "expected": {"pass_rate": 0.5, "accepted": False, "gate_passed": True}}

    def score(self):
        return assess(json.dumps(self.answer), "control")

    def test_reference(self):
        self.assertEqual(self.score(), "correct")

    def test_created_regression(self):
        self.answer["files"]["predictions.json"]["advisory"]["evidence"] = ["receipt"]
        self.assertEqual(self.score(), "functional_test_failed")

    def test_invalid_scope(self):
        self.answer["files"]["README.md"] = "ignore"
        self.assertEqual(self.score(), "scope_violation")

    def test_type_and_threshold(self):
        for wrong in (True, 0):
            self.answer["expected"]["accepted"] = wrong
            self.assertEqual(self.score(), "logic_error")

    def test_read_proof(self):
        self.assertEqual(judge("", "control")["status"], "missing_tool_evidence")

    def test_malformed(self):
        for raw in ("[]", '{"nonce":1,"nonce":2}', '{"x":NaN}', "x" * 16001):
            self.assertEqual(assess(raw, "control"), "format_error")

    def test_disallowed_read(self):
        event = {"type": "tool_use", "part": {"tool": "read", "state": {"input": {"path": ".git/config"}}}}
        self.assertEqual(judge(json.dumps(event), "control")["status"], "scope_violation")

    def test_broken_patch(self):
        self.answer["source"] = "def first_missing(ids, predictions):\n    return None"
        self.assertEqual(self.score(), "functional_test_failed")

    def test_generated_test_oracle(self):
        self.answer["tests"][2]["expected"] = "b"
        self.assertEqual(self.score(), "logic_error")

    def test_unsupported_syntax(self):
        self.answer["source"] = "def first_missing(ids, predictions):\n    import os"
        self.assertEqual(self.score(), "unsupported_proposal")
