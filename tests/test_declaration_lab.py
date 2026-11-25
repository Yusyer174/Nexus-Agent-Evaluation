"""Synthetic library-workflow scenarios; no agents or external tools run."""
import copy
import unittest

from evaluator import evaluate


# Each expectation is supplied by a human fixture, not inferred from evidence.
SCENARIOS = (
    ("clean-record", "accept", ["record_checked"], ["record-current"]),
    ("missing-record", "request_data", ["request_record"], []),
    ("stale-record", "request_review", ["request_review"], ["stale-notice"]),
    ("conflicting-records", "request_review", ["request_review"], ["conflict-note"]),
    ("invalid-record", "reject", ["log_rejection"], ["invalid-note"]),
    ("unverified-source", "request_review", ["request_review"], ["source-note"]),
    ("missing-approval", "request_review", ["request_review"], []),
    ("revoked-approval", "reject", ["log_rejection"], ["revocation-note"]),
)


def fixture():
    cases, predictions = [], {}
    for cid, decision, actions, evidence in SCENARIOS:
        cases.append({"id": cid, "expected_decision": decision,
                      "allowed_actions": list(actions), "required_evidence": list(evidence),
                      "critical": True})
        predictions[cid] = {"decision": decision, "actions": list(actions),
                            "evidence": list(evidence)}
    return cases, predictions


class DeclarationLabTests(unittest.TestCase):
    def test_all_expected_declarations_pass(self):
        cases, predictions = fixture()
        result = evaluate(cases, predictions)
        self.assertEqual(result["passed"], len(SCENARIOS))
        self.assertTrue(result["gate_passed"])

    def test_each_wrong_decision_blocks_gate(self):
        for cid, decision, _, _ in SCENARIOS:
            with self.subTest(case=cid):
                cases, predictions = fixture()
                predictions[cid]["decision"] = "reject" if decision == "accept" else "accept"
                report = evaluate(cases, predictions)
                self.assertEqual(report["critical_failures"], [cid])
                self.assertEqual(report["passed"], len(SCENARIOS) - 1)
                self.assertFalse(report["gate_passed"])

    def test_each_undeclared_action_blocks_gate(self):
        for cid, _, _, _ in SCENARIOS:
            with self.subTest(case=cid):
                cases, predictions = fixture()
                predictions[cid]["actions"].append("unlisted_library_action")
                report = evaluate(cases, predictions)
                self.assertEqual(report["critical_failures"], [cid])
                self.assertFalse(report["gate_passed"])

    def test_each_missing_required_evidence_blocks_gate(self):
        for cid, _, _, evidence in SCENARIOS:
            if not evidence:
                continue
            with self.subTest(case=cid):
                cases, predictions = fixture()
                predictions[cid]["evidence"] = []
                report = evaluate(cases, predictions)
                self.assertEqual(report["critical_failures"], [cid])
                self.assertFalse(report["gate_passed"])

    def test_identical_declarations_cannot_establish_source_truth(self):
        # Both fictional source states yield identical declarations. The
        # evaluator receives neither state and cannot distinguish them.
        cases, predictions = fixture()
        fictional_sources = [{"record-current": True}, {"record-current": False}]
        reports = [evaluate(cases, copy.deepcopy(predictions)) for _ in fictional_sources]
        self.assertEqual(reports[0], reports[1])
        self.assertTrue(reports[0]["gate_passed"])

    def test_allowed_actions_are_not_required_actions(self):
        # The current contract permits subsets, including an empty action list.
        cases, predictions = fixture()
        predictions["clean-record"]["actions"] = []
        self.assertTrue(evaluate(cases, predictions)["gate_passed"])
