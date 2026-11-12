import copy
import json
from pathlib import Path
import unittest
from evaluator import evaluate

ROOT = Path(__file__).resolve().parents[1]

class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT / 'examples/cases.json').read_text())
        self.predictions = json.loads((ROOT / 'examples/predictions.json').read_text())

    def test_pass(self):
        r = evaluate(self.cases, self.predictions)
        self.assertEqual(r['pass_rate'], 1.0)
        self.assertTrue(r['gate_passed'])

    def test_wrong_decision(self):
        self.predictions['research-01']['decision'] = 'approve'
        r = evaluate(self.cases, self.predictions)
        self.assertEqual(r['passed'], 2)
        self.assertTrue(r['gate_passed'])

    def test_unauthorized_action(self):
        self.predictions['permissions-01']['actions'].append('modify_policy')
        r = evaluate(self.cases, self.predictions)
        self.assertFalse(r['gate_passed'])
        self.assertEqual(r['critical_failures'], ['permissions-01'])

    def test_missing_evidence(self):
        self.predictions['permissions-01']['evidence'] = []
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_missing_prediction(self):
        del self.predictions['missing-data-01']
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_extra_prediction(self):
        self.predictions['unexpected'] = {}
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_invalid_actions(self):
        self.predictions['permissions-01']['actions'] = 'log_denial'
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

    def test_duplicate_case(self):
        with self.assertRaises(ValueError):
            evaluate(self.cases + [copy.deepcopy(self.cases[0])], self.predictions)

    def test_empty_cases(self):
        with self.assertRaises(ValueError):
            evaluate([], self.predictions)

    def test_invalid_critical(self):
        self.cases[0]['critical'] = 'false'
        with self.assertRaises(ValueError):
            evaluate(self.cases, self.predictions)

    def test_duplicate_actions(self):
        self.predictions['permissions-01']['actions'] = ['log_denial', 'log_denial']
        self.assertFalse(evaluate(self.cases, self.predictions)['gate_passed'])

if __name__ == '__main__':
    unittest.main()
